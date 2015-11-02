import os, pigpio, json, threading, requests, signal
from sys import argv, exit
from time import time, sleep

pig = pigpio.pi()
components = []

class GPIOThread(object):
	def __init__(self):
		
		global api_port
		self.global_endpoint = "http://localhost:%d" % api_port
		self.time_stamp = time()

	def start(self):
		if hasattr(self, "state_parser"):
			self.state_parser = self.StateParser(self.state_parser)
			self.state_parser.daemon = True
			self.state_parser.start()

	class StateParser(threading.Thread):
		def __init__(self, state_parser):
			self.parse_state = state_parser
			threading.Thread.__init__(self)

		def run(self):
			while True:
				self.parse_state()

	def send(self, endpoint):
		global bouncetime
		time_now = time()

		if (time_now - self.time_stamp) >= bouncetime:
			print "ATTEMPTING SEND!"
			url = "%s/%s" % (self.global_endpoint, endpoint)

			try:
				r = requests.get(url)
			except Exception as e:
				pass

			self.time_stamp = time_now

	def terminate(self):
		pass

class ReceiverThread(GPIOThread):
	def __init__(self):
		super(ReceiverThread, self).__init__()

	def on_hang_up(self):
		super(ReceiverThread, self).send("hang_up")

	def on_pick_up(self):
		super(ReceiverThread, self).send("pick_up")

class ButtonThread(GPIOThread):
	def __init__(self, pin):
		from Button import Button
		self.component = Button(pig, pin, callback=self.on_button_press)

		super(ButtonThread, self).__init__()

	def on_button_press(self, gpio, level, tick):
		print "PRESSED %s" % gpio
		super(ButtonThread, self).send("mapping/%d" % gpio)

	def terminate(self):
		super(ButtonThread, self).terminate()
		self.component.unlisten()

class ButtonLowThread(GPIOThread):
	def __init__(self, pin):
		from ButtonLow import ButtonLow
		self.component = ButtonLow(pig, pin, callback=self.on_button_press)

		super(ButtonLowThread, self).__init__()

	def on_button_press(self, gpio, level, tick):
		print "PRESSED %s" % gpio
		super(ButtonLowThread, self).send("mapping/%d" % gpio)

	def terminate(self):
		super(ButtonThread, self).terminate()
		self.component.unlisten()

class MatrixKeypadThread(GPIOThread):
	def __init__(self, matrix):
		from MatrixKeypad import MatrixKeypad
		self.component = MatrixKeypad(pig, matrix[0], matrix[1])

		super(MatrixKeypadThread, self).__init__()

	def state_parser(self):
		key_pressed = self.component.read_key()
		if key_pressed is not None:
			self.on_button_press(key_pressed)

		sleep(0.1)

	def on_button_press(self, button):
		super(MatrixKeypadThread, self).send("mapping/%d" % button)

class TrellisKeypadThread(GPIOThread):
	def __init__(self):
		from TrellisKeypad import TrellisKeypad
		self.component = TrellisKeypad(callback=self.on_button_press)

		super(TrellisKeypadThread, self).__init__()

	def state_parser(self):
		sleep(0.03)
		self.component.listen()

	def on_button_press(self, button):
		super(TrellisKeypadThread, self).send("mapping/%d" % button)

class HallEffectReceiverThread(ReceiverThread):
	def __init__(self, pin):
		from HallEffect import HallEffect
		self.component = HallEffect(pig, pin, callback=self.on_pick_up, release_callback=self.on_hang_up)

		super(HallEffectReceiverThread, self).__init__()

	def on_pick_up(self, gpio, level, tick):
		super(HallEffectReceiverThread, self).on_pick_up()

	def on_hang_up(self, gpio, level, tick):
		super(HallEffectReceiverThread, self).on_hang_up()

	def terminate(self):
		super(ButtonThread, self).terminate()
		self.component.unlisten()

class IRReceiverThread(ReceiverThread):
	def __init__(self, threshold):
		self.is_hung_up = True
		self.threshold = threshold

		from VCNL4010 import VCNL4010
		self.component = VCNL4010()
		self.component.continuous_conversion_on()

		super(IRReceiverThread, self).__init__()

	def parse_state(self):
		global bouncetime
		sleep(0.3)

		proximity = self.component.read_proximity()
		
		if self.is_hung_up and proximity <= self.threshold['pick_up']:
			self.on_pick_up()
			sleep(bouncetime)
		elif not self.is_hung_up and proximity >= self.threshold['hang_up']:
			self.on_hang_up()
			sleep(bouncetime)

	def on_pick_up(self):
		self.is_hung_up = False
		super(IRReceiverThread, self).on_pick_up()

	def on_hang_up(self):
		self.is_hung_up = True
		super(IRReceiverThread, self).on_hang_up()

def teardown_handler(signal, frame):
	print "SIGNAL TO TEARDOWN PIGPIO!"
	
	teardown_pigpio()
	pig.stop()
	
	exit(0)

def build_pigpio(manifest, api_port_, bouncetime_):
	manifest = json.loads(manifest)

	global api_port, bouncetime
	api_port = int(api_port_)
	bouncetime = bouncetime_

	if "buttons" in manifest.keys():
		if manifest['buttons']['type'] == "Button":
			for pin in manifest['buttons']['pins']:
				components.append(ButtonThread(pin))

		if manifest['buttons']['type'] == "ButtonLow":
			for pin in manifest['buttons']['pins']:
				components.append(ButtonLowThread(pin))

		if manifest['buttons']['type'] == "MatrixKeypad":
			components.append(MatrixKeypadThread(manifest['buttons']['pins']))

		if manifest['buttons']['type'] == "TrellisKeypad":
			components.append(TrellisKeypadThread())
		
	if "receiver" in manifest.keys():
		if manifest['receiver']['type'] == "HallEffect":
			components.append(HallEffectReceiverThread(manifest['receiver']['pin']))

		if manifest['receiver']['type'] == "IRReceiver":
			components.append(IRReceiverThread(manifest['receiver']['threshold']))

	for c in components:
		c.start()

def teardown_pigpio():
	for c in components:
		c.terminate()

signal.signal(signal.SIGINT, teardown_handler)

if __name__ == "__main__":
	print argv

	build_pigpio(argv[1], argv[2], bouncetime_=2.5 if len(argv) == 3 else argv[3])
	
	while True:
		try:
			pass
		except KeyboardInterrupt:
			break	

	


