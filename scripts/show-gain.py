#!/usr/bin/env python
import time
import numpy as np
import pylab as pl
from matplotlib import cm
import trend_gain


antennas = range(101, 139)+[140,]+range(148, 159)
tu = np.linspace(1.30E+09, 1.36E+09, 100000)

gain = np.zeros((len(antennas), len(tu)))
for i, antenna in enumerate(antennas):
	print "o) Processing antenna {:}".format(antenna)
	t0 = time.time()
	gain[i,:] = [trend_gain.get(antenna, ti) for ti in tu]
	dt = time.time()-t0
	print "  --> Done in {:.0f} s".format(dt)

# Show the result.
color = [cm.jet(x) for x in np.linspace(1., 0., len(antennas))]
pl.figure()
for i, antenna in enumerate(antennas):
	pl.plot(tu, gain[i,:], ".", color=color[i])
pl.grid(True)
pl.xlabel("time unix (s)")
pl.ylabel("gain (dB)")

pl.figure()
for i, antenna in enumerate(antennas):
	pl.plot(i/float(len(antennas)), antenna, "o",
		color=color[i], markersize=24.)
pl.xlabel("color index")
pl.ylabel("antenna id")

pl.show()
