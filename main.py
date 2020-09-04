# Import functions and libraries
import numpy as np
from numpy import *
from rtlsdr import RtlSdr
import pyModeS as pms
import threading, time, queue
import pandas as pd
import time
import argparse

# Import program modules
import adsb_signal_processing as asp
import adsb_objects as ao
import app

adsb_objects = {}
packets = []
PACKET_BUFF_SIZE = 256
TTL = 100

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

def signal_process( Qin, source, stop_flag, log, FIX_1BIT_ERRORS=False  ):
	row_size = 16 + 112*2
	
	while(  not stop_flag.is_set() ):
		curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
		# ao.print_dashboard( adsb_objects )
				
		# Get streaming chunk
		y = Qin.get();
			
		packet_diff = len(packets)
		idx_preamble, noise_floor = asp.detectPreamble(y)		
		for n in idx_preamble:
			signal = abs(y[int(n) : int(n) + row_size])
			msg = asp.decode_ADSB( signal, fix_1bit_errors=FIX_1BIT_ERRORS )
			if msg != None:
				snr = asp.SNR(signal, noise_floor)
				pkt = ao.Packet(msg, time.time(), snr)
				packets.append( pkt )
				print( '!' , end=' ' )
				
				if len(packets) > PACKET_BUFF_SIZE:
					packets.pop(0)
				
				if log != None:
					try:
						with open(log, 'a') as f:
							f.write(f"[{curr_time}] {msg}\n")
					except:
						print(f"Error writing to {log}!")
				
				if pkt.icao in adsb_objects:
					adsb_objects[pkt.icao].process_packet( pkt )
				elif pkt.icao != None:
					adsb_objects[pkt.icao] = ao.ADSB_Object( pkt )
		
		if packet_diff == len(packets):
			packets.append(f"[{curr_time}] None received...")
			print('.', end=' ')
		
		# Remove excess objects
		to_delete = []
		for o in adsb_objects.keys():
			if (time.time() - adsb_objects[o].last_update) >= TTL:
				to_delete.append(o)
		
		for o in to_delete:
			adsb_objects.pop(o)
		
		Qin.queue.clear()
	
		
def main():
	# Setup cli arguments
	parser = argparse.ArgumentParser(
		description='''Listen for ADS-B signals using an RTL-SDR and watch the air traffic on local Dash webserver! Default location is http://localhost:8050'''
	)
	parser.add_argument('--rtl_device', '-d',
		type=int, 
		default=0,
		metavar='device_index',
		help='Select the RTL-SDR device index to use. Defaults to device 0.'
	)
	parser.add_argument('--location', '-l', 
		type=float, 
		nargs=2, 
		metavar=('Lat', 'Lon'), 
		default=(21.315603, -157.858093),
		help='Set the latitude and longitude of your ground station. Usually your current location. Defaults to Honolulu, Hawaii.'
	)
	parser.add_argument('--TTL', '-t',
		type=int, 
		default=100,
		help="Delete a tracked object if we haven't heard from it for TTL seconds. Default to 100 seconds."
	)
	parser.add_argument('--port', '-p',
		type=int, 
		default=8050, 
		help='The local port to run the Dash webserver on. Default to port 8050.'
	)
	parser.add_argument('--log',
		type=str, 
		default=None, 
		help='Where to log information on detected ADS-B packets. Does not log if unset.'
	)
	parser.add_argument('--fix-single-bit-errors',
		type=str,
		default='No',
		metavar='[Y/N]',
		dest='fix_single_bit_errors',
		help='Have the decoder attempt to fix single bit errors in packets. VERY RESOURCE INTENSIVE AT THIS TIME!!!'
	)
	args = parser.parse_args()
	
	# Variable initalization
	fs = 2000000; # 2MHz sampling frequency
	center_freq = 1090e6 # 1090 MHz center frequency
	gain = 49.6 # gain
	N_samples = 2048000 # number of sdr samples for each chunk of data
	pos_ref = {'lat': args.location[0], 'lon': args.location[1]}
	TTL = args.TTL
	log = args.log
	FIX_1BIT_ERRORS = (
		args.fix_single_bit_errors[0] == 'Y' or 
		args.fix_single_bit_errors[0] == 'y' or 
		args.fix_single_bit_errors[0] == '1' or 
		args.fix_single_bit_errors[0] == 'T' or 
		args.fix_single_bit_errors[0] == 't'
	)


	# Setup Dash server
	app.server(pos_ref, adsb_objects, packets)
	
	# create an input output FIFO queues
	Qin = queue.Queue()
	
	# create a pyaudio object
	sdr = RtlSdr(args.rtl_device)
	sdr.sample_rate = fs	# sampling rate
	sdr.center_freq = center_freq   # 1090MhZ center frequency
	sdr.gain = gain
	
	stop_flag = threading.Event()
	
	# initialize threads
	t_sdr_read = threading.Thread(target = sdr_read, args = (Qin, sdr, N_samples, stop_flag  ))
	t_signal_process = threading.Thread(target = signal_process, args = ( Qin, source, stop_flag, log, FIX_1BIT_ERRORS))
	
	# start threads
	t_sdr_read.start()
	t_signal_process.start()
	
	app.app.run_server(port = args.port)
	
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
