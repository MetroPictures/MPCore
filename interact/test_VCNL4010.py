from VCNL4010 import VCNL4010
from time import sleep

PICK_UP = 2305
HANG_UP = 7437

if __name__ == "__main__":
	ir = VCNL4010()
	ir.continuous_conversion_on()

	is_hung_up = False

	while True:
		sleep(0.3)
		event_detected = None
		prox = ir.read_proximity()
		
		if is_hung_up and prox <= PICK_UP:
			event_detected = "PICKED UP"
			is_hung_up = False

		elif not is_hung_up and prox >= HANG_UP:
			event_detected = "HUNG UP"
			is_hung_up = True

		print "prox: %d %s" % (prox, "(with %s)" % \
			event_detected if event_detected is not None else "")