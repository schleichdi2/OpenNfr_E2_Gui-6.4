# -*- coding: utf-8 -*-
from imports import *
from debuglog import printlog as printl
from messageboxext import MessageBoxExt
from Plugins.Extensions.MediaPortal.plugin import _
import mechanize

canna_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36"

class CannaLink:
	def __init__(self, session):
		self.session = session
		self._errback = None
		self._callback = None

	def getLink(self, cb_play, cb_err, sc_title, sc_artist, sc_album, url, imgurl, retry=0):
		self._errback = cb_err
		self._callback = cb_play

		stream_url = self.getDLurl(url)
		if stream_url:
			cb_play(sc_title, stream_url, album=sc_album, artist=sc_artist, imgurl=imgurl)
		else:
			if retry < 3:
				retry += 1
				self.getLink(cb_play, cb_err, sc_title, sc_artist, sc_album, url, imgurl, retry)
			else:
				cb_err(_('No URL found!'))

	def getDLurl(self, url):
		try:
			content = self.getUrl(url)
			match = re.findall('flashvars.playlist = \'(.*?)\';', content)
			if match:
				for url in match:
					url = 'http://ua.canna.to/canna/'+url
					content = self.getUrl(url)
					match = re.findall('<location>(.*?)</location>', content)
					if match:
						for url in match:
							req = mechanize.Request('http://ua.canna.to/canna/single.php')
							response = mechanize.urlopen(req)
							url = 'http://ua.canna.to/canna/'+url
							req = mechanize.Request(url)
							req.add_header('User-Agent', canna_agent)
							response = mechanize.urlopen(req)
							response.close()
							code=response.info().getheader('Content-Location')
							url='http://ua.canna.to/canna/avzt/'+code
							return url

		except urllib2.HTTPError, error:
			printl(error,self,"E")
			return False

		except urllib2.URLError, error:
			printl(error.reason,self,"E")
			return False

	def getUrl(self,url):
		req = mechanize.Request(url)
		req.add_header('User-Agent', canna_agent)
		response = mechanize.urlopen(req)
		link = response.read()
		response.close()
		return link