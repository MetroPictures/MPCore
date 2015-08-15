import os

PROD_MODE = "debug"	# or "production"

BASE_DIR = os.getcwd()

GATHER_MODE = 1
RESPOND_MODE = 2

# dtmf tones
DTMF = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", \
	"s", "p", "d", "b", "r"]

# represents keys on a telephone; l-r, t-b
DEFAULT_TELEPHONE_GPIO = xrange(3, 15)
DEFAULT_RELEASE_KEY = 14	# pound sign

DEFAULT_GATHER_EXPIRY = 8000	# seconds until gather is nullified (if flag set)

UNPLAYABLE_FILES = [".DS_Store", "._.DS_Store"]

# recording presets
MAX_RECORDING_TIME = 60
RATE = 48000