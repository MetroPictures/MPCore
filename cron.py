from time import ctime
import os, re

def clear_logs():
	for r, _, files in os.walk(os.path.join(os.getcwd(), ".monitor")):
		for log in [f for f in files if re.match(r'.*\.log\.txt', f)]:
			with open(os.path.join(r, log), 'wb+') as L:
				print r, log
				L.truncate()
				L.write("Log last truncated at %s" % ctime())

		break

if __name__ == "__main__":
	clear_logs()