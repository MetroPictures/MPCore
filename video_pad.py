import pygame, logging
from time import time, sleep

class MPVideoPad():
	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['vp']['log'], level=logging.DEBUG)

	def start_video_pad(self):
		pygame.init()
		clock = pygame.time.Clock()

		self.vp_setup()
		logging.info("VideoPad launched.")

		while True:
			self.vp_draw()
			clock.tick(60)
		
	def vp_setup(self): 
		self.screen = pygame.display.set_mode(self.conf['video_pad']['screen_size'])

	def vp_draw(self):
		pygame.display.flip()