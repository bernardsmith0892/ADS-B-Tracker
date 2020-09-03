import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.express as px
import pandas as pd

external_stylesheets = ['app.css']
app = dash.Dash(__name__, title='ADS-B Tracker', update_title=None, external_stylesheets=external_stylesheets)

TTL = 90

def generate_table(dataframe, max_rows=26):
	table = [html.Caption("Tracked Aircraft")] + [html.Tr([html.Th(col) for col in dataframe.columns]) ] + [html.Tr([html.Td(dataframe.iloc[i][col]) for col in dataframe.columns]) for i in range(min(len(dataframe), max_rows))]
			
	return html.Table(
		children=table
    )
	
def asdb_objects_to_df(adsb_objects):
	if len(adsb_objects) > 0:
		df = pd.DataFrame( adsb_objects.values() )
	else:
		df = pd.DataFrame( [None] * 7 + [0] )
		df = df.T
	
	df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
	
	return df
	
def ttl_inverse(ts):
	if ts >= 90:
		return 0
	else:
		return 90 - ts

def server(pos_ref, adsb_objects, packets):
	ref_obj = {'ICAO':None, 'Callsign':'REF_PNT', 'Latitude':pos_ref['lat'], 'Longitude':pos_ref['lon'], 'Altitude':None, 'Velocity':None, 'Heading':None, 'Age':0}

	df = asdb_objects_to_df(adsb_objects)
	df = df.append(ref_obj, ignore_index=True)
	df['Age'] = df['Age'].apply(ttl_inverse)
	fig = px.scatter_mapbox(df, lat='Latitude', lon='Longitude', text='ICAO', hover_data=['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age'], center=pos_ref, zoom=10,
			mapbox_style="carto-positron", size='Age', size_max=10)
		
	fig.show()
	
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

	app.layout = html.Div(children=[
		html.H2(
			children='ADS-B Tracker'
		),
		
		dcc.Graph(
			id='adsb-map',
			figure=fig
		),
		
		html.Div(
			children=[adsb_table_div, packet_div],
			style={ "display" : "flex" }
		),		
	
		dcc.Interval(
				id='interval-component',
				interval=1*1000, # in milliseconds
				n_intervals=0
		)
	])

	@app.callback(Output('adsb-map', 'figure'),
				  [Input('interval-component', 'n_intervals')])
	def update_map(n):
		df = asdb_objects_to_df(adsb_objects)
		df = df.append(ref_obj, ignore_index=True)
		df['Age'] = df['Age'].apply(ttl_inverse)
		fig = px.scatter_mapbox(df, lat='Latitude', lon='Longitude', text='ICAO', hover_data=['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age'], center=pos_ref, zoom=10,
			mapbox_style="carto-positron", size='Age', size_max=10)
		
		return fig

	@app.callback(Output('adsb-table', 'children'),
				  [Input('interval-component', 'n_intervals')])
	def update_table(n):
		df = asdb_objects_to_df(adsb_objects)
		return generate_table(df)

	@app.callback(Output('packet-list', 'children'),
				  [Input('interval-component', 'n_intervals')])		
	def update_packets(n):
		MAX_LINES = 20
				
		out_str = ""
		
		for p in packets[-MAX_LINES:]:
			out_str = str(p) + '\n' + out_str
		
		out_str = "Last received ADS-B Packets:\n" + out_str
		
		return html.Pre(children=out_str)