import os, re, json, logging
from fabric.api import settings, local
from fabric.context_managers import hide
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Process, Queue
from time import sleep, time

from utils import start_daemon, stop_daemon, time_str_to_millis, millis_to_time_str
from vars import BASE_DIR, MAX_VIDEO_VOLUME, MIN_VIDEO_VOLUME

MUTE_THRESHOLD = 10

class MPVideoPad(object):
	OMX_CMD = {
		'setup' : "omxplayer -I --no-osd -o local %s < %s",
		'exe' : "echo -n %s > %s"
	}

	DBUS_CMD = {
		'exe' : os.path.join(BASE_DIR, "core", "lib", "dbuscontrol.sh")
	}

	class VideoMappingTemplate():
		def __init__(self, video, log_path, index=0):
			self.src = video
			self.index = index
			self.fifo = os.path.join(BASE_DIR, ".monitor", "omxplayer_%d.fifo" % self.index)
			self.d_files = {
				'log' : log_path,
				'pid' : os.path.join(BASE_DIR, ".monitor", "omxplayer_%d.pid.txt" % self.index)
			}

	def __init__(self):
		logging.basicConfig(filename=self.conf['d_files']['vid']['log'])
		self.video_mappings = []

		for root, _, files in os.walk(os.path.join(BASE_DIR, "media", "video", "viz")):
			for v, video in enumerate([v for v in files if re.match(r'.*\.mp4$', v)]):
				video_mapping = self.VideoMappingTemplate(os.path.join(root, video), \
					self.conf['d_files']['vid']['log'], v)
				
				self.video_mappings.append(video_mapping)
			
			break

	def get_video_mapping_by_filename(self, video):
		try:
			return [vm for vm in self.video_mappings if \
				re.match(re.compile(".*/%s$" % video), vm.src)][0]
		except Exception as e:
			logging.error("No video found for %s" % video)
		
		return None

	def get_video_info(self, index):
		try:
			return json.loads(self.db.get("video_%d" % index))
		except Exception as e:
			logging.error("NO INFO FOR VIDEO %d" % index)

		return None

	def start_video_pad(self):
		return True

	def stop_video_pad(self):
		with settings(hide('everything'), warn_only=True):
			for omx_pid in self.get_omx_instances():
				local("kill -9 %d" % omx_pid)

			for video_mapping in self.video_mappings:
				local("rm %s" % video_mapping.fifo)

		return True

	def get_omx_instances(self, video=None):
		omx_pids = []
		
		with settings(hide('everything'), warn_only=True):
			omx_instances = local("ps ax | grep -v grep | grep omxplayer", capture=True)
			
			if not omx_instances.succeeded:
				return omx_pids

			for line in omx_instances.split('\n'):
				if video is not None and not re.match(video, line.strip()):
					print "SKIPPING THIS BECAUSE IT DOES NOT CONCERN VIDEO"
					continue
				
				try:
					omx_pids.append(int(re.findall(r'(\d+)\s.*', line)[0]))
				except Exception as e:
					print "OOPS"
					print e, type(e)
					continue

		return omx_pids

	def stop_video(self, video=None, video_callback=None):
		with settings(warn_only=True):
			for omx_pid in self.get_omx_instances():
				local("kill -9 %d" % omx_pid)

			for video_mapping in self.video_mappings:
				local("rm %s" % video_mapping.fifo)


		logging.debug("stopping video #%d (%s)" % (video_mapping.index, video_mapping.src))

		if video_callback is not None:
			video_callback({'index' : video_mapping.index, 'info' : {'stopped' : True}})

		return True

	def play_video(self, video, with_extras=None, video_callback=None):
		video_mapping = self.get_video_mapping_by_filename(video)

		# make fifo
		with settings(warn_only=True):
			if os.path.exists(video_mapping.fifo):
				local("rm %s" % video_mapping.fifo)

			local("mkfifo %s" % video_mapping.fifo)

		p = Process(target=self.setup_video, args=(video_mapping, with_extras, video_callback))
		p.start()
		
		# set playing
		with settings(hide('everything'), warn_only=True):
			local(self.OMX_CMD['exe'] % ('p', video_mapping.fifo))
			local(self.OMX_CMD['exe'] % ('p', video_mapping.fifo))
			start_time = time()

		if video_callback is not None:
			info = {'start_time' : start_time}
			
			if with_extras is not None:
				info['with_extras'] = with_extras

			video_callback({'index' : video_mapping.index, 'info' : info})

		return True

	def setup_video(self, video_mapping, with_extras=None, video_callback=None):
		logging.debug("setting up video #%d (%s)" % (video_mapping.index, video_mapping.src))
		
		# load video into omxplayer on fifo. this will block.
		start_daemon(video_mapping.d_files)
		
		setup_cmd = self.OMX_CMD['setup']
		if with_extras is not None:
			setup_cmd = setup_cmd.replace("-I", "-I %s " % " ".join(\
				["--%s %s" % (e, with_extras[e]) for e in with_extras.keys()]))

		logging.debug("setup command: %s" % setup_cmd)

		p = Popen(setup_cmd % (video_mapping.src, video_mapping.fifo), \
			shell=True, stdout=PIPE, stderr=STDOUT)

		while True:
			duration_line = re.findall(r'Duration\:\s+(.*),.*', p.stdout.readline())
			if len(duration_line) == 1:
				duration_str = duration_line[0].split(",")[0]
				duration = {
					'millis' : time_str_to_millis(duration_str),
					'str' : duration_str
				}

				if video_callback is not None:
					video_callback({'index' : video_mapping.index, \
						'info' : {'duration' : duration}})

				break

		stop_daemon(video_mapping.d_files)		
	
	def pause_video(self, video=None, unpause=False, video_callback=None):
		if video is None:
			video_mapping = self.video_mappings[0]
		else:
			video_mapping = self.get_video_mapping_by_filename(video)
			if video_mapping is None:
				logging.error("NO VIDEEO %s TO PLAY/PAUSE!" % video)
				return False

		logging.debug("play/pausing video #%d (%s)" % (video_mapping.index, video_mapping.src))

		with settings(hide('everything'), warn_only=True):
			pause_time = time()
			local(self.OMX_CMD['exe'] % ('p', video_mapping.fifo))

			if video_callback is not None:
				info = {}
				
				if not unpause:
					old_info = self.get_video_info(video_mapping.index)					
					info['last_pause_time'] = pause_time
					
					status = local("%s status" % self.DBUS_CMD['exe'], capture=True)
					
					if not status.succeeded:
						logging.error("COULD NOT GET DBUS STATUS")
						return False

					info['position_at_last_pause'] = int(status.splitlines()[1].split(":")[1].strip())

				else:
					info['start_time'] = pause_time

				video_callback({'index' : video_mapping.index, 'info' : info})

		return True

	def unpause_video(self, video=None, video_callback=None):
		logging.debug("unpausing video")

		return self.pause_video(video=video, unpause=True, video_callback=video_callback)

	def mute_video(self, video=None, video_callback=None, unmute=False):
		if video is None:
			video_mapping = self.video_mappings[0]
		else:
			video_mapping = self.get_video_mapping_by_filename(video)
			if video_mapping is None:
				logging.error("NO VIDEEO %s TO MUTE!" % video)
				return False

		logging.debug("muting video")
		
		
		#this sucks.

		def get_vol():
			with settings(warn_only=True):
				volume = local("%s volume" % self.DBUS_CMD['exe'], capture=True)
				
				if not volume.succeeded:
					print "COULD NOT GET VOLUME FROM DBUS"
					return False

				return float(volume.split(":")[1].strip())

		threshold = MAX_VIDEO_VOLUME if unmute else MIN_VIDEO_VOLUME

		while True:
			volume = get_vol()
			print "CURRENT VOLUME: %f" % volume
			
			if unmute and volume >= MAX_VIDEO_VOLUME:
				print "UNMUTING DONE!"
				break

			if not unmute and volume <= MIN_VIDEO_VOLUME:
				print "MUTING DONE!"
				break

			local(self.OMX_CMD['exe'] %('+' if unmute else '-', video_mapping.fifo))
			sleep(0.01)

		if video_callback is not None:
			video_callback({'index' : video_mapping.index, 'info' : {'muted' : not unmute }})

		return True

	def unmute_video(self, video=None, video_callback=None):
		logging.debug("unmuting video")

		return self.mute_video(video=video, video_callback=video_callback, unmute=True)

