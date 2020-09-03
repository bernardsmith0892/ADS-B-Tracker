from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource, axes
import numpy as np

'''
║a499c3║HAL1307_║21.32525 ║-157.9481║100     ║122     ║90.47  ║435  ║
║aa75ef║UAL2380_║21.32525 ║-157.9552║225     ║120     ║89.52  ║0    ║
'''

output_file("radar.html")

'''points = {
	'lat': [21.32525, 21.32525],
	'lon': [-157.9481, -157.9552]
}
source= ColumnDataSource(data=points)'''

planes = [[21.32525, -157.9481, 90.47],[21.32525, -157.9552, 89.52]]
home = [21.315603, -157.858093]



p = figure()
p.square(home[0], home[1], color="orange", size=15)
for pnt in points:
	p.square(pnt[0], pnt[1], angle=pnt[2], size=10)
	p.triangle(pnt[0], pnt[1], angle=pnt[2], color="orange", size=10)

# show the results
show(p)