import os
from ftplib import FTP
from subprocess import Popen, PIPE

from MPy.utils import get_config
from MPy.vars import BASE_DIR, UNPLAYABLE_FILES

redis_port, media_manifest, cdn = get_config(['redis_port', 'media_manifest', 'cdn'])

# download media from "cdn"
if media_manifest is None:
	media_manifest = ["prompts"]
else:
	media_manifest.append("prompts")

ftp = FTP()
ftp.connect(cdn['addr'], cdn['port'])
ftp.login(cdn['user'])
ftp.cwd(cdn['home_dir'])

for mm in media_manifest:
	out_dir = os.path.join(BASE_DIR, "media", mm)
	
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
		print "initialized empty directory \"%s\"" % mm

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

# make .monitor dir
try:
	os.mkdir(os.path.join(BASE_DIR, ".monitor"))
except Exception as e:
	pass

# run setup scripts
run = Popen(['core/setup.sh', BASE_DIR, str(redis_port)])
run.communicate()

