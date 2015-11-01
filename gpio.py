import os, requests, logging
from time import sleep

from utils import get_config, str_to_bool
from vars import BASE_DIR

mock_gpio = False

try:
	mock_gpio = get_config('mock_gpio')
except KeyError as e:
	pass

if not mock_gpio:
	import pigpio, threading
	from multiprocessing import Process
	from utils import start_daemon, stop_daemon

	pig = pigpio.pi()

class MPGPIO():
	"""GPIO utilities for our RPi.
	"""

	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['gpio']['log'], level=logging.DEBUG)

	def start_gpio(self):
		if mock_gpio:
			return self.__on_gpio_status_changed(True, mocked_gpio=True)

		gpio_mappings = get_config('gpio_mappings')
		receiver = buttons = []

		if 'receiver' in gpio_mappings.keys():
			receiver = globals()[gpio_mappings['receiver']['type']](pin=None if 'pin' not in gpio_mappings['receiver'].keys() else \
				gpio_mappings['receiver']['pin'])
		
		if 'buttons' in gpio_mappings.keys():
			buttons = [globals()[gpio_mappings['buttons']['type']](pin) \
				for pin in gpio_mappings['buttons']['pins']]

		for m, mapping in enumerate([receiver] + buttons):
			d_files = {'log' : self.conf['d_files']['gpio']['log'], \
				'pid' : os.path.join(BASE_DIR, ".monitor", "gpio_%d.pid.txt" % m)}
			
			p = Process(target=mapping.run, args=(self.conf['api_port'], d_files,))
			p.start()

		return self.__on_gpio_status_changed(True)

	def stop_gpio(self):
		if mock_gpio:
			return self.__on_gpio_status_changed(False, mocked_gpio=True)

		gpio_mappings = get_config('gpio_mappings')

		pins = 0
		if 'buttons' in gpio_mappings.keys():
			pins += len(gpio_mappings['buttons']['pins'])
		
		for m in xrange((1 if 'receiver' in gpio_mappings.keys() else 0) + pins):
			d_files = {'log' : self.conf['d_files']['gpio']['log'], \
				'pid' : os.path.join(BASE_DIR, ".monitor", "gpio_%d.pid.txt" % m)}

			stop_daemon(d_files)

		return self.__on_gpio_status_changed(False)

	def get_gpio_status(self):
		# maybe this will be something more substantial...
		return str_to_bool(self.db.get('GPIO_STATUS'))

	def __on_gpio_status_changed(self, status, mocked_gpio=False):
		logging.info("GPIO STATUS: %s (mocked: %s)" % (status, mocked_gpio))
		self.db.set('GPIO_STATUS', True)

		return True

class GPIOThread():
	def __init__(self):
		pass
		
	def run(self, api_port, d_files):
		self.global_endpoint = "http://localhost:%d" % api_port
		
		start_daemon(d_files)
		logging.debug("GPIO THREAD STARTED...")

		while True:
			self.parse_state()
			sleep(0.005)

	def parse_state(self):
		pass

	def send(self, endpoint):
		url = "%s/%s" % (self.global_endpoint, endpoint)
		
		try:
			r = requests.get(url)
			logging.info(r.content)
		except Exception as e:
			logging.warning("Could not perform request to %s: " % url)
			print e, type(e)

class ReceiverThread(GPIOThread):
	def __init__(self):
		GPIOThread.__init__(self)

	def on_hang_up(self):
		super(ReceiverThread, self).send("hang_up")

	def on_pick_up(self):
		super(ReceiverThread, self).send("pick_up")

class IRReceiverThread(ReceiverThread):
	def __init__(self, pin=None):
		ReceiverThread.__init__(self)
		from interact.VCNL4010 import VCNL4010

		self.gpio = VCNL4010()
		self.gpio.continuous_conversion_on()

		logging.debug("IRReceiverThread online.")

	def parse_state(self):
		super(ReceiverThread, self).parse_state()

		# TODO: needs debounce.
		
		#logging.debug("proximity is %d" % self.gpio.read_proximity())
		#logging.debug("ambient light is %d" % self.gpio.read_ambient())

		# and decide whether to pickup or hang up based on this...
		# might need to set values in config to declare threshold per sculpture

class HallEffectReceiverThread(ReceiverThread):
	def __init__(self, pin):
		global pig
		from interact.HallEffect import HallEffect

		ReceiverThread.__init__(self)
		self.gpio = HallEffect(pig, pin, callback=self.on_pick_up, release_callback=self.on_hang_up)
		logging.debug("HallEffectReceiverThread online.")

	def on_pick_up(self, gpio, level, tick):
		logging.debug("Hall Effect Pickup: (level: %s, tick: %s)" % (str(level), str(tick)))
		super(ReceiverThread, self).on_pick_up()

	def on_hang_up(self, gpio, level, tick):
		logging.debug("Hall Effect Hangup: (level: %s, tick: %s)" % (str(level), str(tick)))
		super(ReceiverThread, self).on_hang_up()

class ButtonThread(GPIOThread):
	def __init__(self, pin):
		global pig
		from interact.Button import Button

		GPIOThread.__init__(self)
		self.gpio = Button(pig, pin, callback=self.on_button_press)
		logging.debug("ButtonThread %d online." % pin)

	def on_button_press(self, gpio, level, tick):
		logging.debug("Simple button pressed! (level: %s, tick: %s)" % (str(level), str(tick)))
		super(ButtonThread, self).send("mapping/%d" % self.gpio.pin)

class TrellisKeypadThread(GPIOThread):
	def __init__(self, pin):
		GPIOThread.__init__(self)
		from interact.TrellisKeypad import Adafruit_Trellis, Adafruit_TrellisSet

		ADDR = 0x70
		I2C_BUS = 1

		matrix = Adafruit_Trellis()
		self.gpio = Adafruit_TrellisSet(matrix)
		
		self.pad_mapping = {
			0:0, 1:1, 2:2, 4:3, \
			5:4, 6:5, 8:6, 9:7, \
			10:8, 12:9, 13:10, 14:11
		}

		self.gpio.begin((ADDR, I2C_BUS))

	def parse_state(self):
		super(TrellisKeypadThread, self).parse_state()

	def on_key_press(self, key):
		super(TrellisKeypadThread, self).send("mapping/%d" % self.pad_mapping[key])

class MatrixKeypadThread(GPIOThread):
	def __init__(self, pins):
		global pig
		from interact.MatrixKeypad import MatrixKeypad

		GPIOThread.__init__(self)
		self.gpio = MatrixKeypad(pins[0], pins[1])
		
	def parse_state(self):
		super(MatrixKeypadThread, self).parse_state()

		key_pressed = self.gpio.getKey()
		if key_pressed is None:
			return 

		logging.debug("MatrixKeypad key pressed: %d" % key_pressed)
		self.on_key_press(key_pressed)

	def on_key_press(self, key):
		super(MatrixKeypadThread, self).send("mapping/%d" % key)


