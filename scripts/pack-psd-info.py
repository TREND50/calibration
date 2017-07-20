#!/bin/env python2.7

#=======================================================
# Job steering options
#=======================================================
## Set the name
#$ -N pack-psd

## Submit job under trend group
#$ -P P_trend

## Merge the stdout et stderr in a single file
#$ -j y

## Files .e et .o copied to current working directory
#$ -cwd

## Notify stop and kill signals before issuing them.
#$ -notify

## CPU time
#$ -l ct=05:00:00

## Memory
#$ -l vmem=3.0G

## Disk space
#$ -l fsize=10.0G

## Use sps
#$ -l sps=1

#=======================================================
# Python script
#=======================================================
import rec_io, cPickle as pk, os
from sge import SGEMonitor
monitor = SGEMonitor()
config = monitor.configuration()
if config['tmpdir']:
    os.chdir(config['tmpdir'])

runinfo = '/sps/hep/trend/calib/runinfo.psd.p'
try:
    with open(runinfo, 'rb') as f:
        info = pk.load(f)
except IOError:
    info = {}

runs = rec_io.list_psd()
try:
    for run, antennas in runs.iteritems():
        try:
	    d = info[run]
	except KeyError:
	    d = info[run] = {}
	begin = True
	for antenna in antennas:
	    if antenna in d:
	        continue
	    if begin is True:
	        print 'Packing run {0} ...'.format(run)
		begin = False
	    i = rec_io.load_psd_summary(run, antenna)
            d[antenna] = i
	if begin is False:
	    with open(runinfo, 'wb+') as f:
                pk.dump(info, f, pk.HIGHEST_PROTOCOL)
	    print monitor.statistics()
	    print '--> done!'
finally:
    with open(runinfo, 'wb+') as f:
        pk.dump(info, f, pk.HIGHEST_PROTOCOL)
