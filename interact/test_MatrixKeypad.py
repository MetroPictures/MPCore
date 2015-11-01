import pigpio
from time import sleep
from MatrixKeypad import MatrixKeypad

if __name__ == "__main__":
	pig = pigpio.pi()
	matrix = [
		[6, 13, 19, 26],
		[21, 20, 16, 12]
	]

	matrix_keypad = MatrixKeypad(pig, matrix[0], matrix[1])

	raw_input("Press Enter when ready...")
	print "Waiting for input"

	while True:
		try:
			key_pressed = matrix_keypad.read_key()
			if key_pressed is not None:
				print "KEY PRESSED: %s" % key_pressed

			sleep(0.1)
		except KeyboardInterrupt:
			print "Interrupted!"
			break

	pig.stop()