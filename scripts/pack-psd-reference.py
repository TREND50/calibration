#!/bin/env python2.7

#=======================================================
# Job steering options
#=======================================================
## Set the name
#$ -N psd-ref

## Submit job under trend group
#$ -P P_trend

## Merge the stdout et stderr in a single file
#$ -j y

## Files .e et .o copied to current working directory
#$ -cwd

## Notify stop and kill signals before issuing them.
#$ -notify

## CPU time
#$ -l ct=01:00:00

## Memory
#$ -l vmem=2.0G

## Disk space
#$ -l fsize=1.0G

## Use sps
#$ -l sps=1

#=======================================================
# Python script
#=======================================================
import os
import sqlite3
import math
import rec_io
from sge import SGEMonitor

# Settings.
Fref = 95E+06
strdb = "/sps/hep/trend/calib/psd.{:.0f}.db".format(Fref/1E+06)

# Hook the SGE monitor.
monitor = SGEMonitor()
config = monitor.configuration()
if config["tmpdir"]:
	os.chdir(config["tmpdir"])
	
def db_operate(sqlcmd, commit=False):
	connection = result = None
	try:
		connection = sqlite3.connect(strdb)
		cursor = connection.cursor()
		cursor.execute(sqlcmd)
		if commit:
			connection.commit()
		else:
			result = cursor.fetchall()
	finally:
		if connection is not None:
			connection.close()
	return result

# Initialise the DB table, if needed.
strtable = "power{:.0f}".format(Fref/1E+06)
db_operate("""CREATE TABLE IF NOT EXISTS {:}(
	time INTEGER,
	antenna INTEGER,
	run INTEGER,
	value INTEGER,
	PRIMARY KEY(time, antenna)
	)""".format(strtable), commit=True)

# Loop on PSD data.
all_runs = rec_io.list_psd()
for run in sorted(all_runs.keys()):
	# Check if the run was already processed.
	result = db_operate("SELECT 1 from {:} where run={:}".format(
		strtable, run))
	if result:
		continue
	
	# Process the run.
	print 'Packing run {0} ...'.format(run)
	connection = None
	sqlcmd = """INSERT OR REPLACE INTO {:}(time, antenna, run, value)
		VALUES (?, ?, ?, ?)""".format(strtable)
	try:
		connection = sqlite3.connect(strdb)
		cursor = connection.cursor()
		for antenna in all_runs[run]:
			data = rec_io.load_psd_reference(run, antenna, Fref)
			for ti, pi in data:
				ti = int(ti)
				pi = int((10.*math.log10(pi)+120.)*1000)
				cursor.execute(sqlcmd, (ti, antenna, run, pi))
		connection.commit()
	finally:
		if connection is not None:
			connection.close()
	print monitor.statistics()
