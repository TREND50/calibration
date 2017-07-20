#!/usr/bin/env python
import cPickle as pk
import sqlite3
import sys
import numpy as np
import pylab as pl

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

def get_tstart(antenna):
	data = np.array(db_request(antenna, 75.E+06))
	tu = data[:,0]
	runs = data[:,2]
	t0, t1 = [], []
	r = np.unique(runs)
	for run in r:
		K = runs == run
		t0.append(np.min(tu[K]))
		t1.append(np.max(tu[K]))
	return r, t0, t1

antennas = range(101, 139)+[140,]+range(148, 159)
data = {}
for antenna in antennas:
	r, t0, _ = get_tstart(antenna)
	for t0i, ri in zip(t0, r):
		try:
			data[ri].append(t0i)
		except KeyError:
			data[ri] = [t0i]

runs = np.sort(data.keys())
mu = []
sigma = []
for run in runs:
	d = np.array(data[run])
	K = d >= 1.0E+09
	d = d[K]
	if len(d) == 0:
		mu.append(None)
		sigma.append(None)
		continue
	m = np.median(d)
	K = np.absolute(d-m) <= 120.
	d = d[K]
	if len(d) == 0:
		mu.append(None)
		sigma.append(None)
		continue
	elif len(d) == 1:
		mu.append(d[0])
		sigma.append(0.)
	else:
		mu.append(np.median(d))
		sigma.append(np.std(d))

# Dump the result.
with open("data/gain/run-times.py", "wb+") as f:
	d = {}
	for run, t0 in zip(runs, mu):
		if t0 is None:
			continue
		d[run] = t0
		
	pk.dump(d, f, -1)

# Plot the result.
pl.figure()
pl.plot(runs, mu, "ko")
pl.grid(True)

pl.figure()
pl.plot(runs, sigma, "ko")
pl.grid(True)

pl.show()
