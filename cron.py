import os, re

def clear_logs():
	for _, _, files in os.walk(os.path.join(os.getcwd(), ".monitor")):
		for log in [f for f in files if re.match(r'.*\.log\.txt', f)]:
			with open(os.path.join(monitor_dir, log), 'rw+') as L:
				L.truncate()

		break

if __name__ == "__main__":
	clear_logs()