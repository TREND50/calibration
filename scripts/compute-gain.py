#!/usr/bin/env python
import cPickle as pk
import sqlite3
import calendar
import time
import os
import sys
import numpy as np
from scipy.interpolate import interp1d
import pylab as pl

# Time origin, in seconds UNIX.
tfirst = calendar.timegm(time.strptime("01 Jan 11 00", "%d %b %y %H"))
day = 1./(24.*60.*60.)

# Settings.
polar = 0.
RL = 112.5
RN = 0.*1.5
TE = 290.
Fref = np.linspace(55., 95., 9)*1E+06
antenna = 105
# antenna = 135

# Check the arguments.
if len(sys.argv) > 1:
    antenna = int(sys.argv[1])
    do_plot = False
else:
    do_plot = True

# Get the run start times.
with open("data/gain/run-times.py", "rb") as f:
    run_times = pk.load(f)

# Get the antenna data.
def db_request(antenna, frequency):
    connection = result = None
    frequency /= 1E+06
    strtable = "power{:.0f}".format(frequency)
    sqlcmd = """SELECT time, value, run from power{:.0f} where antenna={:}
        and run NOT IN (2667, 3129, 3793, 4441, 3759)
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

power = []
runs = None
for fi in Fref:
    data = np.array(db_request(antenna, fi))
    if runs is None:
        tu = data[:,0].astype(np.float64)
        runs = data[:,2]
    power.append(data[:,1]*1E-03-120.)

# Filter corrupted frequencies.
n = [len(line) for line in power]
n0 = int(np.median(n))
P, F = [], []
for i, ni in enumerate(n):
    if ni != n0:
        continue
    P.append(power[i])
    F.append(Fref[i])
power, Fref = P, F
power = np.array(power)

 # Correct for the FFT window, negative frequencies and the approx. ADC/V.
power += 10.*np.log10(((256/3.3)**2)*2/0.375)

# Map the run periods.
runids = np.unique(runs)
run_stats = {}
for runid in runids:
    try:
        tstart = run_times[runid]
    except KeyError:
        continue
    K = np.nonzero(runs == runid)[0]
    if runid not in (2676, 3130, 3794, 4442, 3761):
        # Not a calibration run, correct the tstart.
        tu[K] += tstart-tu[K][0]
    tt = tu[K]
    if len(tt) <= 1:
        continue
    dt = int(np.mean(np.diff(tt)))
    tu[K] -= 0.5*dt
    run_stats[runid] = (tt[0]-dt, tt[-1], dt)

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

dsl = unix2sideral(tu)
hsl = np.mod(dsl*24., 24.)

# Get the model.
kB = 1.38E-23
T = 273.

with open("data/skymap/skymap.{:02.0f}.{:.0f}.p".format(polar, RL), "rb") as f:
    d = pk.load(f)
    model = []
    for fi in Fref:
        i0 = np.argmin(np.absolute(d["frequencies"]-fi*1E-06))
        y = 10*np.log10(RL*d["flux"][i0,:]+4.*RN*kB*T+0.5*kB*TE*RL)
        f = interp1d(d["lst"], y)
        model.append(f(hsl))
model = np.array(model)

# Compute the Gain.
gain = power-model
mu = np.mean(gain, axis=0)
sigma = np.std(gain, axis=0)
smax = 3.*np.mean(sigma)
for i, mui in enumerate(mu):
    gmin = np.min(gain[:,i])
    K = (np.absolute(gain[:,i]-gmin) <= smax)
    G = gain[K,i]
    if len(G):
        mu[i] = np.mean(G)
        sigma[i] = np.std(G)
    else:
        mu[i] = None
        sigma[i] = None


# Format the gain data.
gain_data = []
runp = None
for runid in runids:
    try:
        t0, t1, dt = run_stats[runid]
    except KeyError:
        continue
    K = runs == runid
    data = (t0, t1, dt, runid, tuple(tu[K]), tuple(mu[K]))
    if gain_data:
        i = 0
        try:
            while t0 < gain_data[-1-i][0]:
                # Sort the list by time of run start.
                i += 1
        except IndexError:
            gain_data.insert(0, data)
            continue
        tlast = gain_data[-1][1]
        if (i == 0) and (t0 <= tlast):
            if t1 > tlast:
                # Prune the run data from duplicated values.
                for j, tj in enumerate(data[4]):
                    if tj-0.5*dt > tlast:
                        break
                else:
                    continue
                if j >= len(data[4])-2:
                    continue
                data = (tj-0.5*dt, t1, dt, runid,
                    data[4][j:], data[5][j:])
            else:
                # This is a subset of the last one.
                continue
        else:
            tfirst = gain_data[-1-i][0]
            tlast = gain_data[-1-i][1]
            if (t0 == tfirst) and (t1 == tlast):
                # Duplicated run?
                continue

        if i == 0:
            gain_data.append(data)
        else:
            gain_data.insert(-1-i+1, data)
    else:
        gain_data.append(data)

# Dump the result.
with open("data/gain/gain.{:}.p".format(antenna), "wb+") as f:
    pk.dump(gain_data, f, -1)

# Cross_check the data.
t0 = 0
for i, data in enumerate(gain_data):
    t1, tt, _, runid, _, _ = data
    if t1 <= t0:
        runp = gain_data[i-1][3]
        print "  . ", runid, runp, run_stats[runid], run_stats[runp]
        if do_plot:
            pl.figure()
            K = runs == runid
            pl.plot(tu[K], mu[K], "ko")
            K = runs == runp
            pl.plot(tu[K], mu[K], "r.")
            pl.grid(True)
    t0 = tt

if do_plot is False:
    exit(0)

print "o) Checking the calibration module ..."
import trend_gain
tt = np.linspace(1.30E+09, 1.36E+09, 100000)
gg = np.zeros(tt.shape)
t0 = time.time()
for i, ti in enumerate(tt):
    gg[i] = trend_gain.get(antenna, ti)
dt = time.time()-t0
print "  --> Done in {:.0f} s".format(dt)

# Show the result.
pl.figure()
pl.plot(tu, mu, "ko")
pl.plot(tt, gg, "r.")
pl.grid(True)

pl.figure()
i0 = np.argmin(np.absolute(np.array(Fref)-75E+06))
day = 60.*60.*24.
x = (tu-tu[0])/day
K = (x >= 422.5) & (x <= 423.5)
ymean = np.mean(power[i0,K])
y1 = power[i0,K]
y2 = model[i0,K] + ymean
k0 = np.argmax(y1)
y2 += y1[k0]-y2[k0]
pl.plot(hsl[K], y1, "ko")
pl.plot(hsl[K], y2, "r.")
np.savetxt("gain-example.txt", np.array((hsl[K], y1, y2)).T)
pl.grid(True)
pl.xlabel("LST (H)", fontsize=16)
pl.ylabel("PSD (dB)", fontsize=16)
pl.savefig("gain-model.png")

pl.figure()
pl.plot(x, power[i0,:], "k.")
pl.plot(x, model[i0,:]+110., "r-")

pl.figure()
pl.plot(x[K], mu[K], "ko")
pl.grid(True)

pl.show()
