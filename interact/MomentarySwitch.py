import pigpio
from time import time

class MomentarySwitch():
	def __init__(self, pin, trigger_low, callback=None, release_callback=None, boucetime=0.3):
		self.pig = pigpio.pi()
		self.time_stamp = time()

		self.pin = pin
		self.trigger_low = trigger_low

		if self.trigger_low:
			self.pud = pigpio.PUD_UP
			self.pressed = pigpio.FALLING_EDGE
			self.released = pigpio.RISING_EDGE
		else:
			self.pud = pigpio.PUD_DOWN
			self.pressed = pigpio.FALLING_EDGE
			self.released = pigpio.RISING_EDGE

		self.callback = self.debounce(boucetime, callback)
		self.release_callback = self.debounce(boucetime, release_callback)

		self.pig.set_mode(self.pin, pigpio.INPUT)
		self.pig.set_pull_up_down(self.pin, self.pud)

	def listen(self):
		self.listen_for_press = self.pig.callback(self.pin, self.pressed, self.callback)
		self.listen_for_release = self.pig.callback(self.pin, self.released, self.release_callback)

	def unlisten(self):
		self.listen_for_press.cancel()
		self.listen_for_release.cancel()

	def debounce(self, bouncetime, func, *args, **kwargs):
		time_now = time()

		if(time_now - self.time_stamp) >= bouncetime:
			func(*args, **kwargs)

		self.time_stamp = time_now