# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def kissmovies(self, data):
	print data
	stream_url = re.findall('[\'|\"]file[\'|\"]:\s{0,1}[\'|\"](.*?)[\'|\"]', data, re.S)
	if stream_url:
		url = str(stream_url[-1]).replace('\/','/')
		if url.startswith('/api'):
			url = "https://kissmovies.cc" + url
		self._callback(url)
	else:
		self.stream_not_found()