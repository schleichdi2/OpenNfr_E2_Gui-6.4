# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def mailru(self, data, ck):
	stream_url = None
	js_data = json.loads(data)
	best_quality = 0
	for video in js_data['videos']:
		if int(video['key'][:-1]) > best_quality:
			stream_url = str(video['url'])
			if stream_url.startswith('//'):
				stream_url = "https:" + stream_url
			best_quality = int(video['key'][:-1])
	if stream_url:
		headers = '&Cookie=%s' % ','.join(['%s=%s' % (key, urllib.quote_plus(ck[key])) for key in ck])
		url = stream_url + '#User-Agent='+mp_globals.player_agent+headers
		self._callback(url)
	else:
		self.stream_not_found()