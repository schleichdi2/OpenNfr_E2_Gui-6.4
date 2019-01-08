# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def kodik(self, data):
	get_packedjava = re.findall("<script type=.text.javascript.*?(eval.function.*?)</script>", data, re.S)
	if get_packedjava and detect(get_packedjava[0]):
		sJavascript = get_packedjava[0]
		sUnpacked = unpack(sJavascript)
		if sUnpacked:
			s1 = re.search('var s1="(.*?)"', sUnpacked)
			s2 = re.search('var s2="(.*?)"', sUnpacked)
			s3 = re.search('var s3="(.*?)"', sUnpacked)
			if s1 and s2 and s3:
				url = "http://api.vk.com/method/video.getEmbed?oid=%s&video_id=%s&embed_hash=%s&callback=responseWork" % (s1.group(1), s2.group(1), s3.group(1))
				getPage(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}).addCallback(self.kodikData).addErrback(self.errorload)
	else:
		self.stream_not_found()

def kodikData(self, data):
	stream_url = re.findall('"url(.*?)":"(.*?)"', data)
	if stream_url:
		self._callback(stream_url[-1][1].replace("\/","/"))
	else:
		self.stream_not_found()