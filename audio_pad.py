import os, signal, logging, json, threading
from subprocess import Popen, PIPE
from time import time, sleep
from fabric.api import settings, local

from utils import start_daemon, stop_daemon, get_config
from vars import BASE_DIR, DTMF, MAX_RECORDING_TIME, RATE, ENDIAN, AUDIO_BIN_SIZE, FRAMERATE, \
	MAX_AUDIO_LEVEL

twilio_audio = get_config('twilio_audio')
if twilio_audio in [None, False]:
	import pygame

AMIXER_EXE = "amixer -q sset 'Speaker' %s,%s"

class MPAudioPad():
	def __init__(self):
		self.split_chan = False
		
		if get_config('split_audio_channels'):
			self.split_chan = True

		self.max_audio_level = get_config('max_audio_level')
		if self.max_audio_level is None:
			self.max_audio_level = MAX_AUDIO_LEVEL

		logging.basicConfig(filename=self.conf['d_files']['audio']['log'], level=logging.DEBUG)

	def start_audio_pad(self):
		if twilio_audio:
			logging.info("Twilio Audio; no audio pad needed")
			return

		start_daemon(self.conf['d_files']['audio'])
			
		with settings(warn_only=True):
			local("rm ~/.asoundrc")
			local("ln -s %s ~/.asoundrc" % os.path.join(BASE_DIR, "core", "lib", "alsa-config", "asoundrc"))
		
		self.restore_audio()

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
					res['ok'] = self.play(command['play'], interruptable=command['interruptable'])
				
				elif "start_recording" in command.keys():
					res['ok'] = self.start_recording(command['start_recording'])
				
				elif "stop_recording" in command.keys():
					res['ok'] = self.stop_recording()
				
				elif "stop_audio" in command.keys():
					res['ok'] = self.stop_audio()

				self.db.publish('audio_responder', json.dumps(res))

	def stop_audio_pad(self):
		if twilio_audio:
			logging.info("Twilio audio. No Audio pad here.")

		stop_daemon(self.conf['d_files']['audio'])

	def restore_audio(self):
		if twilio_audio:
			return

		with settings(warn_only=True):
			local(AMIXER_EXE % ("{0}%".format(self.max_audio_level), \
				"{0}%".format(self.max_audio_level)))

	def stop_audio(self, channel=None):
		if channel is None:
			channel = [0,1]

		if type(channel) is not list:
			channel = [channel]

		for c in channel:
			channel_ = pygame.mixer.Channel(c)
			channel_.stop()
		
		return True

	def pause(self, channel=0):
		channel = pygame.mixer.Channel(channel)
		channel.pause()
		return True

	def unpause(self, channel=0):
		channel = pygame.mixer.Channel(channel)
		channel.unpause()
		return True

	def mute_channel(self, channel):
		logging.info("MUTING AUDIO CHANNEL %d" % channel)

		with settings(warn_only=True):
			local(AMIXER_EXE % ("0%" if channel == 0 else "0%+", \
				"0%" if channel == 1 else "0%+"))

		return True

	def unmute_channel(self, channel):
		logging.info("UNMUTING AUDIO CHANNEL %d" % channel)
		
		with settings(warn_only=True):
			local(AMIXER_EXE % ("{0}%".format(self.max_audio_level) if channel == 0 else "0%+", \
				"{0}%".format(self.max_audio_level) if channel == 1 else "0%+"))

		return True

	class PlayThread(threading.Thread):
		def __init__(self, db, channel, target, callback):
			threading.Thread.__init__(self)
			self.db = db
			self.handler = self.db.pubsub()
			self.handler.subscribe([channel])
			self.target = target
			self.callback = callback

		def run(self):
			for command in self.handler.listen():
				if not command['data']:
					continue

				try:
					command = json.loads(command['data'])
				except Exception as e:
					continue

				if self.target in command.keys():
					self.handler.unsubscribe()
					self.callback()

	def play(self, src, interruptable=True):
		src = os.path.join(self.conf['media_dir'], src)

		try:
			audio = pygame.mixer.Sound(src)
			channel = pygame.mixer.Channel(0)
		
			if self.split_chan:
				channel.set_volume(1, 0)

			duration = audio.get_length()
			time_started = time()
			time_finished = duration + time_started
			channel.play(audio)

			logging.debug("streaming sound file %s" % src)

			if not interruptable:
				self.interrupted = False

				def on_interrupted():
					self.interrupted = True
					self.stop_audio()

				play_thread = self.PlayThread(self.db, 'audio_receiver', 'stop_audio', on_interrupted)
				play_thread.start()
				
				while not self.interrupted:
					if time() > time_finished:
						self.interrupted = True
						break

					sleep(1)

				del self.interrupted

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
			logging.debug("playing clip %s (length %d)" % (src, audio.get_length()))

			if not interruptable:
				sleep(audio.get_length())
			
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

