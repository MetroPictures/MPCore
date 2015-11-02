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
		cmd = [
			"python",
			os.path.join(BASE_DIR, "core", "interact", "pigpio_builder.py"),
			json.dumps(gpio_mappings),
			str(self.conf['api_port'])
		]
		
		# signal start
		from subprocess import Popen

		DEV_NULL = open(os.devnull, 'w')
		gpio_process = Popen(cmd, shell=False, stdout=DEV_NULL, stderr=DEV_NULL)

		with open(self.conf['d_files']['gpio']['pid'], 'wb+') as gpio_pid:			
			gpio_pid.write(str(gpio_process.pid))
		
		return self.__on_gpio_status_changed(True)

	def stop_gpio(self):
		if mock_gpio:
			return self.__on_gpio_status_changed(False, mocked_gpio=True)

		# signal stop

		try:
			with open(self.conf['d_files']['gpio']['pid'], 'rb') as gpio_pid:
				os.kill(int(gpio_pid.read().strip()), SIGINT)
		except Exception as e:
			logging.error("GPIO PID PROBABLY NOT HERE")
		
		return self.__on_gpio_status_changed(False)

	def get_gpio_status(self):
		# maybe this will be something more substantial...
		return str_to_bool(self.db.get('GPIO_STATUS'))

	def __on_gpio_status_changed(self, status, mocked_gpio=False):
		logging.info("GPIO STATUS: %s (mocked: %s)" % (status, mocked_gpio))
		self.db.set('GPIO_STATUS', True)

		return True

