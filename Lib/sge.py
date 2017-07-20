import os, resource, subprocess, time

#===================================================================================================
class SGEMonitor(object):
#===================================================================================================
    """
    Monitoring interface for a grid engine job.
    """
    
    #-----------------------------------------------------------------------------------------------	    
    def __init__(self):
        """.
        """
    
        import signal
	self.signal = 0
	
	def handler(signum, frame):
	    self.signal=signum
	    msg = 'Received signal {0}'.format(signum)
	    raise IOError(msg)
	
	for signum in [signal.SIGXCPU, signal.SIGUSR1, signal.SIGUSR2, signal.SIGXFSZ]:
	    signal.signal(signum, handler)
	    
	self._start_time = time.time()
  
    #-----------------------------------------------------------------------------------------------	    
    def configuration(self):
        """
	Job configuration, as a dictionary.
        """
	
        limits = dict(
    	    cpu    = resource.getrlimit(resource.RLIMIT_CPU)[0],
	    memory = resource.getrlimit(resource.RLIMIT_AS)[0],
            disk   = resource.getrlimit(resource.RLIMIT_FSIZE)[0]
        )
	
	tmpdir = os.getenv('TMPDIR')
	if tmpdir:
	    tag = os.path.basename(tmpdir)
	    jobid, taskid, queue = tag.split('.')
	else:
	    jobid = taskid = queue = None
	
	workdir = os.getenv('SGE_O_WORKDIR')
	if not workdir:
	    workdir = os.getcwd()
	
	# Get the real time limit.
	if queue is None:
	    limits['time'] = None
	else:
	    command = "qconf -sq pa_medium | grep s_rt"
	    pipe = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = pipe.communicate()
	    time = map(float, stdout.split()[1].split(':'))
	    time = (time[0]*60.+time[1])*60.+time[2]
	    limits['time'] = time    
	
	return dict(
	    host    = os.getenv('HOSTNAME'),
	    jobid   = jobid,
	    taskid  = taskid,
	    queue   = queue,
	    limits  = limits,
	    tmpdir  = tmpdir,
	    workdir = workdir 
	)

    #-----------------------------------------------------------------------------------------------	    
    def cpuinfo(self):
        """
	Parse cpu info from /proc/cpuinfo.
        """
    
        command = 'cat /proc/cpuinfo'
	pipe = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = pipe.communicate()
	info = stdout.strip()
        cpu_type = None
	n_proc   = 0
	for line in info.split('\n'):
            if 'model name' in line:
	        n_proc += 1
                if cpu_type is None:
		    cpu_type = ' '.join(line.split(':')[-1].strip().split())
	
	return (cpu_type, n_proc)
	
    #-----------------------------------------------------------------------------------------------	    
    def cpu_time(self):
        """
	Cpu time spent.
        """
    
        u_self     = resource.getrusage(resource.RUSAGE_SELF)
	u_children = resource.getrusage(resource.RUSAGE_CHILDREN)
	
        return u_self[0]+u_self[1]+u_children[0]+u_children[1]
	
    #-----------------------------------------------------------------------------------------------	    
    def elapsed_time(self):
        """
	Real time spent.
        """
	
        return time.time()-self._start_time

    #-----------------------------------------------------------------------------------------------	    
    def netstat(self):
        """
	Get info on ports usage.
        """
    
        command = 'netstat -utn'
        lines = subprocess.check_output(command, shell=True).split('\n')[2:]
        
	ports = {'tcp':[], 'udp':[]}
	for line in lines:
	    if len(line) < 4:
	        continue
		
	    words = line.split()
	    port = int(words[3].split(':')[-1])
	    lst = ports[words[0]]
	    if port in lst:
	        continue
	    lst.append(port)
	    
	ports['tcp'].sort()
	ports['udp'].sort()
	
	return ports
	
    #-----------------------------------------------------------------------------------------------	    
    def statistics(self):
        """
	Job resource used and signal status, as a dictionary.
        """
    
        u_self     = resource.getrusage(resource.RUSAGE_SELF)
	u_children = resource.getrusage(resource.RUSAGE_CHILDREN)
	
	path = os.getenv('TMPDIR')
	if not path:
	    path = os.getcwd()
	    
	disk = 0 
	for root, dirs, files in os.walk(path): 
	    for d in dirs+files:
	        disk += os.stat(os.path.join(root, d)).st_size

        return dict(
	    cpu    = u_self[0]+u_self[1]+u_children[0]+u_children[1],
	    memory = (u_self[2]+u_children[2])*resource.getpagesize(),
	    disk   = disk,
	    time   = self.elapsed_time(),
	    signal = self.signal
	)
