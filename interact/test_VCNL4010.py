from VCNL4010 import VCNL4010
from time import sleep

if __name__ == "__main__":
	ir = VCNL4010()
	ir.continuous_conversion_on()

	while True:
		prox = ir.read_proximity()
		amb = ir.read_ambient()

		print "prox: ", prox
		print "amb: ", amb

		sleep(0.05)