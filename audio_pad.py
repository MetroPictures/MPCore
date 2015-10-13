import os, signal, logging, json
from subprocess import Popen, PIPE
from time import time, sleep
from fabric.api import settings, local

from utils import start_daemon, stop_daemon, get_config
from vars import BASE_DIR, DTMF, MAX_RECORDING_TIME, RATE, ENDIAN, AUDIO_BIN_SIZE, FRAMERATE

if get_config('use_audio') in [None, True]:
	import pygame

class MPAudioPad():
	def __init__(self):
		self.split_chan = False
		
		if get_config('split_audio_channels'):
			self.split_chan = True

		logging.basicConfig(filename=self.conf['d_files']['audio']['log'], level=logging.DEBUG)

	def start_audio_pad(self):
		start_daemon(self.conf['d_files']['audio'])
			
		with settings(warn_only=True):
			local("rm ~/.asoundrc")
			local("ln -s %s ~/.asoundrc" % os.path.join(BASE_DIR, "core", "lib", "alsa-config", "asoundrc"))

		audio_receiver = self.db.pubsub()
		audio_receiver.subscribe(['audio_receiver'])
		
		pygame.mixer.pre_init(frequency=RATE, size=ENDIAN, channels=2, buffer=AUDIO_BIN_SIZE)
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
					res['ok'] = self.play(command['play'])
				
				elif "start_recording" in command.keys():
					res['ok'] = self.start_recording(command['start_recording'])
				
				elif "stop_recording" in command.keys():
					res['ok'] = self.stop_recording()
				
				elif "stop_audio" in command.keys():
					res['ok'] = self.stop_audio(channel=0) and self.stop_audio(channel=1)

				self.db.publish('audio_responder', json.dumps(res))

	def stop_audio_pad(self):
		stop_daemon(self.conf['d_files']['audio'])

	def stop_audio(self, channel=0):
		channel = pygame.mixer.Channel(channel)
		channel.stop()
		return True

	def pause(self, channel=0):
		channel = pygame.mixer.Channel(channel)
		channel.pause()
		return True

	def unpause(self, channel=0):
		channel = pygame.mixer.Channel(channel)
		channel.unpause()
		return True

	def play(self, src):
		src = os.path.join(self.conf['media_dir'], src)

		try:
			audio = pygame.mixer.Sound(src)
			channel = pygame.mixer.Channel(0)
		
			if self.split_chan:
				channel.set_volume(1, 0)

			channel.play(audio)
			logging.debug("streaming sound file %s" % src)

			return True

		except Exception as e:
			print e, type(e)
			logging.error("could not play file %s" % src)

		return False

	def press(self, tone):
		return self.play_clip(os.path.join("dtmf", "DTMF-%s.wav" % tone))

	def play_clip(self, src, channel=None, interruptable=False):
		src = os.path.join(self.conf['media_dir'], src)

		try:
			audio = pygame.mixer.Sound(src)
			channel = pygame.mixer.Channel(1)

			if self.split_chan:
				channel.set_volume(0, 1)
			
			channel.play(audio)

			if not interruptable:
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

