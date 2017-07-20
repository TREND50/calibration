"""Python module providing antenna gains for the TREND-50 data takings.
"""
import cPickle as pk
import os
from scipy.interpolate import interp1d

"""Path where the gain calibration data are stored."""
DATA_PATH = "data/gain"

_data = {}

def clear(antenna=None):
	"""Clear the memory from all/a given antenna data."""
	if antenna is not None:
		try:
			del _data[antenna]
		except KeyError:
			return
	else:
		for key in _data.keys():
			del _data[key]
		_data = {}

def get(antenna, time_unix):
	"""Get the gain for a given antenna and unix time. If no
	calibration data exists `None` is returned.
	"""
	# Load the data.
	try:
		data = _data[antenna]
	except KeyError:
		with open(os.path.join(DATA_PATH, "gain.{:}.p".format(
			int(antenna))), "rb") as f:
			data = pk.load(f)
			_data[antenna] = data
	
	# Check the outer bounds.
	if (time_unix < data[0][0]) or (time_unix > data[-1][1]):
		return None

	# Search the run for the given unix time, using a dichotomy.
	def search_index(i0, i1):
		if i1-i0 <= 1:
			if time_unix < data[i1][0]:
				return i0
			else:
				return i1
		i2 = (i0+i1)/2
		t2 = data[i2][0]
		if time_unix >= t2:
			return search_index(i2, i1)
		else:
			return search_index(i0, i2)
			
	irun = search_index(0, len(data)-1)
	t0, t1, dt, run, t, g = data[irun]
	
	# Check if the unix time is within the run.
	if time_unix > t1:
		# No data for this time.
		return None
	elif time_unix <= t[0]:
		# Time corresponds to the 1st sample.
		return g[0]
	elif time_unix >= t[-1]:
		# Time corresponds to the last sample.
		return g[-1]
	
	# Interpolate the gain.
	def search_index(i0, i1):
		if i1-i0 <= 1:
			if time_unix < t[i1]:
				return i0
			else:
				return i1
		i2 = (i0+i1)/2
		t2 = t[i2]
		if time_unix >= t2:
			return search_index(i2, i1)
		else:
			return search_index(i0, i2)
	i0 = search_index(0, len(t)-1)
	t0, t1 = t[i0], t[i0+1]
	h = time_unix-t0
	if h > 1.1*dt:
		return None
	g0, g1 = g[i0], g[i0+1]
	h /= t1-t0
	return g0*(1.-h)+g1*h
