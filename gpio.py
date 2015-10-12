import os, requests, logging
from threading import Thread
from time import sleep

from utils import start_daemon, stop_daemon, get_config, str_to_bool
from vars import PROD_MODE, BASE_DIR

mock_gpio = False

try:
	mock_gpio = get_config('mock_gpio')
except KeyError as e:
	pass	

class MPGPIO(object):
	"""GPIO utilities for our RPi.
	"""

	def __init__(self):
		print("init MPSAPI")
		logging.basicConfig(filename=self.conf['d_files']['gpio']['log'], level=logging.DEBUG)

	def start_gpio(self):
		if mock_gpio:
			logging.info("starting mocked gpio.")
			self.db.set('GPIO_STATUS', True)
			return 

		start_daemon(self.conf['d_files']['gpio'])

		if self.gpio_mappings is None:
			self.gpio_mappings = []
		else:
			self.gpio_mappings = [ButtonThread(pin) for pin in self.gpio_mappings]
		
		# default mappings for receiver (pick-up/hang-up)
		self.gpio_mappings.append(RecieverThread())

		for mapping in self.gpio_mappings:
			mapping.start()

		logging.info("GPIO listening...")
		self.db.set('GPIO_STATUS', True)

	def stop_gpio(self):
		if mock_gpio:
			logging.info("stopping mocked gpio.")
			self.db.set('GPIO_STATUS', False)
			return 

		stop_daemon(self.conf['d_files']['gpio'])
		self.db.set('GPIO_STATUS', False)
		
		logging.info("GPIO Stopped")

	def get_gpio_status(self):
		# maybe this will be something more substantial...
		return str_to_bool(self.db.get('GPIO_STATUS'))

class GPIOThread(Thread):
	def __init__(self):
		Thread.__init__(self)

	def run(self):
		while True:
			self.__parse_state()
			sleep(0.5)

	def __parse_state(self):
		pass

	def __send(self, endpoint):
		url = "http://localhost:%d/%s" % (self.conf['api_port'], endpoint)
		
		try:
			r = requests.get(url)
			logging.info(r.content)
		except Exception as e:
			logging.warning("Could not perform request to %s: " % url)
			
			if PROD_MODE == "debug":
				print e, type(e)

class RecieverThread(GPIOThread):
	def __init__(self):
		GPIOThread.__init__(self)
		from adafruit.VCNL4010 import VCNL4010

		self.gpio = VCNL4010()
		self.gpio.continuous_conversion_on()

	def __parse_state(self):
		super(RecieverThread, self).__parse_state()
		
		print "prox is ", self.gpio.read_proximity()
		print "ambient light is ", self.gpio.read_ambient()

		# and decide whether to pickup or hang up based on this...
		# might need to set values in config to declare threshold per sculpture

	def __on_hang_up(self):
		super(RecieverThread, self).__send("hang_up")

	def __on_pick_up(self):
		super(RecieverThread, self).__send("pick_up")

class ButtonThread(GPIOThread):
	def __init__(self, pin):
		self.pin = pin
		GPIOThread.__init__(self)

	def __parse_state(self):
		super(ButtonThread, self).__parse_state()
		# do logics?

	def __on_button_press(self):
		super(ButtonThread, self).__send("mapping/%d" % self.pin)


