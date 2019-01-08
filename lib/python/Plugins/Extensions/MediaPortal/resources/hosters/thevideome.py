# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt
import requests

def thevideome(self, data):
	if re.search('.*?File was deleted..*?', data):
		self.stream_not_found()
	else:	
		try:
			s = requests.session()
			s.headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36'}
			vet = re.findall("var lets_play_a_game='(.*?)'", data)
			if vet:
				player_url = "https://thevideo.me/vsign/player/"+str(vet[0])
				play_data = s.get(player_url, timeout=15)
				key = re.findall('jwConfig\|(.*?)\|return', play_data.text)
				if key:
					fake_url = re.findall('"file":"(.*?)"\,"label"', data)
					if fake_url:
						stream_url = '%s?direct=true&ua=1&vt=%s#User-Agent=%s' % (str(fake_url[-1]), str(key[0]), 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36')
						self._callback(stream_url)
					else:
						self.stream_not_found()
				else:
					self.stream_not_found()
		except:
			self.stream_not_found()