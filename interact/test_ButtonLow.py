import pigpio
from time import sleep
from ButtonLow import ButtonLow

def test_callback(gpio, level, tick):
	print "Button callback triggered!"
	print gpio, level, tick

if __name__ == "__main__":
	pig = pigpio.pi()
	button = ButtonLow(pig, 23, callback=test_callback)

	raw_input("Press Enter when ready...")
	print "Waiting for input"
	print dir(button)

	while True:
		try:
			sleep(0.01)
		except KeyboardInterrupt:
			print "Interrupted!"
			break

	button.unlisten()
	pig.stop()