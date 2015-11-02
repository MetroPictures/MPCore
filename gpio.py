import os, logging, json
from time import sleep
from signal import SIGINT

from utils import get_config, str_to_bool
from vars import BASE_DIR

mock_gpio = False

try:
	mock_gpio = get_config('mock_gpio')
except KeyError as e:
	pass

if not mock_gpio:
	from subprocess import Popen

class MPGPIO():
	"""GPIO utilities for our RPi.
	"""

	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['gpio']['log'], level=logging.DEBUG)

	def start_gpio(self):
		if mock_gpio:
			return self.__on_gpio_status_changed(True, mocked_gpio=True)

		gpio_mappings = get_config('gpio_mappings')
		
		# signal start
		cmd = [
			"python", 
			os.path.join(BASE_DIR, "core", "interact", "pigpio_builder.py"),
			json.dumps(gpio_mappings), 
			str(self.conf['api_port'])
		]

		with open(self.conf['d_files']['gpio']['log'], 'a') as gpio_log:
			gpio_process = Popen(cmd, shell=False, \
				stdout=gpio_log, stderr=gpio_log, stdin=gpio_log)

		logging.info("GPIO PROGRAM STARTED AT PID %d" % gpio_process.pid)
		
		# write pid to d_file
		with open(self.conf['d_files']['gpio']['pid'], 'wb+') as PID:
			PID.write(str(gpio_process.pid))
		
		return self.__on_gpio_status_changed(True)

	def stop_gpio(self):
		if mock_gpio:
			return self.__on_gpio_status_changed(False, mocked_gpio=True)

		try:
			# get pid from d_file
			with open(self.conf['d_files']['gpio']['pid'], 'rb') as PID:
				# signal stop
				os.kill(int(PID.read().strip()), SIGINT)
		except Exception as e:
			logging.error("no pid for gpio process probably")
			print e, type(e)

		return self.__on_gpio_status_changed(False)

	def get_gpio_status(self):
		# maybe this will be something more substantial...
		return str_to_bool(self.db.get('GPIO_STATUS'))

	def __on_gpio_status_changed(self, status, mocked_gpio=False):
		logging.info("GPIO STATUS: %s (mocked: %s)" % (status, mocked_gpio))
		self.db.set('GPIO_STATUS', True)

		return True

