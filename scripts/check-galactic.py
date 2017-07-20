#!/usr/bin/env python
import cPickle as pk
import sqlite3
import calendar
import time
import os
import numpy as np
from scipy.interpolate import interp1d
import pylab as pl

# Time origin, in seconds UNIX.
tfirst = calendar.timegm(time.strptime("01 Jan 11 00", "%d %b %y %H"))
day = 1./(24.*60.*60.)

# Settings.
Fref = 55E+06
antenna = 113

# Get the antenna data.
def db_request(antenna, frequency):
	connection = result = None
	frequency /= 1E+06
	strtable = "power{:.0f}".format(frequency)
	sqlcmd = """SELECT time, value, run from power{:.0f} where antenna={:}
		ORDER BY time ASC""".format(frequency, antenna)
	strdb = "data/psd/psd.{:.0f}.db".format(frequency)
	try:
		connection = sqlite3.connect(strdb)
		cursor = connection.cursor()
		cursor.execute(sqlcmd)
		result = cursor.fetchall()
	finally:
		if connection is not None:
			connection.close()
	return result

data = np.array(db_request(antenna, Fref))
power = data[:,1]*1E-03-120.

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

dsl = unix2sideral(data[:,0])
hsl = np.mod(dsl*24., 24.)
day_solar = (data[:,0]-tfirst)*day+6./24.

# Get the model.
RL = 112.
kB = 1.38E-23
T = 297.

fA, RA, XA = np.load("data/nec2/Zbutterfly.npy")
fRA = interp1d(fA*1E+06, RA)
fXA = interp1d(fA*1E+06, XA)

with open("data/skymap/skymap.00.{:.0f}.p".format(RL), "rb") as f:
	d = pk.load(f)
	model = []
	i0 = np.argmin(np.absolute(d["frequencies"]-Fref*1E-06))
	RA, XA = fRA(Fref), fXA(Fref)
	R = ((RA+RL)**2+XA**2)/RL
	y = 10*np.log10(2*R*d["flux"][i0,:]+4.*(RL+RA)*kB*T)
	f = interp1d(d["lst"], y)
	model = f(hsl)

# Plot the data.
pl.figure()
K = (day_solar >= 271.5) & (day_solar <= 272.5)
pl.plot(day_solar[K], power[K]-np.mean(power[K]), "ko")
pl.plot(day_solar[K], model[K]-np.mean(model[K]), "r.")
pl.grid(True)

pl.figure()
pl.plot(day_solar, power-model, "k.")
pl.grid(True)

pl.show()
