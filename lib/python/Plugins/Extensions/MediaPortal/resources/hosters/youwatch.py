# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def youwatch(self, data):
	url = re.findall('<iframe src="(.*?)"', data, re.S)
	if url:
		url =  url[0].replace('\n', '').replace('\r', '')
		getPage(url, headers={'referer': url, 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.youwatchLink).addErrback(self.errorload)
		return
	self.stream_not_found()

def youwatchLink(self, data):
	stream_url = re.findall('sources:\s+\[\{file:\s*["|\'](.*?)["|\']', data)
	if stream_url:
		self._callback(stream_url[0])
	else:
		self.stream_not_found()