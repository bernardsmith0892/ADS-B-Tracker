# Import functions and libraries
import numpy as np
from numpy import *
from rtlsdr import RtlSdr
import pyModeS as pms
import threading, time, queue
import adsb_signal_processing as asp
import adsb_objects as ao
import pandas as pd
import app

pos_ref = {'lat': 21.315603, 'lon': -157.858093} # Honolulu's latitude, longitude
adsb_objects = {}
packets = []

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
		curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
		ao.print_dashboard( adsb_objects )
				
		# Get streaming chunk
		y = Qin.get();
			
		packet_diff = len(packets)
		idx_preamble = asp.detectPreamble(y)		
		for n in idx_preamble:
			msg = asp.decode_ADSB( abs(y[int(n) : int(n) + row_size]) )
			if msg != None:
				pkt = ao.Packet(msg, time.time())
				packets.append( pkt )
				print( pkt )
				with open(log, 'a') as f:
					f.write(f"[{curr_time}] {msg}\n")
				
				if pkt.icao in adsb_objects:
					adsb_objects[pkt.icao].process_packet( pkt )
				elif pkt.icao != None:
					adsb_objects[pkt.icao] = ao.ADSB_Object( pkt )
		
		if packet_diff == len(packets):
			packets.append(f"[{curr_time}] None received...")
					
		Qin.queue.clear()
	
		
def main():
	# Start Dash server
	app.server(pos_ref, adsb_objects, packets)

	fs = 2000000; # 2MHz sampling frequency
	center_freq = 1090e6 # 1090 MHz center frequency
	gain = 49.6 # gain
	N_samples = 2048000 # number of sdr samples for each chunk of data
	log = "adsb.log"
	
	# create an input output FIFO queues
	Qin = queue.Queue()
	
	# create a pyaudio object
	sdr = RtlSdr(1)
	sdr.sample_rate = fs	# sampling rate
	sdr.center_freq = center_freq   # 1090MhZ center frequency
	sdr.gain = gain
	
	stop_flag = threading.Event()
	
	# initialize threads
	t_sdr_read = threading.Thread(target = sdr_read, args = (Qin, sdr, N_samples, stop_flag  ))
	t_signal_process = threading.Thread(target = signal_process, args = ( Qin, source, stop_flag, log))
	
	# start threads
	t_sdr_read.start()
	t_signal_process.start()
	
	app.app.run_server()
	
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
