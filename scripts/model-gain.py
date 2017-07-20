#!/usr/bin/env python
import sqlite3
import calendar
import time
import os
import numpy as np
import pylab as pl
from scipy.interpolate import UnivariateSpline
import rec_io

# Time origin, in seconds UNIX.
tfirst = calendar.timegm(time.strptime("01 Jan 11 00", "%d %b %y %H"))
day = 1./(24.*60.*60.)

# Settings.
Fref = 20E+06
strdb = "data/psd/psd.{:.0f}.db".format(Fref/1E+06)
antenna = 115

# Get the antenna data.
def db_request(antenna):
	connection = result = None
	strtable = "power{:.0f}".format(Fref/1E+06)
	sqlcmd = """SELECT time, value, run from power{:.0f} where antenna={:}
		ORDER BY time ASC""".format(Fref/1E+06, antenna)
	try:
		connection = sqlite3.connect(strdb)
		cursor = connection.cursor()
		cursor.execute(sqlcmd)
		result = cursor.fetchall()
	finally:
		if connection is not None:
			connection.close()
	return result

data = np.array(db_request(antenna))
power = data[:,1]*1E-03
run = data[:,2]

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
day_solar = (data[:,0]-tfirst)*day

# Load the galactic signal.
galactic0 = rec_io.load_mat("data/galactic/{:}.lin.0.mat".format(antenna))
galactic1 = rec_io.load_mat("data/galactic/{:}.lin.1.mat".format(antenna))
hsl_theo = galactic0["Lst"]
pwr_theo = galactic0["v_gal"]**2+galactic1["v_gal"]**2
pwr_theo = 10.*np.log10(pwr_theo)
pwr_theo -= np.mean(pwr_theo)
f_theo = UnivariateSpline(hsl_theo, pwr_theo, s=0.)

# Substract the galactic fluctuation.
pl.figure()
pl.plot(hsl_theo, pwr_theo, "k.")
pl.plot(hsl_theo, f_theo(hsl_theo), "r-")
pl.grid(True)
	
pl.figure()
pl.plot(day_solar, power, "k.")
K = (run == 3759)
pl.plot(day_solar[K], power[K], "ro")
print np.nonzero(K == True)
K = (run == 3761)
pl.plot(day_solar[K], power[K], "gs")
print np.nonzero(K == True)
# pl.plot(day_solar, f_theo(hsl)+13., "r.")
pl.grid(True)

pl.show()
