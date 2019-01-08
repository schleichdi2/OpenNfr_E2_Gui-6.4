# -*- coding: utf-8 -*-
from imports import *
from Plugins.Extensions.MediaPortal.plugin import _
import requests

class MTVdeLink:

	def __init__(self, session):
		self.session = session
		self._callback = None

	def getLink(self, cb_play, cb_err, title, artist, token, imgurl):
		self._callback = cb_play
		self._errback = cb_err
		self.title = title
		self.artist = artist
		self.imgurl = imgurl
		if "&token=" in token:
			token2 = token.split('&token=')[-1]
			token = token.split('&token=')[0]
		else:
			token2 = None
		if token.startswith('http'):
			token = self.getToken(token)
		if not token and token2:
			token = token2
		if not token:
			self._errback(_('Sorry, this video is not found or no longer available due to date or rights restrictions.'))
		else:
			if config_mp.mediaportal.mtvquality.value == "SD":
				quality = "phttp"
			else:
				quality = "hls"
			url = "http://media-utils.mtvnservices.com/services/MediaGenerator/mgid:arc:video:mtv.de:%s?accountOverride=esperanto.mtvi.com&acceptMethods=%s" % (token, quality)
			getPage(url, timeout=5).addCallback(self._parseData).addErrback(cb_err)

	def getToken(self, url):
		s = requests.session()
		try:
			page = s.get(url, timeout=15)
			try:
				token = re.findall('"itemId":"(.*?)"', page.content, re.S)[0]
			except:
				tokendata = re.findall('data-mtv-id="(.*?)"', page.content, re.S)
				if tokendata:
					token = tokendata[0]
				else:
					token = None
			return token
		except:
			token = None

	def _parseData(self, data):
		hlsurl = re.findall('<src>(.*?)</src>', data)
		if hlsurl:
			videourl = hlsurl[-1].replace('&amp;','&')
		else:
			if "geo_block" in data:
				self._errback(_('Sorry, this video is not available in your region.'))
				videourl = None
			if "not_found" in data:
				self._errback(_('Sorry, this video is not found or no longer available due to date or rights restrictions.'))
				videourl = None
			else:
				self._errback(_('No URL found!'))
				videourl = None

		self._callback(self.title, videourl, imgurl=self.imgurl, artist=self.artist)