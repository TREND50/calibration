#!/usr/bin/env python
import sqlite3
import calendar
import time
import os
from datetime import datetime, timedelta
import numpy as np
import pylab as pl
from scipy.interpolate import UnivariateSpline
import rec_io

# Time origin, in seconds UNIX.
tfirst = calendar.timegm(time.strptime("01 Jan 11 00", "%d %b %y %H"))
day = 1./(24.*60.*60.)

# Read the temperature data.
tempdir = "data/temp"
temperature = []
for tag in ("1109", "1110", "1111", "1112", "1201", "1202"):
	tempfile = os.path.join(tempdir, "temp_20{:}.mat".format(tag))
	data = rec_io.load_mat(tempfile)
	t = [(calendar.timegm((datetime.fromordinal(int(ti))+timedelta(days=ti%1)-
		timedelta(days=366)).timetuple())-tfirst)*day
		for ti in data["time"]]
	temperature += zip(t, data["t"])
temperature = np.array(temperature)

Fref = 60E+06
strdb= "data/psd/psd.{:.0f}.db".format(Fref/1E+06)
antenna = 137

def db_request(antenna):
	connection = result = None
	strtable = "power{:.0f}".format(Fref/1E+06)
	sqlcmd = """SELECT time, value from power{:.0f} where antenna={:}
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

# Get the antenna data.
data = np.array(db_request(antenna))
power = data[:,1]*1E-03

# Local sideral time.
tref = calendar.timegm(time.strptime("01 Jan 00 12", "%d %b %y %H"))
longitude = 87.616852
D = (data[:,0]-8.*60.*60.-tref)*day
hsl = 18.697374558+24.06570982441908*D+longitude/15.
dsl = hsl/24.-4100.
hsl = np.mod(hsl, 24.)
time = data[:,0]-tfirst
time = time*day

# Calibration set.
t0 = 70.7
K = (dsl >= t0) & (dsl <= t0+1.)
hcal = hsl[K]
pcal = power[K]
pcal -= np.mean(pcal)
tmp = zip(hcal, pcal)
tmp.sort(key=lambda x:x[0])
hcal, pcal = zip(*tmp)
calibration = UnivariateSpline(hcal, pcal, s=0.005*len(hcal))

pl.figure()
pl.plot(hcal, pcal, "k.")
pl.plot(hcal, calibration(hcal), "r-")
pl.grid(True)

pl.figure()
pl.plot(dsl, power, "k.")
pl.grid(True)

pl.figure()
pl.plot(time, power, "k.")
pl.plot(time, power-calibration(hsl), "b.")
_, _, ymin, ymax = pl.axis()
for k in xrange(1, 3):
	pl.plot((365.25*k, 365.25*k), (ymin, ymax), "r-")
	pl.plot((365.25*(k-0.5), 365.25*(k-0.5)), (ymin, ymax), "r--")
pl.plot(temperature[:,0], temperature[:,1], "g.-")
pl.grid(True)

pl.show()
