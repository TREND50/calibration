#!/usr/bin/env python
import sqlite3
import calendar
import time
import os
import numpy as np
import pylab as pl

# Time origin, in seconds UNIX.
tfirst = calendar.timegm(time.strptime("01 Jan 11 00", "%d %b %y %H"))
day = 1./(24.*60.*60.)

# Settings.
Fref = (35E+06, 65E+06)
antenna = 107

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

data_L = np.array(db_request(antenna, Fref[0]))
data_H = np.array(db_request(antenna, Fref[1]))
power_L = data_L[:,1]*1E-03
power_H = data_H[:,1]*1E-03

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
	
dsl = unix2sideral(data_L[:,0])
hsl = np.mod(dsl*24., 24.)
day_solar = (data_L[:,0]-tfirst)*day+6./24.

# Plot the data.	
pl.figure()
pl.plot(day_solar, power_H, "k.")
pl.plot(day_solar, power_L+30., "r.")
pl.grid(True)

pl.show()
