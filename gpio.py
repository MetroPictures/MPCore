import os, requests, logging, pigpio
from threading import Thread
from time import sleep

from utils import start_daemon, stop_daemon, get_config, str_to_bool
from vars import PROD_MODE, BASE_DIR

class MPGPIO(object):
	"""GPIO utilities for our RPi.
	"""

	def __init__(self):
		print("init MPSAPI")
		logging.basicConfig(filename=self.conf['d_files']['gpio']['log'], level=logging.DEBUG)

	def start_gpio(self):
		self.gpio = pigpio.pi()
		self.db.set('GPIO_STATUS', False)
		
		start_daemon(self.conf['d_files']['gpio'])

		if self.gpio_mappings is None:
			self.gpio_mappings = []
		else:
			self.gpio_mappings = [(pin, ButtonThread(self.gpio, pin)) for pin in self.gpio_mappings]

		# default mappings for receiver (pick-up/hang-up)
		receiver_pin = get_config('receiver_pin')
		self.gpio_mappings.append((receiver_pin, RecieverThread(self.gpio, receiver_pin)))

		for mapping in self.gpio_mappings:
			sleep(1)

			if mapping[0] != receiver_pin:
				logging.debug("setting pin %d mapping" % mapping[0])
				self.gpio.set_mode(mapping[0], pigpio.INPUT)
			else:
				# custom mapping for receiver pin...
				logging.debug("receiver pin set here...")

			mapping[1].start()

		logging.info("GPIO listening...")
		self.db.set('GPIO_STATUS', True)

	def stop_gpio(self):
		try:
			self.gpio.stop()
		except Exception as e:
			pass

		stop_daemon(self.conf['d_files']['gpio'])
		self.db.set('GPIO_STATUS', False)
		
		logging.info("GPIO Stopped")

	def get_gpio_status(self):
		# maybe this will be something more substantial...
		return str_to_bool(self.db.get('GPIO_STATUS'))

class GPIOThread(Thread):
	def __init__(self, gpio, pin):
		Thread.__init__(self)

		self.gpio = gpio
		self.pin = pin

	def run(self):
		while True:
			self.__parse_state(self.gpio.read(self.pin))
			sleep(0.01)

	def __parse_state(self, state):
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
	def __init__(self, gpio, pin):
		GPIOThread.__init__(self, gpio, pin)

	def __parse_state(self, state):
		super(RecieverThread, self).__parse_state(state)
		# decide if it's pick up or hang up

	def __on_hang_up(self):
		super(RecieverThread, self).__send("hang_up")

	def __on_pick_up(self, pin):
		super(RecieverThread, self).__send("pick_up")

class ButtonThread(GPIOThread):
	def __init__(self, gpio, pin):
		GPIOThread.__init__(self, gpio, pin)

	def __parse_state(self, state):
		super(ButtonThread, self).__parse_state(state)
		# do logics?

	def __on_button_press(self):
		super(ButtonThread, self).__send("mapping/%d" % self.pin)


