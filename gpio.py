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

class MPGPIO():
	"""GPIO utilities for our RPi.
	"""

	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['gpio']['log'], level=logging.DEBUG)

	def start_gpio(self):
		if mock_gpio:
			logging.info("starting mocked gpio.")
			self.db.set('GPIO_STATUS', True)
			return 

		start_daemon(self.conf['d_files']['gpio'])

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
		logging.debug("GPIO THREAD STARTED...")

		while True:
			self.__parse_state()
			sleep(0.005)

	def terminate(self):
		logging.debug("terminating GPIO Thread...")

	def parse_state(self):
		logging.debug("parsing GPIO state...")
		pass

	def send(self, endpoint):
		url = "http://localhost:%d/%s" % (self.conf['api_port'], endpoint)
		
		try:
			r = requests.get(url)
			logging.info(r.content)
		except Exception as e:
			logging.warning("Could not perform request to %s: " % url)
			
			if PROD_MODE == "debug":
				print e, type(e)

class IRRecieverThread(GPIOThread):
	def __init__(self):
		GPIOThread.__init__(self)
		from interact.VCNL4010 import VCNL4010

		self.gpio = VCNL4010()
		self.gpio.continuous_conversion_on()

	def parse_state(self):
		super(RecieverThread, self).parse_state()
		
		logging.debug("proximity is %d" % self.gpio.read_proximity())
		logging.debug("ambient light is %d" % self.gpio.read_ambient())

		# and decide whether to pickup or hang up based on this...
		# might need to set values in config to declare threshold per sculpture

	def __on_hang_up(self):
		super(RecieverThread, self).send("hang_up")

	def __on_pick_up(self):
		super(RecieverThread, self).send("pick_up")

class ButtonThread(GPIOThread):
	def __init__(self, pin):
		GPIOThread.__init__(self)
		from interact.MomentarySwitch import MomentarySwitch

		self.gpio = MomentarySwitch(pin, True, self.parse_state)

	def parse_state(self, gpio, level, tick):
		super(ButtonThread, self).parse_state()

		logging.debug("Simple button pressed! (level: %s, tick: %s)" % (str(level), str(tick)))
		self.__on_button_press()

	def terminate(self):
		self.gpio.pig.stop()
		super(ButtonThread, self).terminate()

	def __on_button_press(self):
		super(ButtonThread, self).send("mapping/%d" % self.gpio.pin)

class MatrixKeypadThread(GPIOThread):
	def __init__(self, columm_pins, row_pins):
		GPIOThread.__init__(self)
		from interact.MatrixKeypad import MatrixKeypad

		self.gpio = MatrixKeypad(columm_pins, row_pins)
		
	def parse_state(self):
		super(MatrixKeypadThread, self).parse_state()

		key_pressed = self.gpio.getKey()
		if key_pressed is None:
			return 

		logging.debug("MatrixKeypad key pressed: %d" % key_pressed)
		self.__on_key_press(key_pressed)

	def terminate(self):
		self.gpio.pig.stop()
		super(MatrixKeypadThread, self).terminate()

	def __on_key_press(self, key):
		super(MatrixKeypadThread, self).send("mapping/%d" % key)


