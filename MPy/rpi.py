import os, requests, logging
#from RPi import GPIO

from utils import start_daemon, stop_daemon, get_config
from vars import PROD_MODE, BASE_DIR

class MPRPi(object):
	"""GPIO utilities for our RPi.
	"""

	def __init__(self):
		print("init MPSAPI")

		self.conf['receiver_pin'] = get_config('receiver_pin')
		logging.basicConfig(filename=self.conf['d_files']['gpio']['log'], level=logging.DEBUG)

	def start_RPi(self):
		'''
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		'''

		if self.gpio_mappings is None:
			self.gpio_mappings = []

		# default mappings for receiver (pick-up/hang-up)
		self.gpio_mappings.append((self.conf['receiver_pin'], "GPIO.IN", "GPIO.PUD_DOWN"))

		for mapping in self.gpio_mappings:
			if mapping[0] != self.conf['receiver_pin']:
				#GPIO.add_event_detect(mapping[0], GPIO.FALLING, self.__on_button_press, 100)
				logging.debug("adding hypothetical mapping %d" % mapping[0])
			else:
				# custom mapping for receiver pin...
				logging.debug("receiver pin set here...")

		start_daemon(self.conf['d_files']['gpio'])
		logging.info("GPIO listening...")

		while True:
			pass

	def stop_RPi(self):
		stop_daemon(self.conf['d_files']['gpio'])

	def __on_button_press(self, pin):
		self.__send("mapping/%d" % pin)

	def __on_hang_up(self, pin):
		self.__send("hang_up")

	def __on_pick_up(self, pin):
		self.__send("pick_up")

	def __send(self, endpoint):
		url = "http://localhost:%d/%s" % (self.conf['api_port'], endpoint)
		
		try:
			r = requests.get(url)
		except Exception as e:
			logging.warning("Could not perform request to %s: " % url)
			if PROD_MODE == "debug":
				print e, type(e)

