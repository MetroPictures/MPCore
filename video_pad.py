import os, logging, tornado.web
from fabric.api import settings, local

from multiprocessing import Process
from utils import start_daemon, stop_daemon

class MPVideoPad(object):
	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['vid']['log'])

		# add video pad to routes
		self.routes.extend([
			(r'/video', self.VideoHandler),
			(r'/video/js/(.*)', tornado.web.StaticFileHandler, \
				{ 'path' : os.path.join(self.conf['media_dir'], "video", "js")}),
			(r'/video/viz/(.*)', tornado.web.StaticFileHandler, \
				{ 'path' : os.path.join(self.conf['media_dir'], "video", "viz")})
		])

	def start_video_pad(self):
		# not sure if we're doing anything here...
		return True

	def play_video(self, video):
		p = Process(target=self.omxplayer, args=(video,))
		p.start()

	def stop_video(self):
		logging.debug("stopping video")

	def omxplayer(self, video):
		with settings(warn_only=True):
			omx = local("omxplayer %s" % os.path.join(self.conf['media_dir'], "video", "viz", video))
			dir(omx)

	class VideoHandler(tornado.web.RequestHandler):
		def get(self):
			self.render(os.path.join(self.application.conf['media_dir'], "video", "index.html"))