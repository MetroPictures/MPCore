import os, json, logging
from time import time, sleep
from fabric.api import settings, local

from audio_pad import MPAudioPad
from utils import start_daemon, stop_daemon
from vars import PROD_MODE, DEFAULT_RELEASE_KEY, GATHER_MODE, RESPOND_MODE, BASE_DIR, DEFAULT_GATHER_EXPIRY

class MPIVR(MPAudioPad):
	"""The mock IVR client.

	Modeled after Twilio.

	"""

	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['ivr']['log'], level=logging.DEBUG)
		MPAudioPad.__init__(self)

	def say(self, message, interruptable=True):
		logging.debug("saying %s" % message)

		return self.send_command({ 'play' : message, 'interruptable' : interruptable })

	def record(self, message, dst=None, release_keys=DEFAULT_RELEASE_KEY):
		if dst is None:
			dst = "recording_%d.wav" % time()

		logging.debug("recording into %s" % dst)

		if self.say(message)['ok'] and self.send_command({ 'start_recording' : dst })['ok']:
			if self.gather(release_keys=release_keys) is not None:
				return self.send_command({ 'stop_recording' : True })['ok']

		return False

	def gather(self, release_keys=DEFAULT_RELEASE_KEY, expires=False):
		if type(release_keys) is not list:
			release_keys = [release_keys]

		logging.debug("gathering for %s" % release_keys)

		gathered_keys = None
		gather_start = time()
		self.db.set('MODE', GATHER_MODE)

		while True:
			try:
				gathered_keys = json.loads(self.db.get('gathered_keys'))				
				
				if len(set(release_keys) & set(gathered_keys)) == 1:
					logging.debug("gathered %s" % gathered_keys)
					break			

			except Exception as e:
				pass

			if expires and abs(gather_start - time()) > DEFAULT_GATHER_EXPIRY:
				logging.debug("gather has expired!")
				gathered_keys = None
				break

			sleep(1)

		self.db.set('MODE', RESPOND_MODE)
		self.db.set('gathered_keys', None)
		return gathered_keys

	def prompt(self, message, release_keys=DEFAULT_RELEASE_KEY, expires=False):
		logging.debug("prompt with message %s" % message)

		if type(release_keys) is not list:
			release_keys = [release_keys]
		
		if self.say(message)['ok']:
			gathered_keys = self.gather(release_keys=release_keys, expires=expires)
			return list(set(release_keys) & set(gathered_keys))[0]

		return None

	def sequence(self, message, release_keys=DEFAULT_RELEASE_KEY, expires=False):
		logging.debug("capturing sequence with message %s" % message)

		if type(release_keys) is not list:
			release_keys = [release_keys]

		if self.say(message)['ok']:
			gathered_keys = self.gather(release_keys=release_keys, expires=expires)
			return [k for k in gathered_keys if k not in release_keys]

		return None

	def send_command(self, command):
		audio_responder = self.db.pubsub()
		audio_responder.subscribe('audio_responder')

		res = { 'ok' : False }
		self.db.publish('audio_receiver', json.dumps(command))

		while True:
			response = audio_responder.get_message()

			if response is None or not response['data']:
				continue

			try:
				response = json.loads(response['data'])
			except Exception as e:
				continue

			if 'ok' in response.keys():
				res = response

			break

		audio_responder.unsubscribe()
		logging.debug("Command/Response cycle released: %s" % json.dumps(response))
		return res


