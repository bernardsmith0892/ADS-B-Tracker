import numpy as np
from numpy import *
import pyModeS as pms

def detectPreamble(y):
	"""Returns a list of indices for detected ADS-B preambles in the RF signal.
	
	Parameters
	----------
	y : numpy.array
		The RF signal to analyze for ADS-B preambles. Must have a 2MHz sample rate.
	
	Returns
	-------
	list
		A list of indices of potential preambles in the signal
	float
		The noise floor for this chunk. Calculated from the mean strength.
	"""
	
	idx_preamble = []
	
	y_mean = np.mean(y)
	y_std = np.std(y)
	thresh = y_mean + 5 * y_std
	
	for i in range( len(y) - 16 ):
		if y[i] >= thresh:
			chunk = abs(y[i : i + 16])
			high_bits = np.array([chunk[0], chunk[2], chunk[7], chunk[9]])
			low_bits = np.concatenate([[chunk[1]], chunk[3:7], [chunk[8]], chunk[10:16]])
			
			high_mean = np.mean(high_bits)
			low_mean = np.mean(low_bits)

			if(high_mean > low_mean):
				idx_preamble.append(i)	
	
	return idx_preamble, thresh

def decode_ADSB(signal, fix_1bit_errors=False):
	"""Attempts to decode the given signal as an ADS-B message and calculate SNR.
	
	Parameters
	----------
	signal : numpy.array
		The RF signal to decode. Must have a sample rate of 2MHz and be at least 240 samples long.
	fix_1bit_errors : bool, optional
		Whether or not to attempt to fix single bit errors.
	
	Returns
	-------
	string
		If the CRC check passes, returns the hex string for the ADS-B packet. Returns None if the CRC check fails.
	"""
	
	row_size = 16 + 112 * 2
	msg = None
	
	# Exit if signal's sample size is two small
	if (len(signal) < row_size):
		return
	
	# Decode the signal to binary (assume Manchester encoded)
	# Taken from the EE123 Lab 2 code
	bits = signal[16::2] > signal[17::2]
	tmp =  ''.join(['1' if x else '0' for x in bits])
	msg = hex(int(tmp,2))[2:]
	
	# CRC check for long message
	if (pms.crc(msg) == 0):
		return msg
	# CRC check for short message
	elif (pms.crc(msg[:14]) == 0):
		return msg[:14]
	
	if fix_1bit_errors:
		return correct_single_bit_error(msg)
	else:
		return None

def SNR(signal, noise_floor):
	"""Calculates the SNR of the signal based on a given noise floor.
	
	Parameters
	----------
	signal : numpy.array
		The RF signal to compare.
	noise_floor : float, optional
		The value for the signal's noise floor.
	
	Returns
	-------
	float
		SNR value for this packet.
	"""
	signal_mean = np.mean(signal)
	
	snr = 10 * np.log10( signal_mean / noise_floor )
	
	return snr
	
def correct_single_bit_error(msg):
	"""Attempts to correct a bit-flip error in an ADS-B message.
	
	Parameters
	----------
	msg : str
		The hex-string ADS-B message.
	
	Returns
	-------
	str
		If a solution is found, returns the corrected ADS-B message.
		Returns None if no solution found.
	"""
	
	num = int(msg, 16)
	bit_length = len(bin(num)[2:])
	
	for k in range(bit_length):
		test_num = num ^ (1 << k)
		test_msg = hex(test_num)[2:]
		
		# CRC check for long message
		if (pms.crc(test_msg) == 0):
			print( '*' , end='', flush=True )
			return test_msg
		# CRC check for short message
		elif (pms.crc(test_msg[:14]) == 0):
			print( '*' , end='', flush=True )
			return test_msg[:14]
	
	return None
	
	
	
	
	
	
	
	