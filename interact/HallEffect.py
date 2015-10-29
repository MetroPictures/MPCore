from MomentarySwitch import MomentarySwitch

class HallEffect(MomentarySwitch):
	def __init__(self, pin, callback=None, release_callback=None):
		super(HallEffect, self).__init__(pin, False, bouncetime=0, \
			callback=callback, release_callback=receiver_callback)

		self.listen()