# (Modified from python class by AKA MEDIA SYSTEM, also public domain http://hi-hi-hi.com <3)

# To use: Connect VCC to 3.3-5V (5V is best if it is available), GND to
#         ground, SCL to i2c clock (on classic arduinos, Analog 5), SDA
#         to i2c data (on classic arduinos Analog 4). The 3.3v pin is
#         an ouptut if you need 3.3V
# This sensor is 5V compliant so you can use it with 3.3 or 5V micros

from Adafruit_I2C import Adafruit_I2C
from time import sleep

class VCNL4010():
	# the i2c address
	VCNL4010_ADDRESS = 0x13

	VCNL4010_COMMAND = 0x80
	VCNL4010_PRODUCTID = 0x81
	VCNL4010_IRLED = 0x83
	VCNL4010_AMBIENTPARAMETER = 0x84
	VCNL4010_AMBIENTDATA = 0x85
	VCNL4010_PROXIMITYDATA = 0x87
	VCNL4010_SIGNALFREQ = 0x89
	VCNL4010_PROXIMITYADJUST = 0x8
	VCNL4010_3M125 = 0
	VCNL4010_1M5625 = 1
	VCNL4010_781K25 = 2
	VCNL4010_390K625 = 3
	VCNL4010_MEASUREAMBIENT = 0x10
	VCNL4010_MEASUREPROXIMITY = 0x08
	VCNL4010_AMBIENTREADY = 0x40
	VCNL4010_PROXIMITYREADY = 0x20

	def __init__(self, *args, **kwargs):
		self.i2c = Adafruit_I2C(self.VCNL4010_ADDRESS)
		
		rev = self.i2c.readU8(self.VCNL4010_PRODUCTID)
		if((rev & 0xF0) != 0x10):
			print "Sensor not found wtf"

		self.i2c.write8(self.VCNL4010_IRLED, 5)
		current = self.i2c.readU8(self.VCNL4010_IRLED)
		print "we think current is set to ", current

		sig_freq = self.i2c.readU8(self.VCNL4010_SIGNALFREQ)
		print "we think sig_freq is ", sig_freq

		self.i2c.write8(self.VCNL4010_PROXIMITYADJUST, 0x81)
		prox_adj = self.i2c.readU8(self.VCNL4010_PROXIMITYADJUST)
		print "we think prox_adj is", prox_adj

	def set_LED_current(self, current):
		if current > 20 or current < 0:
			current = 5

		self.i2c.write8(self.VCNL4010_IRLED, current)

	def continuous_conversion_on(self):
		self.i2c.write8(self.VCNL4010_AMBIENTPARAMETER, 0x89)

	def continuous_conversion_off(self):
		self.i2c.write8(self.VCNL4010_AMBIENTPARAMETER, 0x09)

	def set_signal_frequency(self, frequency):
		if frequency not in [00, 01, 02, 03]:
			frequency = 02
			print "frequency must be an int between 0 and 3. using 2 (default)"

		self.i2c.write8(self.VCNL4010_SIGNALFREQ, frequency)

	def get_signal_frequency(self, frequency):
		return self.i2c.readU8(self.VCNL4010_SIGNALFREQ)

	def set_proximity_adjust(self, prox_adj):
		# AKA says:
		# datasheet makes adjusting this look less wise than I thought. Ignoring for now.
    	# Should basically be set to 0x81 = 129
		pass

	def get_proximity(self):
		self.i2c.write8(self.VCNL4010_COMMAND, self.VCNL4010_MEASUREPROXIMITY)
		while True:
			if (self.i2c.readU8(self.VCNL4010_COMMAND) & self.VCNL4010_PROXIMITYREADY):
				h = self.i2c.readList(self.VCNL4010_PROXIMITYDATA, 2)
				return ((h[0] << 8) | h[1] >> 4)

			sleep(0.001)

	def read_ambient(self):
		self.i2c.write8(self.VCNL4010_COMMAND, self.VCNL4010_MEASUREAMBIENT)
		while True:
			if(self.i2c.readU8(self.VCNL4010_COMMAND) & self.VCNL4010_AMBIENTREADY):
				h = self.i2c.readList(self.VCNL4010_PROXIMITYDATA, 2)
				return ((h[0] << 8) | h[1] >> 4)

			sleep(0.001)


