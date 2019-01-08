# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def mega3x(self, data):
	url = None
	get_packedjava = re.findall('>(eval.*?)</script>', data, re.S)
	if get_packedjava:
		sJavascript = get_packedjava[0]
		sUnpacked = unpack(sJavascript)
		if sUnpacked:
			links = re.findall(',"(http.*?.mp4)"', sUnpacked, re.S)
			if links:
				url = links[0]
	if url:
		self._callback(url)
	else:
		self.stream_not_found()