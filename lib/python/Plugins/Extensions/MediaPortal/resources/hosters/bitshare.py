# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt

def bitshare(self, data):
	stream_url = re.findall('(url: |src=)\'(.*?.avi|.*?.mp4)\'', data)
	if stream_url:
		link = stream_url[0][1]
		reactor.callLater(6, self.bitshare_start, link)
		self.session.open(MessageBoxExt, _("Stream starts in 6 sec."), MessageBoxExt.TYPE_INFO, timeout=6)
	else:
		self.stream_not_found()

def bitshare_start(self, url):
	self._callback(url)