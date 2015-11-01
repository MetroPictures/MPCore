from MomentarySwitch import MomentarySwitch

class ButtonLow(MomentarySwitch):
	def __init__(self, pig, pin, callback):
		super(ButtonLow, self).__init__(pig, pin, False, bouncetime=0.2, callback=callback)
		self.listen()