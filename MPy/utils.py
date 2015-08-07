import os, sys, signal, json
from subprocess import Popen, PIPE
from vars import BASE_DIR

def get_config(keys):
	if type(keys) in [str, unicode]:
		keys = [keys]

	if type(keys) is not list:
		return None

	try:
		with open(os.path.join(BASE_DIR, "config.json")) as C:
			config = json.loads(C.read())
			res = [config[key] if key in config.keys() else None for key in keys]
			
			if len(res) == 1:
				return res[0]

			return res

	except Exception as e:
		print e, type(e)

	return None

def start_daemon(d_files):
	print "starting daemon"
	
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError, e:
		print e.errno
		sys.exit(1)
		
	os.chdir("/")
	os.setsid()
	os.umask(0)
	
	try:
		pid = os.fork()
		if pid > 0:
			f = open(d_files['pid'], 'w')
			f.write(str(pid))
			f.close()
			
			sys.exit(0)
	except OSError, e:
		print e.errno
		sys.exit(1)
	
	si = file('/dev/null', 'r')
	so = file(d_files['log'], 'a+')
	se = file(d_files['log'], 'a+', 0)
	os.dup2(si.fileno(), sys.stdin.fileno())
	os.dup2(so.fileno(), sys.stdout.fileno())
	os.dup2(se.fileno(), sys.stderr.fileno())

	print ">>> PROCESS DAEMONIZED"

def stop_daemon(d_files):
	print "stopping daemon"

	pid = False
	try:
		f = open(d_files['pid'], 'r')
		try:
			pid = int(f.read().strip())
		except ValueError as e:
			if DEBUG:
				print "NO PID AT %s" % d_files['pid']
	except IOError as e:
		print "NO PID AT %s" % d_files['pid']
	
	if pid:
		print "STOPPING DAEMON on pid %d" % pid
	
		try:
			os.kill(pid, signal.SIGTERM)
			
			if 'ports' in d_files.keys() and d_files['ports'] is not None:
				print "ALSO STOPPING WHATEVER IS ON PORT %s" % d_files['ports']

				pids = Popen(['lsof', '-t', '-i:%d' % d_files['ports']], stdout=PIPE)
				pid = pids.stdout.read().strip()
				pids.stdout.close()
				
				for p in pid.split("\n"):
					cmd = ['kill', str(p)]
					Popen(cmd)
			
			return True
		except OSError as e:
			print "could not kill process at PID %d" % pid

	return False