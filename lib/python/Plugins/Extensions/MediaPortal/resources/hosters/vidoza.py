# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def vidoza(self, data):
	stream_url = re.findall('src:\s"(.*?.mp4)"', data, re.S)
	if stream_url:
		self._callback(stream_url[0])
	else:
		self.stream_not_found()