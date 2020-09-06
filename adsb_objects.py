import numpy as np
from numpy import *
import pyModeS as pms
import time
from datetime import datetime
import pandas as pd

def print_dashboard(planes):
	"""
	Prints a table of tracked aircraft to stdout.
	Outputs:
		'ICAO'
		'Callsign'
		'Latitude, Longitude'
		'Altitude'
		'Velocity'
		'Heading'
		'Age'
	
	Parameters
	----------
	planes : dict of (str : ADSB_Object)
		The objects to print information for.
	"""
	
	# Print the current date and time
	curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
	print(f"As of {curr_time}...")
	
	# Convert the dictionary to a Pandas DataFrame and print that DataFrame
	if len(planes) > 0:
		df = pd.DataFrame( planes.values() )
		df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
	
		print( df.to_string(index=False) )
	
	# Print 'None Found' if there are no objects in the dictionary
	else:
		print("None found...")
	
	print()


def print_dashboard_fancy(planes):
	"""
	Prints a fancy table of ADS-B object informaiton to stdout.
	Differs from 'print_dashboard' by using ASCII box drawing characters instead of
		default Pandas DataFrame output.
	Outputs:
		'ICAO'
		'Callsign'
		'Latitude, Longitude'
		'Altitude'
		'Velocity'
		'Heading'
		'Age'
	
	Parameters
	----------
	planes : dict of (str : ADSB_Object)
		The objects to print information for.
	"""
	
	curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
	print(f"As of {curr_time}...")

	header = """
╔══════╦════════╦═════════╦═════════╦════════╦════════╦═══════╦═════╗
║ ICAO ║Callsign║Latitude ║Longitude║Altitude║Velocity║Heading║ Age ║
╠══════╬════════╬═════════╬═════════╬════════╬════════╬═══════╬═════╣"""
	print(header)
	
	for o in planes.values():
		line = f"║{o.icao}║"
		
		if o.callsign == None:
			line += " " * 8 + "║"
		else:
			line += '{:{w}.{w}}'.format(o.callsign, w = '8') + "║"
						
		if o.pos[0] == None or o.pos[1] == None:
			line += " " * 9 + "║" + " " * 9 + "║"
		else:
			line += '{:{w}.{w}}'.format(str(o.pos[0]), w = '9') + "║"
			line += '{:{w}.{w}}'.format(str(o.pos[1]), w = '9') + "║"
			
		if o.altitude == None:
			line += " " * 8 + "║"
		else:
			line += '{:{w}.{w}}'.format(str(o.altitude), w = '8') + "║"
			
		if o.velocity == None:
			line += " " * 8 + "║" + " " * 7 + "║"
		else:
			line += '{:{w}.{w}}'.format(str(o.velocity[0]), w = '8') + "║"
			line += '{:{w}.{w}}'.format(str(o.velocity[1]), w = '7') + "║"
			
		line += '{:{w}.{w}}'.format(str( int( time.time() - o.last_update) ), w = '5') + "║"
	
		print(line)
		
	print('''╚══════╩════════╩═════════╩═════════╩════════╩════════╩═══════╩═════╝''')
	print()

class Packet:
	"""Class to store information and metadata for an ADS-B packet.
	
	Attributes
	----------
	msg : str
		The ADS-B message in hex-string format
	short : bool
		Whether this packet is a short squitter (True) or a long squitter (False)
	icao : str
		The ICAO hex code for packet's transmitter.
	df : int
		The downlink format of the packet.
	typecode : int
		The typecode of the packet.
	timestamp : float
		The Unix timestamp for when this packet was received.
	snr : float, optional
		The SNR of this packet in dB - as compared to the calculated noise floor.
	"""

	msg = None
	snr = None
	timestamp = -1

	short = None
	icao = None
	df = None
	typecode = None
	
	def __init__( self, msg, timestamp = None, snr = None):
		"""		
		Parameters
		----------
		msg : str
			A valid ADS-B message in hex-string format. Must have already passed a CRC check.
		timestamp : float, optional
			The Unix timestamp for when this packet was received. By default, uses the current time.
		snr : float, optional
			The calculated SNR value for this packet's signal, in dB as compared to the noise floor.
		"""
		
		self.msg = msg
		self.timestamp = timestamp if timestamp != None else time.time()
		self.snr = snr
		self.short = ( len(msg) <= 14 )
		
		self.icao = pms.adsb.icao( msg )
		self.df = pms.adsb.df( msg )
		self.typecode = pms.adsb.typecode( msg )
	
	def __repr__(self):
		return f"<ADSB_Packet msg:{self.msg}>"
		
	def __str__(self):
		dtg = datetime.fromtimestamp(self.timestamp).strftime('%d/%b/%Y %H:%M:%S')
		return f"[{dtg}] {'Short' if self.short else 'Long'} DF{self.df} ICAO: {self.icao} typecode: {self.typecode} MSG:{self.msg} SNR:{self.snr:.2f}dB"
		
