import pigpio
from time import sleep
from HallEffect import HallEffect

def test_pick_up(gpio, level, tick):
	print "HallEffect pick up callback triggered!"
	print gpio, level, tick

def test_hang_up(gpio, level, tick):
	print "HallEffect hang up callback triggered!"
	print gpio, level, tick


if __name__ == "__main__":
	pig = pigpio.pi()
	hall_effect = HallEffect(pig, 17, callback=test_pick_up, release_callback=test_hang_up)

	raw_input("Press Enter when ready...")
	print "Waiting for input"

	while True:
		try:
			sleep(0.01)
		except KeyboardInterrupt:
			print "Interrupted!"
			break

	hall_effect.unlisten()
	pig.stop()