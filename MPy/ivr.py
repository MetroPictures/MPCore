import os, json, socket, logging
from time import time, sleep

from vars import PROD_MODE, DEFAULT_RELEASE_KEY, GATHER_MODE, RESPOND_MODE

class MPIVR(object):
	"""The mock IVR client.

	Modeled after Twilio.

	"""

	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['ivr']['log'], level=logging.DEBUG)

	def say(self, message):
		logging.info("saying %s" % message)

		say = self.send_command({ 'play' : message })
		
		if 'play_length' in say.keys():
			play_length = say['play_length']/1000
			
			logging.info("waiting %d until after this has been played!" % play_length)
			
			sleep(play_length)

		return say

	def record(self, message, dst=None, release_keys=DEFAULT_RELEASE_KEY):
		if dst is None:
			dst = "recording_%d.wav" % time()

		logging.info("recording into %s" % dst)

		if self.say(message)['ok'] and self.send_command({ 'start_recording' : dst })['ok']:
			if self.gather(release_keys=release_keys) is not None:
				return self.send_command({ 'stop_recording' : True })['ok']

		return False

	def gather(self, release_keys=DEFAULT_RELEASE_KEY, expires=False):
		if type(release_keys) is not list:
			release_keys = [release_keys]
		
		gathered_keys = None
		gather_start = time()

		if type(release_keys) is not list:
			release_keys = [release_keys]

		self.db.set('MODE', GATHER_MODE)
		logging.info("gathering for %s" % release_keys)

		while True:
			try:
				gathered_keys = json.loads(self.db.get('gathered_keys'))				
				
				if len(set(release_keys) & set(gathered_keys)) == 1:
					self.db.set('MODE', RESPOND_MODE)
					self.db.set('gathered_keys', None)

					logging.info("gathered %s" % gathered_keys)

					break			

			except Exception as e:
				pass

			if expires and abs(gather_start - time()) > DEFAULT_GATHER_EXPIRY:
				logging.info("gather has expired!")
				return None

			sleep(1)

		if PROD_MODE == "debug":
			logging.debug("release keys: %s" % release_keys)
			logging.debug("gathered keys: %s" % gathered_keys)

		return gathered_keys

	def prompt(self, message, release_keys=DEFAULT_RELEASE_KEY, expires=False):
		print("prompt with message %s" % message)

		if type(release_keys) is not list:
			release_keys = [release_keys]
		
		if self.say(message)['ok']:
			gathered_keys = self.gather(release_keys=release_keys, expires=expires)
			return list(set(release_keys) & set(gathered_keys))[0]

	def send_command(self, command):
		result = { 'ok' : False, 'command' : command }

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect(("127.0.0.1", self.conf['processing_port']))
		except Exception as e:
			logging.warning("Could not connect to processing:")
			
			if PROD_MODE == "debug":
				print e, type(e)

			result['error'] = "Could not connect to processing."
			return result

		s.sendall(json.dumps(command))
		
		while True:
			data = s.recv(1024)
			if data == "":
				break

			try:
				result.update(json.loads(data))
				result['ok'] = result['response']

			except Exception as e:
				logging.warning("could not jsonify data:")
				if PROD_MODE == "debug":
					print e, type(e)

				result['error'] = "could not jsonify data"

			break

		s.shutdown(socket.SHUT_WR)
		s.close()

		if not result['ok'] and result['retry_command']:
			return self.send_command(command)
		
		return result