class Plane:
	"""Class to store information for a tracked aircraft.
	
	Attributes
	----------
	icao : str
		The ICAO hex code for this plane.
	callsign : str
		The transmitted callsign for this plane.
	altitude : int
		The current altitude received from this plane in feet.
	velocity : float
		The current speed received from this plane in knots.
	heading : float
		The current heading received from this plane in degrees.
	pos : list(float)
		The current position of this plane, stored as [latitude, longitude].
	pos_ref : list(float)
		The nearby reference position to calculate the plane's position with, stored as [latitude, longitude].
	last_update : float
		The Unix timestamp of the last packet received from this object.
	"""

	icao = None
	callsign = None
	altitude = None
	velocity = None
	heading = None
	pos = [None, None]
	pos_ref = [None, None]
	last_update = None
	
	def __init__(self, packet=None, pos_ref=[None, None]):
		self.pos_ref = pos_ref
		if packet != None:
			self.process_packet( packet )
		
	def __repr__(self):
		return f"<ADSB_Object icao:{self.icao}>"
		
	def __str__(self):
		"""
		Returns the plane's attributes as a comma-separated string.
		"""
		ret_str = f"{self.icao},{self.callsign},{self.pos[0]},{self.pos[1]},{self.altitude},{self.velocity},{self.heading},{ int( time.time() - self.last_update ) }"
		
		return ret_str
	
	def __eq__(self, icao):
		"""
		Determine if the plane's icao matches the given icao.
		"""
		return self.icao == icao
		
	def __iter__(self):
		"""
		Return a list of its attributes as the iterable.		
		"""
		
		yield(self.icao)
		yield(self.callsign)
		yield(self.pos[0])
		yield(self.pos[1])
		yield(self.altitude)
		yield(self.velocity)
		yield(self.heading)		
		yield(int( time.time() - self.last_update))
		
	def to_dict(self):
		"""
		Return the plane's attributes as a dictionary.
		"""
	
		return {
		'icao': self.icao,
		'callsign': self.callsign,
		'lat': self.pos[0],
		'lon': self.pos[1],
		'altitude': self.altitude,
		'velocity': self.velocity,
		'heading': self.heading,
		'last_update': int( time.time() - self.last_update)
		}
	
	def process_packet(self, packet):
		"""
		Process an ADS-B packet and use it to update the plane's information.
		
		Parameters
		----------
		packet : adsb_objects.Packet
			The ADS-B packet to process.
		"""
	
		# If this object doesn't have an ICAO value, get it from the packet
		if self.icao == None:
			self.icao = packet.icao
		
		# Update the plane's last_update time based on the packet's timestamp
		self.last_update = packet.timestamp
		
		# Determine if the packet is a short or long squitter and process it accordingly
		if packet.short:
			self.process_short_packet( packet )
		else:
			self.process_long_packet( packet )
	
	def process_short_packet(self, packet):
		"""
		Process a short squitter ADS-B packet and use it to update the plane's information.
		TO BE IMPLEMENTED. NO OPERATIONS PERFORMED CURRENTLY.
		"""
		
		pass
	
	def process_long_packet(self, packet):
		"""
		Process a long squitter ADS-B packet and use it to update the plane's information.
		
		Parameters
		----------
		packet : adsb_objects.Packet
			The ADS-B packet to process.
		"""
		
		# Process callsign
		if packet.typecode >= 1 and packet.typecode <= 4:
			self.callsign = pms.adsb.callsign( packet.msg )
		
		# Process surface information
		elif packet.typecode >= 5 and packet.typecode <= 8:
			self.altitude = pms.adsb.altitude( packet.msg )
			self.pos = pms.adsb.position_with_ref( packet.msg, self.pos_ref[0], self.pos_ref[1] )
			self.velocity = pms.adsb.velocity( packet.msg )[0]
			self.heading = pms.adsb.velocity( packet.msg )[1]
		
		# Process airborne information
		elif packet.typecode >= 9 and packet.typecode <= 18:	
			self.altitude = pms.adsb.altitude( packet.msg )
			self.pos = pms.adsb.position_with_ref( packet.msg, self.pos_ref[0], self.pos_ref[1] )
						
		# Process velocity and heading information
		elif packet.df == 17 and packet.typecode == 19:		
			self.velocity = pms.adsb.velocity( packet.msg )[0]
			self.heading = pms.adsb.velocity( packet.msg )[1]
		
		
		
		
		
		
		
		
		
		
		
		