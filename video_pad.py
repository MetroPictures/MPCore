import os, re, logging, tornado.web
from fabric.api import settings, local
from fabric.context_managers import hide
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Process
from copy import deepcopy
from time import sleep

from utils import start_daemon, stop_daemon
from vars import BASE_DIR

class MPVideoPad(object):
	OMX_CMD = {
		'setup' : "omxplayer -I --no-osd -o local %s < %s",
		'exe' : "echo -n %s > %s"
	}

	class VideoMappingTemplate(object):
		def __init__(self, video, log_path, index=0):
			self.src = video
			self.index = index
			self.fifo = os.path.join(BASE_DIR, ".monitor", "omxplayer_%d.fifo" % self.index)
			self.d_files = {
				'log' : log_path,
				'pid' : os.path.join(BASE_DIR, ".monitor", "omxplayer_%d.pid.txt" % self.index)
			}
			self.duration = {}

		def set_duration(self, duration):
			self.duration = duration

	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['vid']['log'])
		self.video_mappings = []

		for root, _, files in os.walk(os.path.join(BASE_DIR, "media", "video", "viz")):
			for v, video in enumerate([v for v in files if re.match(r'.*\.mp4$', v)]):
				video_mapping = self.VideoMappingTemplate(os.path.join(root, video), \
					self.conf['d_files']['vid']['log'], v)
				
				self.video_mappings.append(video_mapping)
			
			break

		# add video pad to routes
		self.routes.extend([
			(r'/video', self.VideoHandler),
			(r'/video/js/(.*)', tornado.web.StaticFileHandler, \
				{ 'path' : os.path.join(self.conf['media_dir'], "video", "js")}),
			(r'/video/viz/(.*)', tornado.web.StaticFileHandler, \
				{ 'path' : os.path.join(self.conf['media_dir'], "video", "viz")})
		])

	def get_video_mapping_by_filename(self, video):
		try:
			return [vm for vm in self.video_mappings if \
				re.match(re.compile(".*/%s$" % video), vm.src)][0]
		except Exception as e:
			logging.error("No video found for %s" % video)
		
		return None


	def start_video_pad(self):
		return True

	def stop_video_pad(self):
		with settings(hide('everything'), warn_only=True):
			omx_instances = local("ps ax | grep -v grep | grep omxplayer", capture=True)
			if omx_instances.succeeded:
				for line in omx_instances.split('\n'):
					try:
						omx_pid = re.findall(r'(\d+)\s.*', line)[0]
					except Exception as e:
						continue

					local("kill -9 %d" % int(omx_pid))

			for video_mapping in self.video_mappings:
				stop_daemon(video_mapping.d_files)
				local("rm %s" % video_mapping.fifo)

		return True

	def play_video(self, video):
		video_mapping = self.get_video_mapping_by_filename(video)

		# make fifo
		with settings(warn_only=True):
			if os.path.exists(video_mapping.fifo):
				local("rm %s" % video_mapping.fifo)

			local("mkfifo %s" % video_mapping.fifo)

		p = Process(target=self.setup_video, args=(video_mapping,))
		p.start()

		# set playing
		with settings(warn_only=True):
			local(self.OMX_CMD['exe'] % ('p', video_mapping.fifo))
			sleep(0.5)
			local(self.OMX_CMD['exe'] % ('p', video_mapping.fifo))

		return True

	def setup_video(self, video_mapping):
		logging.debug("setting up video #%d (%s)" % (video_mapping.index, video_mapping.src))
		
		# load video into omxplayer on fifo. this will block.
		start_daemon(video_mapping.d_files)
		p = Popen(self.OMX_CMD['setup'] % (video_mapping.src, video_mapping.fifo), \
			shell=True, stdout=PIPE, stderr=STDOUT)

		while True:
			duration_line = re.findall(r'Duration\:\s+(.*),.*', p.stdout.readline())
			if len(duration_line) == 1:
				duration_str = duration_line[0].split(",")[0]
				d = duration_str.split(":")
				
				dh = (int(d[0]) * 60 * 60) * 1000
				dm = (int(d[1]) * 60) * 1000
				ds = (float(d[2])) * 1000

				self.video_mappings[video_mapping.index].set_duration({
					'str' : duration_str,
					'millis' : dh + dm + ds
				})

	def pause_video(self, video=None):
		if video is None:
			video_mapping = self.video_mappings[0]
		else:
			video_mapping = self.get_video_mapping_by_filename(video)
			if video_mapping is None:
				logging.err("NO VIDEEO %s TO PLAY/PAUSE!" % video)
				return False

		logging.debug("play/pausing video #%d (%s)" % (video_mapping.index, video_mapping.src))

		with settings(warn_only=True):
			local(self.OMX_CMD['exe'] % ('p', video_mapping.fifo))

		return True

	def unpause_video(self, video=None):
		logging.debug("unpausing video")

		return self.pause_video(video=video)

	class VideoHandler(tornado.web.RequestHandler):
		def get(self):
			self.render(os.path.join(self.application.conf['media_dir'], "video", "index.html"))



