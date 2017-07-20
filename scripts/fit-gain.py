#!/usr/bin/env python
import sqlite3
import calendar
import time
import os
import numpy as np
import pylab as pl
from scipy.optimize import fmin_l_bfgs_b as fminb

# Time origin, in seconds UNIX.
tfirst = calendar.timegm(time.strptime("01 Jan 11 00", "%d %b %y %H"))
day = 1./(24.*60.*60.)

# Settings.
Fref = 60E+06
strdb = "data/psd/psd.{:.0f}.db".format(Fref/1E+06)
antenna = 115 # 107

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

# Extract the nodes.
def node_model(node, dsl):
	return node[2]*np.exp(-0.5*((dsl-node[0])/node[1])**2)+node[3]
	
def node_objective(node, dsl, power):
	m = node_model(node, dsl)
	return np.mean((m-power)**2)

def node_fit(node, bound, dsl, power):
	d0 = np.mean(bound[0])
	k0 = np.argmin(np.absolute(dsl-d0+0.5))
	k1 = np.argmin(np.absolute(dsl-d0-0.5))
	d = dsl[k0:k1+1]
	p = power[k0:k1+1]
	K = np.absolute(p-np.median(p)) < 7.
	node, f, _ = fminb(node_objective, node, args=(d[K], p[K]),
		approx_grad=1, bounds=bound)
	return list(node), f

nodes = []
bounds = []
hsl_max = 18.
dsl_max = hsl_max/24.
t0 = int(dsl[0])+dsl_max
while t0 < dsl[-1]:
	k0 = np.argmin(np.absolute(dsl-t0+0.5))
	k1 = np.argmin(np.absolute(dsl-t0-0.5))
	t0 += 1.
	# Check the data sample length.
	if k0 == k1:
		continue
	Dt = dsl[k1]-dsl[k0]
	# Extract the data.
	d = dsl[k0:k1+1]-t0+1.
	p = power[k0:k1+1]
	# Check the coverage of the galactic center.
	dt = np.min(np.absolute(np.diff(d)))
	coverage = sum((d >= -2./24.) & (d <= 2./24.))*dt/(Dt*4./24.)
	#if coverage < 0.75:
	#	continue
	# Append the node.
	cpu0 = time.time()
	print "o) Appending node {:} at {:.2f}".format(len(nodes)/4+1, t0)
	node = [t0-1., 2.5/24., 3., np.mean(p)]
	dh0 = 3./24.
	ds0 = 1./24.
	dA0 = 2.
	bound = [(node[0]-dh0, node[0]+dh0), (node[1]-ds0, node[1]+ds0),
		(node[2]-dA0, node[2]+dA0), (None, None)]
	node, _ = node_fit(node, bound, dsl, power)
	nodes += node
	bounds += bound
	dcpu = time.time()-cpu0
	print "  --> Done in {:.1f} s".format(dcpu)

# Global model and fit.
node_max_distance = 1.2

def galactic_noise_model(nodes, dsl):
	p = np.zeros(dsl.shape)
	K = np.zeros(dsl.shape)
	n_nodes = len(nodes)/4
	node1 = nodes[:4]
	for i in xrange(n_nodes-1):
		node0 = node1
		node1 = nodes[(i+1)*4:(i+2)*4]
		k0 = np.argmin(np.absolute(dsl-node0[0]))
		k1 = np.argmin(np.absolute(dsl-node1[0]))
		if node1[0]-node0[0] <= node_max_distance: 
			d = dsl[k0:k1]
			p0 = node0[2]*np.exp(-0.5*((d-node0[0])/
				node0[1])**2)+node0[3]
			p1 = node1[2]*np.exp(-0.5*((d-node1[0])/
				node1[1])**2)+node1[3]
			p[k0:k1] = p0+(d-node0[0])/(node1[0]-node0[0])*(p1-p0)
			K[k0:k1] = 1
		else:
			k0b = np.argmin(np.absolute(dsl-node0[0]-0.5))
			d = dsl[k0:k0b]
			p[k0:k0b] = node0[2]*np.exp(-0.5*((d-node0[0])/
				node0[1])**2)+node0[3]
			K[k0:k0b] = 1
			k1b = np.argmin(np.absolute(dsl-node1[0]+0.5))
			d = dsl[k1b:k1]
			p[k1b:k1] = node1[2]*np.exp(-0.5*((d-node1[0])/
				node1[1])**2)+node1[3]
			K[k1b:k1] = 1
	return (K == 1), p
	
pl.figure()
pl.plot(dsl, power, "k.")
K, model = galactic_noise_model(nodes, dsl)
pl.plot(dsl[K], model[K], "r-")
pl.grid(True)

pl.figure()
dm = np.array(nodes[::4])
pl.plot(dm, np.mod(dm*24., 24.), "ko")
pl.grid(True)

pl.show()
