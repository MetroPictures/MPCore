import os, logging, tornado.web

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
		return False

	class VideoHandler(tornado.web.RequestHandler):
		def get(self):
			self.render(os.path.join(self.application.conf['media_dir'], "video", "index.html"))