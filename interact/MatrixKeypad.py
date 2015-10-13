import pigpio
from time import sleep

class MatrixKeypad():
	def __init__(self, column_pins, row_pins):
		self.pig = pigpio.pi()
		self.column_pins = column_pins
		self.row_pins = row_pins

	def setup(self):
		for pin in self.column_pins:
			self.pig.set_mode(pin, pigpio.OUTPUT)
			self.pig.write(pin, 0)

		for pin in self.row_pins:
			self.pig.set_mode(pin, pigpio.INPUT)
			self.pig.set_pull_up_down(pin, pigpio.PUD_UP)

	def exit(self):
		for pin in self.row_pins:
			self.pig.set_mode(pin, pigpio.INPUT)
			self.pig.set_pull_up_down(pin, pigpio.PUD_UP)

		for pin self.column_pins:
			self.pig.set_mode(pin, pigpio.INPUT)
			self.pig.set_pull_up_down(pin, pigpio.PUD_UP)

	def read_key(self):
		self.setup()

		key_input = []
		row_val = -1
		col_val = -1

		for i in xrange(len(self.row_pins)):
			tmp_val = self.pig.read(self.row_pins[i])
			if tmp_val == 0:
				row_val = i

		if (row_val < 0) or (row_val > (len(self.column_pins) - 1)):
			self.exit()
			return

		key_input.append(row_val)

		for i in xrange(len(self.column_pins)):
			self.pig.set_mode(self.column_pins[i], pigpio.INPUT)
			self.pig.set_pull_up_down(self.column_pins[i], pigpio.PUD_DOWN)

		self.pig.set_mode(self.row_pins[row_val], pigpio.OUTPUT)
		self.pig.write(self.row_pins[row_val], 1)

		for i in xrange(len(self.column_pins)):
			tmp_val = self.pig.read(self.column_pins[i])
			if tmp_val == 1:
				col_val = i

		if (col_val < 0) or (col_val > (len(self.column_pins) - 1)):
			self.exit()
			return

		key_input.append(col_val)
		self.exit()

		return (key_input[0] * len(self.column_pins)) + key_input[1]


