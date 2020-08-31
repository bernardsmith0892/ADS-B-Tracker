import numpy as np
from numpy import *
import pyModeS as pms
import time

class Packet:
	msg = None
	timestamp = -1

	short = None
	icao = None
	df = None
	typecode = None
	
	def __init__( self, msg, timestamp = time.time()):
		self.msg = msg
		self.timestamp = timestamp
		self.short = ( len(msg) <= 14 )
		
		self.icao = pms.adsb.icao( msg )
		self.df = pms.adsb.df( msg )
		self.typecode = pms.adsb.typecode( msg )
	
	def __repr__(self):
		return f"<ADSB_Packet msg:{self.msg}>"
		
	def __str__(self):
		return f"[{self.timestamp}] Short: {self.short} DF{self.df} ICAO: {self.icao} typecode: {self.typecode} MSG:{self.msg}"
		
class ADSB_Object:
	icao = None
	callsign = "NONE___"
	altitude = None
	heading = None
	velocity = None
	pos = (None, None)
	pos_ref = [21.315603, -157.858093] # Reference for Honolulu, Hawaii
	last_update = None
	
	def __init__(self, packet):
		self.pos_ref = [21.315603, -157.858093]
		self.process_packet( packet )
		
	def __repr__(self):
		return f"<ADSB_Object icao:{self.icao}>"
		
	def __str__(self):
		ret_str = f"{self.icao}\t{self.callsign}  \t{self.pos[0]}\t{self.pos[1]}\t{self.altitude}\t{self.velocity}\t{self.heading}\t{ int( time.time() - self.last_update) }"
		
		return ret_str
	
	def __eq__(self, icao):
		return self.icao == icao
	
	def process_packet(self, packet):
		# If this object doesn't have an ICAO value, get it from the packet
		if self.icao == None:
			self.icao = packet.icao
		
		self.last_update = packet.timestamp
		if packet.short:
			self.process_short_packet( packet )
		else:
			self.process_long_packet( packet )
	
	def process_short_packet(self, packet):
		pass
	
	def process_long_packet(self, packet):
		# Process callsign
		if packet.typecode >= 1 and packet.typecode <= 4:
			print(pms.adsb.callsign( packet.msg ))
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
		elif packet.typecode == 19:		
			self.velocity = pms.adsb.velocity( packet.msg )[0]
			self.heading = pms.adsb.velocity( packet.msg )[1]
			# self.heading = pms.adsb.speed_heading( packet.msg )
		
		
		
		
		
		
		
		
		
		
		
		