# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def exashare(self, data):
	stream_url = None
	stream_url = re.findall('file:\s"(.*?)"', data)
	if stream_url:
		stream_url = stream_url[0]
		self._callback(stream_url)
	else:
		self.stream_not_found()