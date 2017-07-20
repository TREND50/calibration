#!/usr/bin/env python
import sqlite3
import calendar
import time
import os
import numpy as np
import pylab as pl
from scipy.optimize import fmin_powell as fmin

# Time origin, in seconds UNIX.
tfirst = calendar.timegm(time.strptime("01 Jan 11 00", "%d %b %y %H"))
day = 1./(24.*60.*60.)

# Settings.
Fref = 60E+06
strdb = "data/psd/psd.{:.0f}.db".format(Fref/1E+06)
antenna = 107

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

# Loop over sideral days.
def galactic_noise_model(x, h):
	d = np.minimum(np.absolute(h-x[0]), np.absolute(h+24.-x[0]))
	return x[2]*np.exp(-0.5*(d/x[1])**2)+x[3]

def range_constraint(x, x0, dx):
	c = abs(x-x0)
	if c <= dx:
		return 0.
	return 1E+04*(c/dx-1.)**2

def fit_function(x, h, p):
	h0 = 18.0
	s0 = 2.5
	A0 = 3.0
	y = galactic_noise_model(x, h)-p
	f = np.mean(y**2)
	f += range_constraint(x[0], h0, 3.0)
	f += range_constraint(x[1], s0, 1.0)
	f += range_constraint(x[2], A0, 2.0)
	return f
	
def fit_model(x, h, p):
	# Raw fit.
	x, f, _, _, _, _ = fmin(fit_function, x, args=(h, p), disp=0,
		full_output=1)
	# Refit removing noisy points.
	y = galactic_noise_model(x, h)
	K = (p-y) <= 1.
	x, f, _, _, _, _ = fmin(fit_function, x, args=(h[K], p[K]), disp=0,
		full_output=1)
	return x, f

model = []
t0 = int(dsl[0])+1.
n = 0
while t0 < dsl[-1]-1.:
	# Select data for the given sideral day.
	k0 = np.argmin(np.absolute(dsl-t0))
	k1 = np.argmin(np.absolute(dsl-t0-1.))
	t0 += 1.
	# Check the data sample length.
	if k0 == k1:
		continue
	Dt = dsl[k1]-dsl[k0]
	if abs(Dt-1.) > 5E-2:
		continue
	# Extract and format the daylies data.
	h = hsl[k0:k1+1]
	p = power[k0:k1+1]
	data = zip(h, p)
	data.sort()
	h, p = map(np.array, zip(*data))
	# Check the total data coverage.
	dt = np.min(np.diff(h))
	coverage = dt*len(h)/Dt
	if coverage < 0.5:
		continue
	# Check the coverage of the galactic center.
	coverage = sum((h >= 16.) & (h <= 20.))*dt/(Dt*4./24.)
	if coverage < 0.75:
		continue
	# Do the fit.
	x, f = fit_model((17.9, 3., 3., np.mean(p)), h, p)
	hm = np.linspace(0., 24., 241)
	dm = (sideral2unix(t0-1.+hm/24.)-tfirst)*day
	pm = galactic_noise_model(x, hm)
	model += zip(dm, pm)
	# Show the fit result.
	if  ((n % 10) == 0):
		pl.figure()
		pl.plot(day_solar[k0:k1+1], p, "k.-")
		print n/10+1, x, f
		pl.plot(dm, pm, "r-")
		# pl.plot(h, galactic_noise_model(x, h), "r-")
		pl.grid(True)
	n += 1

pl.figure()
pl.plot(day_solar, power, "k.")
d, p = zip(*model)
pl.plot(d, p, "r-")
pl.grid(True)

pl.show()
