import os, logging
from time import sleep

from utils import get_config, str_to_bool
from vars import BASE_DIR

mock_gpio = False

try:
	mock_gpio = get_config('mock_gpio')
except KeyError as e:
	pass

if not mock_gpio:
	from utils import start_daemon, stop_daemon

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

		return self.__on_gpio_status_changed(True)

	def stop_gpio(self):
		if mock_gpio:
			return self.__on_gpio_status_changed(False, mocked_gpio=True)

		gpio_mappings = get_config('gpio_mappings')

		# signal stop

		return self.__on_gpio_status_changed(False)

	def get_gpio_status(self):
		# maybe this will be something more substantial...
		return str_to_bool(self.db.get('GPIO_STATUS'))

	def __on_gpio_status_changed(self, status, mocked_gpio=False):
		logging.info("GPIO STATUS: %s (mocked: %s)" % (status, mocked_gpio))
		self.db.set('GPIO_STATUS', True)

		return True

