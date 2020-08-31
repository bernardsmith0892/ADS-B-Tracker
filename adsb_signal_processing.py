import numpy as np
from numpy import *
import pyModeS as pms

def bool2Hex(lst):
	"""Encodes a list of boolean values into a hex string.
	
	Function taken from UC Berkeley EE123 Lab 2. Actually, most of the basic idea of this was from that lab.
	
	Parameters
	----------
	lst : list[bool]
		The boolean list to encode.
		
	Returns
	-------
	string
		The encoded hex string.
	"""
	
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
		A list of indices of potential preambles in the signal
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
