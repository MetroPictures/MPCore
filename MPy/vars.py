import os
#from RPi import GPIO

PROD_MODE = "debug"	# or "production"

BASE_DIR = os.getcwd()

GATHER_MODE = 1
RESPOND_MODE = 2

# represents keys on a telephone; l-r, t-b
#DEFAULT_TELEPHONE_GPIO = [(pin, GPIO.IN, GPIO.PUD_DOWN) for pin in xrange(3, 15)]
DEFAULT_TELEPHONE_GPIO = [(pin, "GPIO.IN", "GPIO.PUD_DOWN") for pin in xrange(3, 15)]
DEFAULT_RELEASE_KEY = 14	# pound sign

DEFAULT_GATHER_EXPIRY = 8000	# seconds until gather is nullified (if flag set)

UNPLAYABLE_FILES = [".DS_Store"]