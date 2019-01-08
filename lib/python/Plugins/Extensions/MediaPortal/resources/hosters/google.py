# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def google(self, data):
	self.VIDEO_FMT_PRIORITY_MAP = {
		'37' : 1, #MP4 1080p
		'22' : 2, #MP4 720p
		'59' : 3, #MP4 480p
		'18' : 4, #MP4 360p
	}

	links = {}
	stream_urls = re.findall('(\d+)\|(http.*?)[,|"\]]', data, re.S)
	if stream_urls:
		for x in stream_urls:
			try:
				links[self.VIDEO_FMT_PRIORITY_MAP[x[0]]] = x[1]
			except KeyError:
				continue

		stream_url = links[sorted(links.iterkeys())[0]].encode('utf-8')

		headers = '&Cookie=%s' % ','.join(['%s=%s' % (key, urllib.quote_plus(self.google_ck[key])) for key in self.google_ck])
		url = stream_url.replace("\u003d","=").replace("\u0026","&") + '#User-Agent='+mp_globals.player_agent+headers
		self._callback(url)
	else:
		self.stream_not_found()