import scipy.io as spio

def load_mat(filename):
    """This function should be called instead of direct spio.loadmat
    as it cures the problem of not properly recovering python dictionaries
    from mat files. It calls the function check keys to cure all entries
    which are still mat-objects.
    """
    data = spio.loadmat(filename, struct_as_record=False, squeeze_me=True)
    return _check_keys(data)

def _check_keys(dict):
    """Checks if entries in dictionary are mat-objects. If yes
    todict is called to change them to nested dictionaries.
    """
    for key in dict:
        if isinstance(dict[key], spio.matlab.mio5_params.mat_struct):
            dict[key] = _to_dict(dict[key])
    return dict        

def _to_dict(matobj):
    """ A recursive function which constructs from matobjects nested dictionaries.
    """
    dict = {}
    for strg in matobj._fieldnames:
        elem = matobj.__dict__[strg]
        if isinstance(elem, spio.matlab.mio5_params.mat_struct):
            dict[strg] = _to_dict(elem)
        else:
            dict[strg] = elem
    return dict

import os
_dst_path = '/sps/hep/trend'
_dst_tags = ('dst102012', 'dst122013')

def list_dst():
    """List valid dst on storage.
    """
    d = {}
    for tag in _dst_tags:
        dst = [map(int, v.split('.')[0][3:].split('_')) for v in os.listdir(os.path.join(_dst_path, tag)) if v.endswith('mat') and not ('_light' in v)]
        for run, index in dst:
	    try:
	        if d[run][1] < index:
		    d[run][1] = index
	    except KeyError:
	        d[run] = [tag, index]     
    return d

def load_dst(run, tag, index, light=False):
    """Load full data from a dst. If 'light' is True a light version is loaded if available.
    """
    path = os.path.join(_dst_path, tag, 'dst{0}_{1}_light.mat'.format(run, index))
    if not os.path.exists(path):
        path = os.path.join(_dst_path, tag, 'dst{0}_{1}.mat'.format(run, index))
    return load_mat(path)['Struct']

def load_dst_summary(run, tag, index=1):
    """Load a summary from a dst.
    """
    setup = load_dst(run, tag, index, light=True)['Setup']
    antennas = {}
    det = setup['Det']
    if isinstance(det, dict):
        detiter = (det,)
    else:
        detiter = (d.__dict__ for d in det)
    for d in detiter:
        antennas[int(d['Name'])] = (map(float, (d['X'], d['Y'], d['Z'], d['Delay'])), int(d['Evt']))
    try:
        start = int(setup['RunTimeStart'][0])
	stop  = int (setup['RunTimeStop'][-1])
    except IndexError:
        start = stop = None
    return {
        'antennas' : antennas, 
	'start'    : start, 
	'stop'     : stop
    }

import array, sys, numpy as np
_psd_path = '/sps/hep/trend/psd'

def list_psd():
    """List psd data on storage.
    """
    d = {}
    runs = [int(v[1:]) for v in os.listdir(_psd_path) if (v[0] == 'R')]
    for run in runs:
        runtag = 'R{0:06d}'.format(run)
        files = [v for v in os.listdir(os.path.join(_psd_path, runtag)) if  v.endswith('.bin') and not ('_.' in v) and v.startswith(runtag)]
        if not files:
	    continue
	antennas = {}
	for f in files:
	    index = int(f[9:13])
	    try:
	        antennas[index] += 1
	    except KeyError:
	        antennas[index] = 1
	for key in antennas.keys():
	    if antennas[key] == 1:
	        del antennas[key]
	antennas = sorted(antennas.keys())
	if antennas:
	    d[run] = antennas
    return d

_PSD_NFFT = 256
_PSD_NPAR = 2
_PSD_FSAMPLING = 200.e6 # Hz
_PSD_SCALE = 3.3/2**8 

def load_psd(run, antenna):
    """Load full data from a psd file.
    """
    N = _PSD_NFFT+_PSD_NPAR
    path = os.path.join(_psd_path, 'R{0:06d}'.format(run))

    # Read data file.
    strfile = os.path.join(path, 'R{0:06d}_A{1:04d}_PSD_data.bin'.format(run, antenna))
    data = []
    with open(strfile, 'rb') as f:
	while True:
	    try:
	        a = array.array('f')
                a.fromfile(f, N)
		data.append(a)
            except EOFError:
                break	  
    data = np.array(data).T
    df = 0.5*_PSD_FSAMPLING/_PSD_NFFT;
    F  = np.arange(1, _PSD_NFFT+1)*df
    P  = data[:_PSD_NFFT,:]*_PSD_SCALE**2/df
    mu = data[_PSD_NFFT,:]
    sigma = data[_PSD_NFFT+1,:]

    # Read time file.
    strfile = os.path.join(path, 'R{0:06d}_A{1:04d}_PSD_time.bin'.format(run, antenna))
    data = []
    with open(strfile, 'rb') as f:
	while True:
	    try:
	        a = array.array('i')
                a.fromfile(f, 4)
		data.append(a)
            except EOFError:
                break	  
    data = np.array(data).T

    T = data[0,:]
    flag = data[2,:] - data[1,:]
  
    # Clean data.
    nmin = min(P.shape[1], len(T))
    P = P[:,:nmin]
    T = T[:nmin]
    flag = flag[:nmin]
    mu = mu[:nmin]
    sigma = sigma[:nmin]

    return {
        'power' : P,
	'frequency' : F,
	'time': T,
	'flag' : flag,
	'mean' : mu,
	'standard': sigma
    }

def load_psd_summary(run, antenna):
    """Load a summary from a psd file.
    """
    data = load_psd(run, antenna)
    F, P = data['frequency'], data['power']
    K = (F >= 55.e6) & (F <= 95.e6)
    return {
        'start' : data['time'][0],
	'stop' : data['time'][-1],
	'flag' : any(data['flag']),
	'mean' : np.mean(data['mean']),
	'standard' : np.mean(data['standard']),
	'entries' : len(data['time']),     
        'bandwidth_level' : np.mean(np.sqrt(np.trapz(P[K,:], F[K], axis=0)))
    }

def load_psd_reference(run, antenna, Fref):
    """Load the PSD reference values.
    """
    data = load_psd(run, antenna)
    F, P = data['frequency'], data['power']
    kref = np.argmin(np.absolute(F-Fref))
    K = (data['flag'] == False) & (P[kref,:] > 0.)
    return zip(data['time'][K], P[kref,K])
