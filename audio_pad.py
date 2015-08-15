import os, signal, logging
from subprocess import Popen, PIPE
from time import time, sleep
from fabric.api import settings, local

from vars import DTMF, MAX_RECORDING_TIME, RATE

class MPAudioPad(object):
	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['ivr']['log'], level=logging.DEBUG)
		
	def ap_receive(self, command):
		if "press" in command.keys() and command['press'] in DTMF:
			return self.play_tone(command['press'])			

		elif "play" in command.keys():
			return self.play(command['play'])

		elif "start_recording" in command.keys():
			return self.start_recording(command['start_recording'])

		elif "stop_recording" in command.keys():
			return self.stop_recording()
		
		return False

	def play_tone(self, tone):
		return self.__play_audio(os.path.join(self.conf['media_dir'], "dtmf", "DTMF-%s.wav" % tone))

	def play(self, src):
		return self.__play_audio(os.path.join(self.conf['media_dir'], src))

	def __play_audio(self, src):
		try:
			play_cmd = ["aplay", "-N", "--process-id-file", \
				self.conf['d_files']['ap_player']['pid'], src]

			logging.debug("CMD: %s" % " ".join(play_cmd))
			Popen(play_cmd, stdout=PIPE, stderr=PIPE).communicate()
						
			return True
		except Exception as e:
			print e, type(e)
			logging.error("could not play file: %s" % e)

		return False

	def start_recording(self, dst):
		try:
			record_cmd = ["arecord", "-D", "plughw:0", "-f", "dat", "-r", str(RATE), "-N", \
				"--process-id-file", self.conf['d_files']['ap_recorder']['pid'], \
				os.path.join(self.conf['media_dir'], dst)]

			logging.debug("CMD: %s" % " ".join(record_cmd))
			Popen(record_cmd, stdout=PIPE, stderr=PIPE)

			while not os.path.exists(self.conf['d_files']['ap_recorder']['pid']):
				pass

			with open(self.conf['d_files']['ap_recorder']['pid'], 'rb') as PID:
				current_record_pid = PID.read().strip()
				self.db.set("CURRENT_RECORD_PID", current_record_pid)

			os.remove(self.conf['d_files']['ap_recorder']['pid'])
			sleep(0.001)

			logging.info("NOW ABSORBED INTO %s" % current_record_pid)

			return True
		except Exception as e:
			logging.error("COULD NOT START RECORDING: %s" % e)
			print e, type(e)

		return False

	def stop_recording(self, message=None):
		logging.debug("STOPPING RECORDING %s" % ("MANUALLY." if message is None else " : %s" % message))

		try:			
			os.kill(int(self.db.get("CURRENT_RECORD_PID")), signal.SIGKILL)

			return True
		except Exception as e:
			logging.error("COULD NOT STOP RECORDING: %s" % e)
			print e, type(e)

		return False

