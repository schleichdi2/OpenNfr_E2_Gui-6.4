# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def rapidvideocom(self, data):
	url = re.findall('source\ssrc="(.*?)"', data, re.S)
	if url:
		self._callback(url[-1])
		return
	self.stream_not_found()