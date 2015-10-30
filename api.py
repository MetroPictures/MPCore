import signal, os, redis, json, logging
from multiprocessing import Process
import tornado.ioloop, tornado.httpserver, tornado.web
from time import sleep

from ivr import MPIVR
from gpio import MPGPIO

from utils import start_daemon, stop_daemon, get_config, str_to_bool
from vars import PROD_MODE, BASE_DIR, GATHER_MODE, RESPOND_MODE

def terminationHandler(signal, frame): exit(0)
signal.signal(signal.SIGINT, terminationHandler)

class MPServerAPI(tornado.web.Application, MPIVR, MPGPIO):
	"""The REST API.

	To be used to direct communication flows between the circuitry inputs and outputs.

	"""
	
	def __init__(self):
		api_port, num_processes, redis_port, rpi_id, custom_test_pad = \
			get_config(['api_port', 'num_processes', 'redis_port', 'rpi_id', 'custom_test_pad'])

		self.conf = {
			'rpi_id' : rpi_id,
			'd_files' : {
				'api' : {
					'pid' : os.path.join(BASE_DIR, ".monitor", "server.pid.txt"),
					'log' : os.path.join(BASE_DIR, ".monitor", "%s.log.txt" % rpi_id),
					'ports' : api_port
				},
				'gpio' : {
					'log' : os.path.join(BASE_DIR, ".monitor", "%s.log.txt" % rpi_id),
					'pid' : os.path.join(BASE_DIR, ".monitor", "gpio.pid.txt")
				},
				'ivr' : {
					'log' : os.path.join(BASE_DIR, ".monitor", "%s.log.txt" % rpi_id)
				},
				'module' : {
					'log' : os.path.join(BASE_DIR, ".monitor", "%s.log.txt" % rpi_id),
					'pid' : os.path.join(BASE_DIR, ".monitor", "%s.pid.txt" % rpi_id)
				},
				'ap_recorder' : {
					'pid' : os.path.join(BASE_DIR, ".monitor", "ap_recorder.pid.txt")
				},
				'ap_player' : {
					'pid' : os.path.join(BASE_DIR, ".monitor", "ap_player.pid.txt")
				},
				'audio' : {
					'pid' : os.path.join(BASE_DIR, ".monitor", "audio.pid.txt"),
					'log' : os.path.join(BASE_DIR, ".monitor", "%s.log.txt" % rpi_id)
				}
			},
			'api_port' : api_port,
			'num_processes' : num_processes,
			'redis_port' : redis_port,
			'media_dir' : os.path.join(BASE_DIR, "core", "media")
		}

		if custom_test_pad is not None:
			self.test_pad_dir = os.path.join(BASE_DIR, custom_test_pad)
			print "CUSTOM TEST PAD: %s" % self.test_pad_dir
		else:
			self.test_pad_dir = os.path.join(BASE_DIR, "core", "test_pad")

		self.routes = [
			("/", self.TestHandler),
			(r'/js/(.*)', tornado.web.StaticFileHandler, \
				{ 'path' : os.path.join(self.test_pad_dir, "js")}),
			("/status", self.StatusHandler),
			("/pick_up", self.PickUpHandler),
			("/hang_up", self.HangUpHandler),
			(r'/mapping/(\d+)', self.MappingHandler)
		]

		self.db = redis.StrictRedis(host='localhost', port=self.conf['redis_port'], db=0)
		
		logging.basicConfig(filename=self.conf['d_files']['api']['log'], level=logging.DEBUG)

	def start(self):
		logging.info("Start invoked.")

		MPIVR.__init__(self)
		MPGPIO.__init__(self)

		p = Process(target=self.start_audio_pad)
		p.start()	

		p = Process(target=self.start_gpio)
		p.start()

		p = Process(target=self.start_api)
		p.start()

		while not self.get_gpio_status():
			sleep(1)		

		logging.info("EVERYTHING IS ONLINE.")
		return True

	def stop(self):
		logging.info("Stop invoked.")

		self.stop_api()
		self.stop_gpio()
		self.stop_audio_pad()
		
		logging.info("EVERYTHING IS OFFLINE.")
		return True

	class TestHandler(tornado.web.RequestHandler):
		def get(self):
			self.render(os.path.join(self.application.test_pad_dir, "index.html"))

	class StatusHandler(tornado.web.RequestHandler):
		def get(self):
			result = self.application.get_status()

			self.set_status(200 if result['ok'] else 400)
			self.finish(result)

	class PickUpHandler(tornado.web.RequestHandler):
		def get(self):
			logging.info("pick up: rpi_id %s" % self.application.conf['rpi_id'])
			
			result = self.application.on_pick_up()

			if type(result) is dict:
				self.set_status(200 if result['ok'] else 400)

			self.finish(result)

	class HangUpHandler(tornado.web.RequestHandler):
		def get(self):
			logging.info("hang up: rpi_id %s" % self.application.conf['rpi_id'])
			
			result = self.application.on_hang_up()

			if type(result) is dict:
				self.set_status(200 if result['ok'] else 400)
			
			self.finish(result)

	class MappingHandler(tornado.web.RequestHandler):
		def get(self, pin):
			pin = int(pin)

			logging.info("pin %d: rpi_id %s" % (pin, self.application.conf['rpi_id']))

			result = self.application.on_key_pressed(pin)

			if type(result) is dict:
				self.set_status(200 if result['ok'] else 400)
			
			self.finish(result)

	def map_key_to_tone(self, key):
		if key not in [12, 13, 14]:
			tone = str(key - 2)
		elif key == 12:
			tone = 's'
		elif key == 13:
			tone = str(0)
		elif key == 14:
			tone = 'p'
		 
		return tone

	def on_key_pressed(self, key):
		if str_to_bool(self.db.get('IS_HUNG_UP')):
			return { 'ok' : False, 'error' : "Phone is hung up" }

		# play dmtf tone;
		command = { "press" : self.map_key_to_tone(key) }
		
		mode = int(self.db.get('MODE'))
		logging.info("CURRENT MODE: %d" % mode)

		if mode == GATHER_MODE:
			logging.info("THIS IS A GATHER: %d" % key)

			try:
				gathered_keys = json.loads(self.db.get('gathered_keys'))
				print gathered_keys
			except Exception as e:
				logging.warning("could not get gathered_keys: ")
				print e, type(e)

				gathered_keys = []

			gathered_keys += [key]
			self.db.set('gathered_keys', json.dumps(gathered_keys))

		return self.send_command(command)

	def reset_for_call(self):
		self.db.set('IS_HUNG_UP', False)
		self.db.set('MODE', RESPOND_MODE)
		self.db.set('gathered_keys', None)

	def on_pick_up(self):
		logging.info("picking up")

		self.reset_for_call()

		p = Process(target=self.run_script)
		p.start()

		return { 'ok' : not str_to_bool(self.db.get('IS_HUNG_UP')) }

	def on_hang_up(self):
		logging.info("hanging up")
		self.send_command({ 'stop_audio' : True })
		stop_daemon(self.conf['d_files']['module'])
		self.db.set('IS_HUNG_UP', True)

		try:
			current_record_pid = self.db.get("CURRENT_RECORD_PID")
			if current_record_pid is not None:
				logging.debug("current_record_pid: %s" % current_record_pid)
				os.kill(int(current_record_pid), signal.SIGKILL)
				self.db.delete("CURRENT_RECORD_PID")
			else:
				logging.debug("not currently recording")

		except Exception as e:
			logging.warning("NO CURRENT RECORD TO KILL")
			print e, type(e)

		return { 'ok' : str_to_bool(self.db.get('IS_HUNG_UP')) }

	def get_status(self):
		return { 'ok' : self.get_gpio_status() }

	def run_script(self):
		start_daemon(self.conf['d_files']['module'])

	# necessary?
	def build_key_map(self, route):
		return [c[0] for c in self.key_mappings[route]]

	# necessary?
	def find_next_route(self, route, choice):
		try:
			return [c[1] for c in self.key_mappings[route] if c[0] == choice][0]
		except Exception as e:
			print e, type(e)

		return None

	# necessary?
	def route_loop(self, route):
		logging.info(route)

		choice = self.prompt(os.path.join("prompts", "%s.wav" % route), self.build_key_map(route))
		next_route = self.find_next_route(route, choice)

		if next_route is not None:
			return self.route_loop(next_route)
		
		return False

	def start_api(self):
		"""Starts API, initializes the redis database, and daemonizes all processes so they may be restarted or stopped.
		"""

		self.db.set('MODE', RESPOND_MODE)

		tornado.web.Application.__init__(self, self.routes)
		server = tornado.httpserver.HTTPServer(self)

		try:
			server.bind(self.conf['api_port'])
		except Exception as e:
			import re
			from fabric.api import settings, local
			from fabric.context_managers import hide
			from vars import KILL_RX, NO_KILL_RX

			with settings(hide('everything'), warn_only=True):
				print "killing whatever is on port %d" % self.conf['api_port']
				
				kill_list = local("ps -ef | grep %s.py" % self.conf['rpi_id'], capture=True)
				for k in [k.strip() for k in kill_list.splitlines()]:
					
					for r in NO_KILL_RX:						
						if re.match(r, k) is not None:
							continue

					# TODO: does this work on rpi, too? (should...)
					has_tty = [t for t in k.split(" ") if len(t) != 0][5]
					if re.match(r'pts/\d+', has_tty):
						continue

					pid = re.findall(re.compile(KILL_RX % self.conf['rpi_id']), k)
					if len(pid) == 1 and len(pid[0]) >= 1:
						try:
							pid = int(pid[0])
						except Exception as e:
							continue

					local("kill -9 %d" % pid)

			server.bind(self.conf['api_port'])

		start_daemon(self.conf['d_files']['api'])
		server.start(self.conf['num_processes'])

		tornado.ioloop.IOLoop.instance().start()

	def stop_api(self):
		"""Stops the API.
		"""

		# don't forget to save the redis db
		stop_daemon(self.conf['d_files']['api'])

