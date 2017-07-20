#!/usr/bin/env python
import subprocess as sp
import os
import time

antennas = range(101, 139)+[140,]+range(148, 159)

for antenna in antennas:
	if os.path.exists("data/gain/gain.{:}.p".format(antenna)):
		continue
	print "o) Processing antenna {:}".format(antenna)
	t0 = time.time()
	cmd = "./scripts/compute-gain.py {:}".format(antenna)
	p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
	stdout, stderr = p.communicate()
	if stderr:
		raise RuntimeError(stderr)
	if stdout:
		print stdout
	dt = time.time()-t0
	print "  --> Done in {:.0f} s".format(dt)
