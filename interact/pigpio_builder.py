import os, pigpio, json, requests, threading
from sys import argv, exit
from time import sleep

pig = pigpio.pi()
api_port = 8080
components = []

class GPIOThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		
		global api_port
		self.global_endpoint = "http://localhost:%d" % api_port

	def run(self):
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
			print "OH NO COULD NOT SEND"
			print e, type(e)

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
		print "HELLO PRESS %s" % gpio
		super(ButtonThread, self).send("mapping/%d" % gpio)

class HallEffectReceiverThread(ReceiverThread):
	def __init__(self, pin):
		from HallEffect import HallEffect
		self.component = HallEffect(pig, pin, callback=self.on_pick_up, release_callback=self.on_hang_up)

		super(HallEffectReceiverThread, self).__init__()

	def on_pick_up(self, gpio, level, tick):
		super(HallEffectReceiverThread, self).on_pick_up()

	def on_hang_up(self, gpio, level, tick):
		super(HallEffectReceiverThread, self).on_hang_up()

def build_pigpio(manifest):
	manifest = json.loads(manifest)

	if "buttons" in manifest.keys():
		if manifest['buttons']['type'] == "Button":
			for pin in manifest['buttons']['pins']:
				components.append(ButtonThread(pin))
		
	if "receiver" in manifest.keys():
		if manifest['receiver']['type'] == "HallEffect":
			components.append(HallEffectReceiverThread(manifest['receiver']['pin']))

		# etc.

	for c in components:
		c.start()

	return False

if __name__ == "__main__":
	print argv
	exit(0 if build_pigpio(argv[1]) else -1)