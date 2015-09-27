import os, signal, logging, pygame, json
from subprocess import Popen, PIPE
from time import time, sleep
from fabric.api import settings, local

from utils import start_daemon, stop_daemon
from vars import DTMF, MAX_RECORDING_TIME, RATE, ENDIAN, AUDIO_BIN_SIZE, FRAMERATE

class MPAudioPad():
	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['audio']['log'], level=logging.DEBUG)

	def start_audio_pad(self, num_channels=2):
		start_daemon(self.conf['d_files']['audio'])

		audio_receiver = self.db.pubsub()
		audio_receiver.subscribe(['audio_receiver'])
		
		pygame.mixer.pre_init(RATE, ENDIAN, num_channels, AUDIO_BIN_SIZE)
		pygame.init()

		while True:
			for command in audio_receiver.listen():
				if not command['data']:
					continue

				try:
					command = json.loads(command['data'])
				except Exception as e:
					continue

				print "COMMAND: ", command
				res = { 'command' : command, 'ok' : False }

				if "press" in command.keys():
					res['ok'] = self.press(command['press'])
				
				elif "play" in command.keys():
					res['ok'] = self.play(command['play'], interruptable=command['interruptable'])
				
				elif "start_recording" in command.keys():
					res['ok'] = self.start_recording(command['start_recording'])
				
				elif "stop_recording" in command.keys():
					res['ok'] = self.stop_recording()
				
				elif "stop_audio" in command.keys():
					res['ok'] = self.stop_audio()

				self.db.publish('audio_responder', json.dumps(res))

	def stop_audio_pad(self):
		stop_daemon(self.conf['d_files']['audio'])

	def stop_audio(self):
		pygame.mixer.music.stop()
		return True

	def pause(self):
		pygame.mixer.music.pause()
		return True

	def unpause(self):
		pygame.mixer.music.unpause()
		return True

	def play(self, src, interruptable=False):
		src = os.path.join(self.conf['media_dir'], src)

		try:
			pygame.mixer.music.load(src)
			pygame.mixer.music.play()

			logging.debug("streaming sound file %s" % src)
			return True

		except Exception as e:
			print e, type(e)
			logging.error("could not play file %s" % src)

		return False

	def press(self, tone):
		return self.play_clip(os.path.join("dtmf", "DTMF-%s.wav" % tone))

	def play_clip(self, src, channel=None):
		# TODO: multi-channel
		src = os.path.join(self.conf['media_dir'], src)

		try:
			audio = pygame.mixer.Sound(src)
			
			audio.play()
			sleep(audio.get_length())
			logging.debug("playing clip %s (length %d)" % (src, audio.get_length()))
			
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

