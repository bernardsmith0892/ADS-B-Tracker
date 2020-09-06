# Import functions and libraries
import numpy as np
from numpy import *
from rtlsdr import RtlSdr
import pyModeS as pms
import threading, time, queue
import pandas as pd
import time
import argparse
import requests

# Import program modules
import adsb_signal_processing as asp
import adsb_objects as ao
import app

planes = {}
packets = []
PACKET_BUFF_SIZE = 256
TTL = 100

def sdr_read( Qin, sdr, N_samples, stop_flag ):
	"""
	Modified from UC Berkeley's EE123 course. Processes reads N_samples from the RTL-SDR and provides it
		to the 'signal_process' thread.
	"""
	while (  not stop_flag.is_set() ):
		try:
			data_chunk = abs(sdr.read_samples(N_samples))   # get samples 
		except Exception as e:
			print("\n*** Error reading RTLSDR - ", e, " ***")
			print("Stopping threads...")
			stop_flag.set()
			
		Qin.put( data_chunk ) # append to list

	sdr.close()

def signal_process( Qin, source, stop_flag, log, pos_ref, FIX_1BIT_ERRORS=False  ):
	"""
	Modified from UC Berkeley's EE123 course. Processes RF chunks provided by the 'sdr_read' thread.
	"""

	row_size = 16 + 112*2 #240 bits
	
	while(  not stop_flag.is_set() ):
		curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
		
		# Get streaming chunk from sdr_read thread
		y = Qin.get();
			
		packet_diff = len(packets)
		idx_preamble, noise_floor = asp.detectPreamble(y)		
		for n in idx_preamble:
			signal = abs(y[int(n) : int(n) + row_size])
			msg = asp.decode_ADSB( signal, FIX_1BIT_ERRORS )
			if msg != None:
				snr = asp.SNR(signal, noise_floor)
				pkt = ao.Packet(msg, time.time(), snr)
				packets.append( pkt )
				print( '!' , end='', flush=True )
				
				if len(packets) > PACKET_BUFF_SIZE:
					packets.pop(0)
				
				if log != None:
					try:
						with open(log, 'a') as f:
							f.write(f"[{curr_time}] {msg}\n")
					except:
						print(f"Error writing to {log}!")
				
				if pkt.icao in planes:
					planes[pkt.icao].process_packet( pkt )
				elif pkt.icao != None:
					planes[pkt.icao] = ao.Plane( pkt, pos_ref )
		
		if packet_diff == len(packets):
			# packets.append(f"[{curr_time}] None received...")
			print( '.' , end='', flush=True )
		
		# Remove excess objects
		to_delete = []
		for p in planes.keys():
			if (time.time() - planes[p].last_update) >= TTL:
				to_delete.append(p)
		
		for p in to_delete:
			planes.pop(p)
		
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
		default=(None, None),
		help='Set the latitude and longitude of your ground station; usually your current location. If unset, attempts to determine your location using your IP address.'
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
	
	# Variable initialization
	fs = 2000000; # 2MHz sampling frequency
	center_freq = 1090e6 # 1090 MHz center frequency
	gain = 49.6 # Gain
	N_samples = 2048000 # SDR samples for each chunk of data ( Approx 1.024 seconds per chunk )
	TTL = args.TTL # How long to store ADS-B object information
	log = args.log # Where to log packets
	
	# Determine ground station location using IP address or manual input
	if args.location[0] == None or args.location[1] == None:
		try:
			url = 'https://ipinfo.io'
			loc_request = requests.get(url)
			lat_lon = loc_request.json()['loc'].split(',')
			pos_ref = [ float(lat_lon[0]), float(lat_lon[1]) ]
		except Exception:
			print(f'Error requesting location information from {url}')
			exit()
	else:
		pos_ref = [args.location[0], args.location[1]]
	
	# Determine whether to fix 1-bit errors
	FIX_1BIT_ERRORS = (
		args.fix_single_bit_errors[0] == 'Y' or 
		args.fix_single_bit_errors[0] == 'y' or 
		args.fix_single_bit_errors[0] == '1' or 
		args.fix_single_bit_errors[0] == 'T' or 
		args.fix_single_bit_errors[0] == 't'
	)


	# Setup Dash server
	app.server(pos_ref, planes, packets)
	
	# Create a queue for communication between the reading and processing threads
	Qin = queue.Queue()
	
	# Setup the RTL-SDR reader
	sdr = RtlSdr(args.rtl_device)
	sdr.sample_rate = fs	# sampling rate
	sdr.center_freq = center_freq   # 1090MhZ center frequency
	sdr.gain = gain
	
	stop_flag = threading.Event()
	
	# Setup the reading and processing threads
	t_sdr_read = threading.Thread(target = sdr_read, args = (Qin, sdr, N_samples, stop_flag  ))
	t_signal_process = threading.Thread(target = signal_process, args = ( Qin, source, stop_flag, log, pos_ref, FIX_1BIT_ERRORS))
	
	t_sdr_read.start()
	t_signal_process.start()
	
	# Run the Dash web server
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
