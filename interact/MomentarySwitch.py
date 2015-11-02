import pigpio
from time import time

class MomentarySwitch(object):
	listen_for_press = None
	listen_for_release = None

	def __init__(self, pig, pin, trigger_low, bouncetime=0.3, callback=None, release_callback=None):
		self.pig = pig
		self.time_stamp = time()

		self.pin = pin
		self.trigger_low = trigger_low

		if self.trigger_low:
			self.pud = pigpio.PUD_UP
			self.pressed = pigpio.FALLING_EDGE
			self.released = pigpio.RISING_EDGE
		else:
			self.pud = pigpio.PUD_DOWN
			self.pressed = pigpio.RISING_EDGE
			self.released = pigpio.FALLING_EDGE

		self.callback = self.debounce(bouncetime, callback) if callback is not None else None
		self.release_callback = self.debounce(bouncetime, release_callback) if release_callback is not None else None

		self.pig.set_mode(self.pin, pigpio.INPUT)
		self.pig.set_pull_up_down(self.pin, self.pud)

	def listen(self):
		if self.callback is not None:
			self.listen_for_press = self.pig.callback(self.pin, self.pressed, self.callback)

		if self.release_callback is not None:
			self.listen_for_release = self.pig.callback(self.pin, self.released, self.release_callback)

	def unlisten(self):
		if self.listen_for_press is not None:
			self.listen_for_press.cancel()

		if self.listen_for_release is not None:
			self.listen_for_release.cancel()

	def debounce(self, bouncetime, func, *args, **kwargs):
		def debounced(*args, **kwargs):
			time_now = time()
			
			if (time_now - self.time_stamp) >= bouncetime:
				func(*args, **kwargs)
				self.time_stamp = time_now
			
		return debounced


