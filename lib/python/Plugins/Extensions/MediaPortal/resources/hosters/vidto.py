# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def vidto(self, data):
		stream_url = re.search('file:"(.*?)"', data, re.S)
		if stream_url:
			stream_url.group(1)
			self._callback(stream_url.group(1))
		else:
			self.stream_not_found()