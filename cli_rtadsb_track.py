# Import functions and libraries
from __future__ import division
import numpy as np
from numpy import *
from rtlsdr import RtlSdr
import pyModeS as pms
import threading, time, queue

def bool2Hex(lst):
	tmp =  ''.join(['1' if x else '0' for x in lst])
	return hex(int(tmp,2))[2:]


def detectPreamble(y):
	"""Returns a list of indices for detected ADS-B preambles in the RF signal.
	
	Parameters
	----------
	y : numpy.array
		The RF signal to analyze for ADS-B preambles. Must have a 2MHz sample rate.
	
	Returns
	-------
	list
		A list of indexes of potential preambles in the signal
	"""
	
	idx_preamble = []
	
	y_mean = np.mean(y)
	y_std = np.std(y)
	thresh = y_mean + 4 * y_std
	
	for i in range( len(y) - 16 ):
		if y[i] >= thresh:
			chunk = abs(y[i : i + 16])
			high_bits = np.array([chunk[0], chunk[2], chunk[7], chunk[9]])
			low_bits = np.concatenate([[chunk[1]], chunk[3:7], [chunk[8]], chunk[10:16]])

			high_mean = np.mean(high_bits)
			low_mean = np.mean(low_bits)

			if(high_mean > low_mean):
				idx_preamble.append(i)	
	
	return idx_preamble

def decode_ADSB(signal):
	"""Attempts to decode the given signal as an ADS-B message.
	
	Parameters
	----------
	signal : numpy.array
		The RF signal to decode. Must have a sample rate of 2MHz and be at least 240 samples long.
	log : str, optional
		The log file's location. If declared, appends decoded ADS-B packets to this file.
	
	Returns
	-------
	string
		Returns the ADS-B packet as a hex string, if the CRC check passes. Returns None if the CRC check fails.
	"""
	
	row_size = 16 + 112 * 2
	msg = None
	
	# Exit if signal's sample size is two small
	if (len(signal) < row_size):
		return
	
	# Decode the signal to binary (assume Manchester encoded)
	bits = signal[16::2] > signal[17::2]
	msg = bool2Hex(bits)
	
	# CRC check for long message
	if (pms.crc(msg) == 0):
		return msg
	# CRC check for short message
	elif (pms.crc(msg[:14]) == 0):
		return msg[:14]
	
	return None
		
				
def sdr_read( Qin, sdr, N_samples, stop_flag ):
	while (  not stop_flag.is_set() ):
		try:
			data_chunk = abs(sdr.read_samples(N_samples))   # get samples 
		except Exception as e:
			print("\n*** Error reading RTLSDR - ", e, " ***")
			print("Stopping threads...")
			stop_flag.set()
			
		Qin.put( data_chunk ) # append to list

	sdr.close()

def signal_process( Qin, source, stop_flag, log  ):
	row_size = 16 + 112*2
	
	while(  not stop_flag.is_set() ):
		
		# Get streaming chunk
		y = Qin.get();
		
		curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
		print(f"{ curr_time }: Looking for packets... ", end="")
		
		idx_preamble = detectPreamble(y)		
		print(f"Detected {len(idx_preamble)} possible preambles...")
		
		curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
		for n in idx_preamble:
			msg = decode_ADSB( abs(y[int(n) : int(n) + row_size]) )
			if msg != None:
				packet = f"[{curr_time}] CRC OK, DF{pms.df(msg)} ICAO: {pms.adsb.icao(msg)} typecode: {pms.adsb.typecode(msg)} MSG:{msg}"
				
				print(packet)
				with open(log, 'a') as f:
					f.write(packet + '\n')
				   
		Qin.queue.clear()
	
		
def main():
	fs = 2000000; # 2MHz sampling frequency
	center_freq = 1090e6 # 1090 MHz center frequency
	gain = 49.6 # gain
	N_samples = 2048000 # number of sdr samples for each chunk of data
	log = "adsb.log"


	pos_ref = [21.315603, -157.858093] # Honolulu's latitude, longitude for initializing the map
	
	# create an input output FIFO queues
	Qin = queue.Queue()
	
	# create a pyaudio object
	sdr = RtlSdr(1)
	sdr.sample_rate = fs	# sampling rate
	sdr.center_freq = center_freq   # 1090MhZ center frequency
	sdr.gain = gain
	
	stop_flag = threading.Event()
	
	# initialize threads
	t_sdr_read = threading.Thread(target = sdr_read,   args = (Qin, sdr, N_samples, stop_flag  ))
	t_signal_process = threading.Thread(target = signal_process, args = ( Qin, source, stop_flag, log))
	
	# start threads
	t_sdr_read.start()
	t_signal_process.start()
	
	# Run until the threads stop
	while threading.active_count() > 0:
		try:
			time.sleep(0.1)
		except:
			print("Stopping threads...")
			stop_flag.set()
			raise
			exit()
			
	
if __name__ == '__main__':
	main()
