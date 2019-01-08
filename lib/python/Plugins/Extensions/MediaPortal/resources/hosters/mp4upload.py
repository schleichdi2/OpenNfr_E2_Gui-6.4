# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def mp4upload(self, data):
	stream_url = re.search("'file':\s'(.*?)'", data)
	if stream_url:
		self._callback(stream_url.group(1))
	else:
		self.stream_not_found()