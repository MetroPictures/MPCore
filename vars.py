import os

PROD_MODE = "debug"	# or "production"

BASE_DIR = os.getcwd()

GATHER_MODE = 1
RESPOND_MODE = 2

# dtmf tones
DTMF = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", \
	"s", "p", "d", "b", "r"]

# represents keys on a telephone; l-r, t-b
MAX_AUDIO_LEVEL = 50
DEFAULT_TELEPHONE_GPIO = range(3, 15)
DEFAULT_RELEASE_KEY = 14	# pound sign

DEFAULT_GATHER_EXPIRY = 8000	# seconds until gather is nullified (if flag set)

UNPLAYABLE_FILES = [".DS_Store", "._.DS_Store"]

# recording presets
MAX_RECORDING_TIME = 60
RATE = 48000
AUDIO_BIN_SIZE = 2048
ENDIAN = -16
FRAMERATE = 30

NO_KILL_RX = [
	r".*\d{1,2}:\d{2}[:|\.]\d{2}\s+/bin/sh",
	r".*\d{1,2}:\d{2}[:|\.]\d{2}\s+grep"
]

KILL_RX = r"(?:\d{3,4}|[a-zA-Z0-9_\-\+]{1,8})\s+(\d{2,6}).*%s\.py"