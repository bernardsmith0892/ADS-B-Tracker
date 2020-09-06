import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.express as px
import pandas as pd

# Suppress non-error logging to the console
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

external_stylesheets = ['app.css']
mapstyle = 'carto-positron'
app = dash.Dash(__name__, title='ADS-B Tracker', update_title=None, external_stylesheets=external_stylesheets)

def generate_table(df, max_rows=26):
	"""
	Generate an HTML table for a DataFrame using Dash HTML components. Taken from: https://stackoverflow.com/questions/52213738/html-dash-table
	
	Parameters
	----------
	df : pd.DataFrame
		The DataFrame to convert into an HTML table.
	max_rows : int, optional
		The maximum number of rows to output into the table.
	
	Returns
	-------
	html.Table
		The HTML version of the given DataFrame.
	
	"""
	
	table = [html.Caption("Tracked Aircraft")] + [html.Tr([html.Th(col) for col in df.columns]) ] + [html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(min(len(df), max_rows))]
			
	return html.Table(
		children=table
    )
	
	
def planes_to_df(planes):
	"""
	Convert a dict of Plane objects into a pd.DataFrame.
	Performs check to properly handle and convert an empty dictionary.
	
	Parameters
	----------
	planes : dict(ao.Plane)
		A dictionary of Plane objects. Key value is arbitrary.
	
	Returns
	-------
	pd.DataFrame
		An 8-column DataFrame converted from the dictionary.
	"""
	
	if len(planes) > 0:
		df = pd.DataFrame( planes.values() )
	else:
		df = pd.DataFrame( [None] * 7 + [0] )
		df = df.T
	
	df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
	
	return df
	
	
def server(pos_ref, planes, packets):
	"""
	Setup the Dash web server to display air traffic information.
	
	Parameters
	----------
	pos_ref : list(float)
		The location of the tracker's ground station. Used as the initial center for the map.
	planes : dict(ao.Plane)
		Dictionary of the currently tracked aircraft.
		Dictionary of the currently tracked aircraft.
		Positions are plotted on the map and detailed information is displayed in the table.
	packets : list(ao.Packet)
		List of the last received ADS-B packets. Their information and timestamp is displayed on the dashboard.	
	"""
	
	# Initial setup for the map
	df = planes_to_df(planes)
	map = px.scatter_mapbox(center={ 'lat' : pos_ref[0], 'lon' : pos_ref[1] }, mapbox_style = mapstyle)
	
	# Setting up the div information for the aircraft table and packet displays
	adsb_table_div = html.Div(
		children=generate_table(df),
		id='adsb-table',
		style={
			"width" : "50%"
		}
	)
	packet_div = html.Div(
		id='packet-list',
		children="",
		style={	
			"flex-grow" : "1"
		}
	) 

	# Layout of the webpage
	app.layout = html.Div(children=[
		# Title header
		html.H1(
			children='ADS-B Tracker'
		),
		
		# Map display
		dcc.Graph(
			id='adsb-map',
			figure=map
		),
		
		# The aircraft table and packet displays
		html.Div(
			children=[adsb_table_div, packet_div],
			style={ 
				"display" : "flex" 
			}
		),		
	
		# Request an update every second
		dcc.Interval(
				id='interval-component',
				interval=1*1000, # in milliseconds
				n_intervals=0
		)]
	)

	# Function to update map data
	@app.callback(Output('adsb-map', 'figure'),
				  [Input('interval-component', 'n_intervals')])
	def update_map(n):
		df = planes_to_df(planes)
		
		map = px.scatter_mapbox(center={ 'lat' : pos_ref[0], 'lon' : pos_ref[1] }, mapbox_style = mapstyle)
		map['layout']['uirevision'] = True
		map['layout']['margin']['t'] = 5
		map['layout']['margin']['b'] = 5
		
		map.add_scattermapbox(lat=[pos_ref[0]], lon=[pos_ref[1]], text='Grnd Stn', hoverinfo="text", name='Ground Station')
		map.add_scattermapbox(lat=df['Latitude'], lon=df['Longitude'], text=df['ICAO'], hoverinfo="text", name='Aircraft')
		
		return map

	# Function to update the aircraft table
	@app.callback(Output('adsb-table', 'children'),
				  [Input('interval-component', 'n_intervals')])
	def update_table(n):
		df = planes_to_df(planes)
		return generate_table(df)

	# Function to update packet display
	@app.callback(Output('packet-list', 'children'),
				  [Input('interval-component', 'n_intervals')])		
	def update_packets(n):
		MAX_LINES = 25
				
		out_str = ""
		
		for p in packets[-MAX_LINES:]:
			out_str = str(p) + '\n' + out_str
		
		out_str = "Last received ADS-B Packets:\n" + out_str
		
		return html.Pre(children=out_str)