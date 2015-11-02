from time import sleep
from TrellisKeypad import TrellisKeypad

def on_button_press(button):
	print "Button pressed: %d" % button

if __name__ == "__main__":
	trellis = TrellisKeypad(callback=on_button_press)

	while True:
		sleep(0.03)
		trellis.listen()
