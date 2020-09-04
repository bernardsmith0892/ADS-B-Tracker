import numpy as np
from numpy import *
import pyModeS as pms
import time
from datetime import datetime
import pandas as pd

def print_dashboard(adsb_objects):
	
	
	curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
	print(f"As of {curr_time}...")
	
	if len(adsb_objects) > 0:
		df = pd.DataFrame( adsb_objects.values() )
		df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
	
		print( df.to_string(index=False) )
	else:
		print("None found...")
	
	print()


def print_dashboard_ASCII(adsb_objects):
	curr_time = time.strftime('%d/%b/%Y %H:%M:%S', time.localtime())
	print(f"As of {curr_time}...")
	
	# Column sizes:
	# ICAO - 6, Callsign - 8, Lat - 9, Lon - 9, Alt - 8, Vel - 8, Head - 7, Age - 5
	header = """
╔══════╦════════╦═════════╦═════════╦════════╦════════╦═══════╦═════╗
║ ICAO ║Callsign║Latitude ║Longitude║Altitude║Velocity║Heading║ Age ║
╠══════╬════════╬═════════╬═════════╬════════╬════════╬═══════╬═════╣"""
	print(header)
	
	for o in adsb_objects.values():
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
		
	print("╚══════╩════════╩═════════╩═════════╩════════╩════════╩═══════╩═════╝")
	print()

class Packet:
	msg = None
	snr = None
	timestamp = -1

	short = None
	icao = None
	df = None
	typecode = None
	
	def __init__( self, msg, timestamp = None, snr = None):
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
		
class ADSB_Object:
	icao = None
	callsign = None
	altitude = None
	velocity = None
	heading = None
	pos = [None, None]
	pos_ref = [21.315603, -157.858093] # Reference for Honolulu, Hawaii
	last_update = None
	TTL = 90
	
	def __init__(self, packet=None):
		self.pos_ref = [21.315603, -157.858093]
		if packet != None:
			self.process_packet( packet )
		
	def __repr__(self):
		return f"<ADSB_Object icao:{self.icao}>"
		
	def __str__(self):
		ret_str = f"{self.icao},{self.callsign},{self.pos[0]},{self.pos[1]},{self.altitude},{self.velocity},{self.heading},{ int( time.time() - self.last_update ) }"
		
		return ret_str
	
	def __eq__(self, icao):
		return self.icao == icao
		
	def __iter__(self):
		yield(self.icao)
		yield(self.callsign)
		yield(self.pos[0])
		yield(self.pos[1])
		yield(self.altitude)
		yield(self.velocity)
		yield(self.heading)		
		yield(int( time.time() - self.last_update))
		
	def to_dict(self):
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
			# self.heading = pms.adsb.speed_heading( packet.msg )
		
		
		
		
		
		
		
		
		
		
		
		