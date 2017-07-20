#!/usr/bin/env python
import numpy as np
import pylab as pl
import rec_io

run = 3341
antenna = 127
data = rec_io.load_psd(run, antenna)
T, F, P = data["time"], data['frequency'], data['power']

pl.figure()
pl.pcolor((T-T[0])/(60.*60.), F*1E-06, 10.*np.log10(P), vmin=-130., vmax=-90.)
pl.grid(True)
pl.colorbar()

pl.figure()
for i in xrange(P.shape[1]):
	pl.plot(F, 10.*np.log10(P[:,i]), "k-")
pl.grid(True)
pl.show()
