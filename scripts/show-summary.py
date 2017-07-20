#!/usr/bin/env python
import cPickle as pk
import pylab as pl
import rec_io

def get_psd(antenna):
	runinfo = '/sps/hep/trend/calib/runinfo.psd.p'
	with open(runinfo, 'rb') as f:
		info = pk.load(f)
	data = []
	for _, d in info.iteritems():
		try:
			d = d[antenna]
		except KeyError:
			continue
		mean = d["mean"]
		if mean == 0.:
			continue
		values = (d["start"], d["stop"], mean, d["standard"],
			d["bandwidth_level"])
		data.append(values)
	data.sort(key=lambda x:x[0])
	return data

def get_dst(antenna):
	runinfo = '/sps/hep/trend/calib/runinfo.dst.p'
	with open(runinfo, 'rb') as f:
		info = pk.load(f)
	data = []
	for _, d in info.iteritems():
		try:
			n = d["antennas"][antenna][-1]
		except KeyError:
			continue
		t0 = d["start"]
		if t0 is None:
			continue
		t1 = d["stop"]
		if t1 is None:
			continue
		data.append((t0, t1, n/(t1-t0)))
	data.sort(key=lambda x:x[0])
	return data

def s2d(s):
	return (s-s0)/(60.*60.*24.)

def plotit(data, index):
	pl.figure()
	for datum in data:
		pl.plot((s2d(datum[0]), s2d(datum[1])), (datum[index],
			datum[index]), "k.-")
	pl.grid(True)

antenna = 128
psd = get_psd(antenna)
dst = get_dst(antenna)
s0 = dst[0][0]

plotit(psd, 2)
plotit(psd, 3)
plotit(psd, 4)
plotit(dst, 2)

pl.show()
