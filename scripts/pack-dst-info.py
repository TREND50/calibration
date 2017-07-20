#!/bin/env python2.7

#=======================================================
# Job steering options
#=======================================================
## Set the name
#$ -N pack-dst

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

runinfo = '/sps/hep/trend/calib/runinfo.dst.p'
try:
    with open(runinfo, 'rb') as f:
        info = pk.load(f)
except IOError:
    info = {}

dsts = rec_io.list_dst()
try:
    for run, (tag, depth) in dsts.iteritems():
        if run in info:
	    continue
	print 'Packing run {0} ...'.format(run)
	try:
	    i = rec_io.load_dst_summary(run, tag, depth)
	except MemoryError:
	    print monitor.statistics()
	    print '\033[31m--> memory error! Skipping.\033[0m'
	else:
            info[run] = i
	    with open(runinfo, 'wb+') as f:
                pk.dump(info, f, pk.HIGHEST_PROTOCOL)
	    print monitor.statistics()
	    print '--> done!'
finally:
    with open(runinfo, 'wb+') as f:
        pk.dump(info, f, pk.HIGHEST_PROTOCOL)
