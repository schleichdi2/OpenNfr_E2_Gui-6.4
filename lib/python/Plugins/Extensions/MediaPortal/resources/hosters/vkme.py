# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def vkme(self, data, link):
	stream_urls = re.findall('url[0-9]+=(http(s)?://.*?.vk.me/.*?/videos/.*?[0-9]+.mp4)', data)
	if stream_urls:
		stream_url = stream_urls[-1][0]
		self._callback(stream_url)
		return
	else:
		stream_urls = re.findall('url[0-9]+\\\\":\\\\"(http(s)?:.*?/videos.*?[0-9]+.mp4)', data)
		if stream_urls:
			stream_url = stream_urls[-1][0].replace('\\','')
			self._callback(stream_url)
			return
		else:
			stream_urls = re.findall('"url[0-9]+":"(http(s)?:.*?videos.*?)"', data)
			if stream_urls:
				self._callback(stream_urls[-1][0].replace("\/","/"))
				return
			else:
				stream_urls = re.findall('"mp4_[0-9]+":"(http(s)?:.*?extra.*?)"', data)
				if stream_urls:
					self._callback(stream_urls[-1][0].replace("\/","/"))
					return

	oid = re.search('oid=(.*?)&', link, re.S)
	video_id = re.search('&id=(.*?)&', link, re.S)
	hash = re.search('&hash=(.*?)[$|&|"|\']', link, re.S)
	if not oid:
		oid = re.search('video=(.*?)_', link, re.S)
		video_id = re.search('video=.*?_(.*?)$', link, re.S)
	if oid and video_id:
		if hash:
			self.vkmeHashGet(oid.group(1), video_id.group(1), hash.group(1))
		else:
			url = 'http://vk.com/al_video.php?act=show_inline&al=1&video=%s_%s' % (oid.group(1), video_id.group(1))
			twAgentGetPage(url).addCallback(self.vkmeHash, oid.group(1), video_id.group(1)).addErrback(self.errorload)
	else:
		self.stream_not_found()

def vkmeHash(self, data, oid, video_id):
	data = data.replace('\'', '"').replace(' ', '')
	data = re.sub(r'[^\x00-\x7F]+', ' ', data)
	match = re.search('"hash2"\s*:\s*"(.+?)"', data)
	if match:
		self.vkmeHashGet(oid, video_id, match.group(1))
	else:
		match = re.search('"hash"\s*:\s*"(.+?)"', data)
		if match:
			self.vkmeHashGet(oid, video_id, match.group(1))
		else:
			self.stream_not_found()

def vkmeHashGet(self, oid, video_id, hash):
	url = 'http://api.vk.com/method/video.getEmbed?oid=%s&video_id=%s&embed_hash=%s' % (oid, video_id, hash)
	twAgentGetPage(url).addCallback(self.vkmeHashData, oid, video_id, hash).addErrback(self.errorload)

def vkmeHashData(self, data, oid, video_id, hash):
	data = re.sub(r'[^\x00-\x7F]+', ' ', data)
	try:
		self.vkPrivatData(json.loads(data)['response'])
	except:
		url = 'http://vk.com/al_video.php?act=show_inline&al=1&video=%s_%s' % (oid, video_id)
		twAgentGetPage(url).addCallback(self.vkPrivat).addErrback(self.errorload)

def vkPrivat(self, data):
	data = re.sub(r'[^\x00-\x7F]+', ' ', data)
	match = re.search('var\s+vars\s*=\s*({.+?});', data)
	try:
		self.vkPrivatData(json.loads(match.group(1)))
	except:
		self.stream_not_found()

def vkPrivatData(self, data):
	quality_list = []
	link_list = []
	best_link = ''
	for quality in ['url240', 'url360', 'url480', 'url540', 'url720']:
		if quality in data:
			quality_list.append(quality[3:])
			link_list.append(data[quality])
			best_link = data[quality]
	if best_link:
		self._callback(best_link.encode("utf-8"))
	else:
		self.stream_not_found()