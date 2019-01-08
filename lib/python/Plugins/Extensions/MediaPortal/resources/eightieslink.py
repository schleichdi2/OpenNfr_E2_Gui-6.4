# -*- coding: utf-8 -*-

from imports import *
from Plugins.Extensions.MediaPortal.plugin import _

class EightiesLink:
	def __init__(self, session):
		self.session = session
		self._callback = None
		self._errback = None
		self.baseurl = ''
		self.title = ''
		self.artist = ''
		self.album = ''
		self.imgurl = ''

	def getLink(self, cb_play, cb_err, title, artist, album, url, token, imgurl):
		self._callback = cb_play
		self._errback = cb_err
		self.title = title
		self.artist = artist
		self.album = album
		self.imgurl = imgurl
		self.baseurl = "http://www."+token+".com"

		getPage(url).addCallback(self.getVid).addErrback(cb_err)

	def getVid(self, data):
		stream_url = re.findall('(/vid/.*?.flv)', data, re.S)
		if stream_url:
			stream_url = "%s%s" % (self.baseurl, stream_url[0].replace(' ','%20'))
			if mp_globals.isDreamOS:
				if fileExists("/usr/bin/ffmpeg"):
					BgFileEraser = eBackgroundFileEraser.getInstance()
					self.path = config_mp.mediaportal.storagepath.value
					if os.path.exists(self.path):
						for fn in next(os.walk(self.path))[2]:
							BgFileEraser.erase(os.path.join(self.path,fn))
					self.container=eConsoleAppContainer()
					self.container.appClosed_conn = self.container.appClosed.connect(self.finishedDownload)
					self.random = random.randint(1, 999999)
					self.container.execute("ffmpeg -i %s -vcodec copy -acodec copy %s%s.flv -y -loglevel quiet" % (stream_url, self.path, self.random))
				else:
					self._callback(self.title, stream_url, album=self.album, artist=self.artist, imgurl=self.imgurl)
			else:
				self._callback(self.title, stream_url, album=self.album, artist=self.artist, imgurl=self.imgurl)
		else:
			self._errback(_('No URL found!'))

	def finishedDownload(self, retval):
		self.container.kill()
		self._callback(self.title, 'file://%s%s.flv' % (self.path, self.random), album=self.album, artist=self.artist, imgurl=self.imgurl)