from MomentarySwitch import MomentarySwitch

class Button(MomentarySwitch):
	def __init__(self, pig, pin, callback):
		super(Button, self).__init__(pig, pin, True, bouncetime=0.2, callback=callback)
		self.listen()