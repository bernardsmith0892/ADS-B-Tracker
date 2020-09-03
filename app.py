import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, title='ADS-B Tracker', update_title=None, external_stylesheets=external_stylesheets)

def generate_table(dataframe, max_rows=26):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns]) ] +
        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

def server(pos_ref, adsb_objects, packets):
	if len(adsb_objects) > 0:
		df = pd.DataFrame( adsb_objects.values() )
		df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
		fig = px.scatter_mapbox(df, lat='Latitude', lon='Longitude', text='ICAO', hover_data=['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age'], center=pos_ref, zoom=10,
					  mapbox_style="carto-positron")
	else:
		df = pd.DataFrame( [None] * 8 )
		df = df.T
		df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
		fig = px.scatter_mapbox(df, lat='Latitude', lon='Longitude', text='ICAO', hover_data=['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age'], center=pos_ref, zoom=10,
					  mapbox_style="carto-positron")
		
	fig.show()

	app.layout = html.Div(children=[
		html.Title(
			children='ADS-B Tracker'
		),
		
		dcc.Graph(
			id='adsb-map',
			figure=fig
		),
		
		html.Table(
			id='adsb-table',
			children=generate_table(df)
		),

		html.Br(),
		
		dcc.Markdown(
			id='packet-list',
			children=""
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
		if len(adsb_objects) > 0:
			df = pd.DataFrame( adsb_objects.values() )
			df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
		else:
			df = pd.DataFrame( [None] * 8 )
			df = df.T
			df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
		
		fig = px.scatter_mapbox(df, lat='Latitude', lon='Longitude', text='ICAO', hover_data=['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age'], center=pos_ref, zoom=10,
					  mapbox_style="carto-positron")
		
		return fig

	@app.callback(Output('adsb-table', 'children'),
				  [Input('interval-component', 'n_intervals')])
	def update_table(n):
		if len(adsb_objects) > 0:
			df = pd.DataFrame( adsb_objects.values() )
			df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
		else:
			df = pd.DataFrame( [None] * 8 )
			df = df.T
			df.columns = ['ICAO', 'Callsign', 'Latitude', 'Longitude', 'Altitude', 'Velocity', 'Heading', 'Age']
		return generate_table(df)

	@app.callback(Output('packet-list', 'children'),
				  [Input('interval-component', 'n_intervals')])		
	def update_packets(n):
		MAX_LINES = 20
		out_str = ""
		
		for p in packets[-MAX_LINES:]:
			out_str = str(p) + '\n' + out_str
		
		out_str = '```text\nLast received ADS-B Packets:\n' + out_str
		return out_str

if __name__ == '__main__':
    app.run_server(debug=True)