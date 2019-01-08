# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def uptostream(self, data):
	url = None
	source = re.findall("<source\ssrc='(.*?)'\stype='video/mp4'", data, re.S)
	if source:
		url = source[0]
		if url[:2] == "//":
			url = "http:" + url
	if url:
		self._callback(url)
	else:
		self.stream_not_found()