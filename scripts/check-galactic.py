#!/usr/bin/env python
import cPickle as pk
import sqlite3
import calendar
import time
import os
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as pl
import trend_gain


# Time origin, in seconds UNIX.
tfirst = calendar.timegm(time.strptime("01 Jan 11 00", "%d %b %y %H"))
day = 1./(24.*60.*60.)

# Settings.
Fref = 75E+06
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

tu = data[:,0]
dsl = unix2sideral(data[:,0])
hsl = np.mod(dsl*24., 24.)
day_solar = (data[:,0]-tfirst)*day+6./24.

# Get the model.
kB = 1.38E-23
RL = 112.5
RN = 0.*1.5
TE = 290.
rZE = 0.7

with open("data/skymap/skymap.00.{:.0f}.p".format(RL), "rb") as f:
	d = pk.load(f)
	i0 = np.argmin(np.absolute(d["frequencies"]-Fref*1E-06))
	y = 10*np.log10(RL*d["flux"][i0,:]+0.5*kB*TE*RL*rZE)
	f = interp1d(d["lst"], y)
	model = f(hsl)

gain = np.array([trend_gain.get(antenna, ti) for ti in tu])


# Plot the data.
kADC = 256 / 3.3 * 280E-03 / 37.
pl.style.use("deps/mplstyle-l3/style/l3.mplstyle")
pl.figure()
K = (day_solar >= 271.5) & (day_solar <= 273.5)
t = day_solar[K]
t -= t[0]
r = np.mean(power[K]) - np.mean(model[K])
pl.plot(t, 10**((power[K])/10) * kADC * 1E+12, "ko")
pl.plot(t, 10**((model[K] + r)/10) * kADC* 1E+12, "r-", linewidth=2)
pl.xlabel("solar time (day)")
pl.ylabel("PSD (mV$^2$ / MHz)")
pl.savefig("exGain.png")

pl.figure()
pl.plot(t, 10**(gain[K] / 20.) / 1E+06, "ko")
pl.xlabel("solar time (day)")
pl.ylabel("gain, $\overline{G}_V$ (V / $\mu$V)")
pl.savefig("exGain2.png")

pl.show()
