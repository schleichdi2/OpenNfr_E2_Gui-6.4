# -*- coding: utf-8 -*-

from config import config_mp

class YoutubeLink(object):
	def __init__(self, session):
		self.session = session
		self._callback = None
		self.title = ''
		self.videoPrio = int(config_mp.mediaportal.youtubeprio.value)

	def getLink(self, cb_play, cb_err, title, url, imgurl, album='', artist='', dash=None, fmt_map=None):
		dash = config_mp.mediaportal.youtubeenabledash.value
		self._callback = cb_play
		self.title = title
		self.imgurl = imgurl
		self.artist = artist
		self.album = album
		if config_mp.mediaportal.sp_use_yt_with_proxy.value in ("rdb", "prz"):
			url = "http://www.youtube.com/watch?v=" + url
			from streams import get_stream_link
			get_stream_link(self.session).check_link(url, self.cbYTLink)
		else:
			from yt_url import youtubeUrl
			y = youtubeUrl(self.session)
			y.addErrback(cb_err)
			y.addCallback(self.cbYTLink)
			y.getVideoUrl(url, self.videoPrio, dash=dash, fmt_map=fmt_map)

	def cbYTLink(self, url, suburi=None, buffering=False, proxy=None):
		self._callback(self.title, url, suburi=suburi, imgurl=self.imgurl, album=self.album, artist=self.artist, buffering=buffering, proxy=proxy)