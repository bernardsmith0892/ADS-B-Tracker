# Import functions and libraries
from __future__ import division
import numpy as np
from numpy import *
from rtlsdr import RtlSdr
import pyModeS as pms
import threading, time, queue
import adsb_signal_processing as asp
import adsb_objects as ao
				
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
	adsb_objects = {}
	
	while(  not stop_flag.is_set() ):
		curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
		print(f"As of {curr_time}...")
		print(f"ICAO\tCall\t\tLat\t\tLon\t\tAlt\tVel\tHead\tAge" )
		print( "----\t----\t\t---\t\t---\t\t---\t---\t----\t---" )
		for o in adsb_objects.values():
			print(o)
				
		# Get streaming chunk
		y = Qin.get();
			
		idx_preamble = asp.detectPreamble(y)		
		# print(f"Detected {len(idx_preamble)} possible preambles...")
		
		for n in idx_preamble:
			msg = asp.decode_ADSB( abs(y[int(n) : int(n) + row_size]) )
			if msg != None:
				pkt = ao.Packet(msg, time.time())
				print( pkt )
				with open(log, 'a') as f:
					f.write(f"[{curr_time}] {msg}\n")
				
				if pkt.icao in adsb_objects:
					adsb_objects[pkt.icao].process_packet( pkt )
				elif pkt.icao != None:
					adsb_objects[pkt.icao] = ao.ADSB_Object( pkt )
				
				'''
				packet = f"[{curr_time}] CRC OK, DF{pms.df(msg)} ICAO: {pms.adsb.icao(msg)} typecode: {pms.adsb.typecode(msg)} MSG:{msg}"
				
				print(packet)
				with open(log, 'a') as f:
					f.write(packet + '\n')
				'''
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
