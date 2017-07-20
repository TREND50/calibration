#!/usr/bin/env python
import calendar
import time
import numpy as np
import pylab as pl

day = 60.*60.*24.

# Local sideral time.
def unix2sideral(ts):
    tref = calendar.timegm(time.strptime("01 Jan 00 12", "%d %b %y %H"))
    longitude = 86.71
    D = (ts-tref)*day
    hsl = 18.697374558+24.06570982441908*D+longitude/15.
    return hsl/24.

def sideral2unix(ts):
    tref = calendar.timegm(time.strptime("01 Jan 00 12", "%d %b %y %H"))
    longitude = 86.71
    hsl = ts*24.
    D = (hsl-longitude/15-18.697374558)/24.06570982441908
    return D/day+tref

data = np.loadtxt('data/load/gains.txt')
antenna = data[:,0]
tu = data[:,1]
gain = data[:,2]

dsl = unix2sideral(tu)
hsl = np.mod(dsl*24., 24.)

n, h = np.histogram(hsl, np.linspace(0., 24., 25))
h = 0.5*(h[1:]+h[:-1])

pl.figure()
pl.plot(h, n, 'ko')
pl.grid(True)
pl.show()
