from time import sleep
from TrellisKeypad import TrellisKeypad

NUMTRELLIS = 1
numKeys = NUMTRELLIS * 16

I2C_BUS = 1

MOMENTARY = 0
LATCHING = 1

MODE = LATCHING

matrix = TrellisKeypad()
trellis = TrellisKeypad.Adafruit_TrellisSet(matrix)

trellis.begin((0x70, I2C_BUS))

for i in range(numKeys):
	trellis.setLED(i)
	trellis.writeDisplay()
	sleep(0.05)

for i in range(numKeys):
	trellis.clrLED(i)
	trellis.writeDisplay()
	sleep(0.05)

while True:
	sleep(0.03)

	if MODE == MOMENTARY:
		if trellis.readSwitches():
			for i in range(numKeys):
				if trellis.justPressed(i):
					print "v%d" % i
					trellis.setLED(i)

				if trellis.justReleased(i):
					print "^%d" % i
					trellis.clrLED(i)

			trellis.writeDisplay()

	if MODE == LATCHING:
		if trellis.readSwitches():
			for i in range(numKeys):
				if trellis.justPressed(i):
					print "v%d" % i
					if trellis.isLED(i):
						trellis.clrLED(i)
					else:
						trellis.setLED(i)

			trellis.writeDisplay()