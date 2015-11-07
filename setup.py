import os
from sys import argv, exit
from ftplib import FTP
from subprocess import Popen, PIPE

from utils import get_config
from vars import BASE_DIR, UNPLAYABLE_FILES

def update_cdn():
	use_cdn = get_config("use_cdn")
	if use_cdn is not None and use_cdn is False:
		print "Not pulling from cdn!"
		return

	media_manifest, cdn = get_config(['media_manifest', 'cdn'])
	# download media from "cdn"
	if media_manifest is None or len(media_manifest) == 0:
		media_manifest = ["prompts"]
	else:
		media_manifest.append("prompts")

	ftp = FTP()
	ftp.connect(cdn['addr'], cdn['port'])
	ftp.login(cdn['user'])
	ftp.cwd(cdn['home_dir'])

	for mm in media_manifest:
		out_dir = os.path.join(BASE_DIR, "media", mm)
		
		if mm == "video":
			out_dir = os.path.join(out_dir, "viz")
		
		if not os.path.exists(out_dir):
			os.makedirs(out_dir)
			print "initialized empty directory \"%s\" at %s" % (mm, out_dir)

		try:
			ftp.cwd(mm)
		except Exception as e:
			print "directory \"%s\" doesn't exist in CDN" % mm		
			continue

		dir_list = []
		ftp.dir(dir_list.append)
		dir_list = [d for d in dir_list if d not in [UNPLAYABLE_FILES]]

		for l in [l.split(" ")[-1] for l in dir_list]:
			out_file = os.path.join(out_dir, l)

			try:
				with open(out_file, 'wb+') as O:
					ftp.retrbinary("RETR %s" % l, O.write)
			except Exception as e:
				print "could not download %s to %s" % (l, out_file)
				print e, type(e)

				continue

		ftp.cwd('..')

	ftp.quit()

def install(with_cdn=True):
	# run setup scripts
	redis_port, api_port, mock_gpio = get_config(['redis_port', 'api_port', 'mock_gpio'])
	if 8888 in [redis_port, api_port]:
		print "HEY, WAIT!  Port 8888 is reserved for another purpose (the GPIO).\nEdit your config and run setup.py again."
		return

	if with_cdn:
		update_cdn()

	# make .monitor dir
	try:
		os.mkdir(os.path.join(BASE_DIR, ".monitor"))
	except Exception as e:
		pass

	# setup auto-start
	info = get_config('info')
	if info is not None:
		with open(os.path.join(os.path.expanduser('~'), ".mp_autostart"), 'wb+') as A:
			A.write("cd %s && python %s.py --start" % (info['dir'], info['module']))

	# modify redis config
	redis_conf = []
	redis_repl = [
		("daemonize no", "no", "yes"),
		("pidfile /var/run/redis.pid", "redis", "redis_%d" % redis_port),
		("port 6379", "6379", str(redis_port)),
		("logfile \"\"", "\"\"", "/var/log/redis_%d.log" % redis_port),
		("dir ./", "./", "/var/redis/%d" % redis_port)
	]

	with open(os.path.join(os.path.expanduser('~'), "redis-stable", "redis.conf"), 'rb') as R:
		for line in R.read().splitlines():
			for rr in redis_repl:
				if line == rr[0]:
					line = line.replace(rr[1], rr[2])

			redis_conf.append(line)

	with open(os.path.join(BASE_DIR, "%d.conf" % redis_port), 'wb+') as R:
		R.write("\n".join(redis_conf))

	Popen(['sudo', 'mv', os.path.join(BASE_DIR, "%d.conf" % redis_port), \
		os.path.join("/", "etc", "redis", "%d.conf" % redis_port)])

	print "OK!  Don't forget to test your soundcard, and then reboot!"

if __name__ == "__main__":
	if len(argv) == 1:
		install()
		
	elif len(argv) == 2:
		if argv[1] == "update":
			update_cdn()

		if argv[1] == "no-update":
			install(with_cdn=False)
