from MomentarySwitch import MomentarySwitch

class Button(MomentarySwitch):
	def __init__(self, pin, callback=None):
		super(Button, self).__init__(pin, True, bouncetime=0.3, callback=callback)
		self.listen()