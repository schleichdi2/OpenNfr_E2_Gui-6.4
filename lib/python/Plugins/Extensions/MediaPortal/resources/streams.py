# -*- coding: utf-8 -*-
##############################################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2018
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding execution on hardware, you are permitted to execute this plugin on VU+ hardware
#  which is licensed by satco europe GmbH, if the VTi image is used on that hardware.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
##############################################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from imports import *
import mp_globals
from jsunpacker import cJsUnpacker
from debuglog import printlog as printl
from messageboxext import MessageBoxExt
from realdebrid import realdebrid_oauth2

try:
	import requests
except:
	requestsModule = False
else:
	requestsModule = True

ck = {}

def isSupportedHoster(linkOrHoster, check=False):
	if not check:
		return False
	if not linkOrHoster:
		return False

	printl("check hoster: %s" % linkOrHoster,'',"S")

	host = linkOrHoster.lower().strip()
	if re.search(mp_globals.hosters[0], host):
		printl("match1: %s" % linkOrHoster,'',"H")
		return True
	elif re.search(mp_globals.hosters[1], host):
		printl("match2: %s" % linkOrHoster,'',"H")
		return True

	printl("hoster not supported",'',"H")
	return False

class get_stream_link:

	# hosters
	from hosters.bestreams import bestreams, bestreamsCalllater, bestreamsPostData
	from hosters.bitshare import bitshare, bitshare_start
	from hosters.clipwatching import clipwatching
	from hosters.datoporn import datoporn
	from hosters.epornik import epornik
	from hosters.exashare import exashare
	from hosters.fembed import fembed
	from hosters.flashx import flashx
	from hosters.flyflv import flyflv, flyflvData
	from hosters.google import google
	from hosters.gounlimited import gounlimited
	from hosters.kodik import kodik, kodikData
	from hosters.mailru import mailru
	from hosters.mega3x import mega3x
	from hosters.mp4upload import mp4upload
	from hosters.okru import okru
	from hosters.openload import openload
	from hosters.powvideo import powvideo
	from hosters.rapidvideocom import rapidvideocom
	from hosters.streamango import streamango
	from hosters.thevideome import thevideome
	from hosters.uptostream import uptostream
	from hosters.userporn import Userporn
	from hosters.vidcloud import vidcloud
	from hosters.videowood import videowood
	from hosters.vidlox import vidlox
	from hosters.vidoza import vidoza
	from hosters.vidspot import vidspot
	from hosters.vidto import vidto
	from hosters.vidup import vidup, vidup_thief
	from hosters.vidwoot import vidwoot
	from hosters.vidzi import vidzi
	from hosters.vivo import vivo
	from hosters.vkme import vkme, vkmeHash, vkmeHashGet, vkmeHashData, vkPrivat, vkPrivatData
	from hosters.xdrive import xdrive
	from hosters.yourupload import yourupload
	from hosters.youwatch import youwatch, youwatchLink

	def __init__(self, session):
		self._callback = None
		self.session = session
		useProxy = config_mp.mediaportal.premiumize_use.value
		self.puser = config_mp.mediaportal.premiumize_username.value
		self.ppass = config_mp.mediaportal.premiumize_password.value
		self.papiurl = "https://api.premiumize.me/pm-api/v1.php?method=directdownloadlink&params[login]=%s&params[pass]=%s&params[link]=" % (self.puser, self.ppass)
		self.rdb = 0
		self.prz = 0
		self.fallback = False

	def grabpage(self, pageurl, method='GET', postdata={}):
		if requestsModule:
			try:
				import urlparse
				s = requests.session()
				url = urlparse.urlparse(pageurl)
				if method == 'GET':
					page = s.get(url.geturl(), timeout=15)
				elif method == 'POST':
					page = s.post(url.geturl(), data=postdata, timeout=15)
				return page.content
			except:
				return "error"
		else:
			return "error"

	def callPremium(self, link):
		if self.prz == 1 and config_mp.mediaportal.premiumize_use.value:
			r_getPage(self.papiurl+link).addCallback(self.papiCallback, link).addErrback(self.errorload)
		elif self.rdb == 1 and config_mp.mediaportal.realdebrid_use.value:
			self.session.openWithCallback(self.rapiCallback, realdebrid_oauth2, str(link))

	def callPremiumYT(self, link, val):
		if val == "prz":
			r_getPage(self.papiurl+link).addCallback(self.papiCallback, link).addErrback(self.errorload)
		if val == "rdb":
			self.session.openWithCallback(self.rapiCallback, realdebrid_oauth2, str(link))

	def rapiCallback(self, stream_url, link):
		if stream_url:
				mp_globals.realdebrid = True
				mp_globals.premiumize = False
				self._callback(stream_url)
		elif self.prz == 1 and config_mp.mediaportal.premiumize_use.value:
			self.rdb = 0
			r_getPage(self.papiurl+link).addCallback(self.papiCallback, link).addErrback(self.errorload)
		else:
			self.fallback = True
			self.check_link(self.link, self._callback)

	def papiCallback(self, data, link):
		if re.search('status":200', data):
			stream_url = re.findall('"stream_location":"(.*?)"', data, re.S|re.I)
			if not stream_url:
				stream_url = re.findall('"location":"(.*?)"', data, re.S|re.I)
			if stream_url:
				if "&sig=" in stream_url[0]:
					url = stream_url[0].split('&sig=')
					file = url[1].split('&f=')
					url = url[0] + "&sig=" + file[0].replace('%2F','%252F').replace('%3D','%253D').replace('%2B','%252B') + "&f=" + file[1]
				else:
					url = stream_url[0]
				mp_globals.premiumize = True
				mp_globals.realdebrid = False
				self._callback(url.replace('\\',''))
			else:
				self.fallback = True
				self.check_link(self.link, self._callback)
		elif self.rdb == 1 and config_mp.mediaportal.realdebrid_use.value:
			self.prz = 0
			self.session.openWithCallback(self.rapiCallback, realdebrid_oauth2, str(link))
		else:
			if re.search('status":400', data):
				self.session.openWithCallback(self.papiCallback2, MessageBoxExt, _("premiumize: No valid link."), MessageBoxExt.TYPE_INFO, timeout=3)
			elif re.search('status":401', data):
				self.session.openWithCallback(self.papiCallback2, MessageBoxExt, _("premiumize: Login failed."), MessageBoxExt.TYPE_INFO, timeout=3)
			elif re.search('status":402', data):
				self.session.openWithCallback(self.papiCallback2, MessageBoxExt, _("premiumize: You are no Premium-User."), MessageBoxExt.TYPE_INFO, timeout=3)
			elif re.search('status":403', data):
				self.session.openWithCallback(self.papiCallback2, MessageBoxExt, _("premiumize: No Access."), MessageBoxExt.TYPE_INFO, timeout=3)
			elif re.search('status":404', data):
				self.session.openWithCallback(self.papiCallback2, MessageBoxExt, _("premiumize: File not found."), MessageBoxExt.TYPE_INFO, timeout=3)
			elif re.search('status":428', data):
				self.session.openWithCallback(self.papiCallback2, MessageBoxExt, _("premiumize: Hoster currently not available."), MessageBoxExt.TYPE_INFO, timeout=3)
			elif re.search('status":502', data):
				self.session.openWithCallback(self.papiCallback2, MessageBoxExt, _("premiumize: Unknown technical error."), MessageBoxExt.TYPE_INFO, timeout=3)
			elif re.search('status":503', data):
				self.session.openWithCallback(self.papiCallback2, MessageBoxExt, _("premiumize: Temporary technical error."), MessageBoxExt.TYPE_INFO, timeout=3)
			elif re.search('status":509', data):
				self.session.openWithCallback(self.papiCallback2, MessageBoxExt, _("premiumize: Fair use limit exhausted."), MessageBoxExt.TYPE_INFO, timeout=3)
			else:
				self.papiCallback2(True)

	def papiCallback2(self, answer):
		self.fallback = True
		self.check_link(self.link, self._callback)

	def check_link(self, data, got_link):
		self._callback = got_link
		self.link = data
		if data:
			if re.search("http://streamcloud.eu/", data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					link = re.search("(http://streamcloud.eu/\w+)", data, re.S)
					if link:
						link = link.group(1)
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					spezialagent = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
					getPage(link, cookies=ck, agent=spezialagent).addCallback(self.streamcloud).addErrback(self.errorload)

			elif re.search('rapidgator.net|rg.to', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('turbobit.net', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('4shared.com', data, re.S):
				link = data
				if config_mp.mediaportal.realdebrid_use.value and not self.fallback:
					self.rdb = 1
					self.prz = 0
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('vimeo.com', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('uptobox.com', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('filerio.com|filerio.in', data, re.S):
				link = data
				if config_mp.mediaportal.realdebrid_use.value and not self.fallback:
					self.rdb = 1
					self.prz = 0
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('filer.net', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('extmatrix.com', data, re.S):
				link = data
				if config_mp.mediaportal.realdebrid_use.value and not self.fallback:
					self.rdb = 1
					self.prz = 0
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('mediafire.com', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('filefactory.com', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('gigapeta.com', data, re.S):
				link = data
				if config_mp.mediaportal.realdebrid_use.value and not self.fallback:
					self.rdb = 1
					self.prz = 0
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('salefiles.com', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('oboom.com', data, re.S):
				link = data
				if config_mp.mediaportal.realdebrid_use.value and not self.fallback:
					self.rdb = 1
					self.prz = 0
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('uploaded.net|uploaded.to|ul.to', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('youtube.com', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					if config_mp.mediaportal.sp_use_yt_with_proxy.value == "rdb":
						self.callPremiumYT(link, "rdb")
					if config_mp.mediaportal.sp_use_yt_with_proxy.value == "prz":
						self.callPremiumYT(link, "prz")
				else:
					self.only_premium()

			elif re.search('bangbrothers.net', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('brazzers.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('teamskeet.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('naughtyamerica.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('wicked.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('digitalplayground.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('mofos.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('nubilefilms.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('julesjordan.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('kink.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('badoinkvr.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('realitykings.com', data, re.S):
				link = data
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('1fichier.com', data, re.S):
				link = data
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					self.only_premium()

			elif re.search('http://.*?bitshare.com', data, re.S):
				link = data
				getPage(link).addCallback(self.bitshare).addErrback(self.errorload)

			elif re.search('epornik.com', data, re.S):
				link = data
				getPage(link).addCallback(self.epornik).addErrback(self.errorload)

			elif re.search('clipwatching.com', data, re.S):
				link = data
				twAgentGetPage(link).addCallback(self.clipwatching).addErrback(self.errorload)

			elif re.search('vidup.tv', data, re.S):
				link = data
				mp_globals.player_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
				twAgentGetPage(link, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36').addCallback(self.vidup).addErrback(self.errorload)

			elif re.search('fembed.com', data, re.S):
				link = 'http://www.fembed.com/api/source/' + data.split('/v/')[-1]
				mp_globals.player_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
				twAgentGetPage(link, method='POST', agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36', headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.fembed).addErrback(self.errorload)

			elif re.search('flashx.tv|flashx.pw|flashx.co|flashx.to', data, re.S):
				link = data
				id = re.search('flashx.(tv|pw|co|to)/(embed-|dl\?|fxplay-|embed.php\?c=|)(\w+)', data)
				if id:
					link = "https://www.flashx.co/%s.html" % id.group(3)
					if config_mp.mediaportal.premiumize_use.value and not self.fallback:
						self.rdb = 0
						self.prz = 1
						TwAgentHelper().getRedirectedUrl(link).addCallback(self.flashx).addErrback(self.errorload)
					else:
						self.only_premium()
				else:
					self.stream_not_found()

			elif re.search('userporn.com', data, re.S):
				self.userporn_tv(data)

			elif re.search('vk.com|vk.me', data, re.S):
				link = data
				getPage(link).addCallback(self.vkme, link).addErrback(self.errorload)

			elif re.search('http://youwatch.org', data, re.S):
				link = data
				id = link.split('org/')
				url = "http://youwatch.org/embed-%s.html" % id[1]
				getPage(url).addCallback(self.youwatch).addErrback(self.errorload)

			elif re.search('allmyvideos.net', data, re.S):
				link = data
				if re.search('allmyvideos.net/embed', link, re.S):
					getPage(link).addCallback(self.allmyvids).addErrback(self.errorload)
				else:
					id = re.findall('allmyvideos.net/(.*?)$', link)
					if id:
						new_link = "http://allmyvideos.net/embed-%s.html" % id[0]
						getPage(new_link).addCallback(self.allmyvids).addErrback(self.errorload)
					else:
						self.stream_not_found()

			elif re.search("mp4upload.com", data, re.S):
				link = data
				getPage(link).addCallback(self.mp4upload).addErrback(self.errorload)

			elif re.search("mega3x.com|mega3x.net", data, re.S):
				link = data
				getPage(link).addCallback(self.mega3x).addErrback(self.errorload)

			elif re.search("dato.porn|datoporn.co", data, re.S):
				link = data
				getPage(link).addCallback(self.datoporn).addErrback(self.errorload)

			elif re.search("gounlimited.to", data, re.S):
				link = data
				twAgentGetPage(link).addCallback(self.gounlimited).addErrback(self.errorload)

			elif re.search("uptostream.com", data, re.S):
				link = data
				getPage(link).addCallback(self.uptostream).addErrback(self.errorload)

			elif re.search("vidwoot.com", data, re.S):
				link = data
				getPage(link).addCallback(self.vidwoot).addErrback(self.errorload)

			elif re.search("yourupload.com", data, re.S):
				link = data
				getPage(link).addCallback(self.yourupload).addErrback(self.errorload)

			elif re.search("flyflv\.com", data, re.S):
				link = data
				getPage(link).addCallback(self.flyflv).addErrback(self.errorload)

			elif re.search("videowood\.tv", data, re.S):
				link = data
				if re.search('videowood\.tv/embed', data, re.S):
					link = data
				else:
					id = re.search('videowood\.tv/.*?/(\w+)', data)
					if id:
						link = "http://videowood.tv/embed/%s" % id.group(1)
				getPage(link).addCallback(self.videowood).addErrback(self.errorload)

			elif re.search("vivo.sx", data, re.S):
				link = data.replace('http:','https:')
				if mp_globals.isDreamOS or not mp_globals.requests:
					twAgentGetPage(link).addCallback(self.vivo, link).addErrback(self.errorload)
				else:
					data = self.grabpage(link)
					if data == "error":
						message = self.session.open(MessageBoxExt, _("Mandatory Python module python-requests is missing!"), MessageBoxExt.TYPE_ERROR)
					else:
						self.vivo(data, link)

			elif re.search('bestreams\.net/', data, re.S):
				link = data
				getPage(link, cookies=ck, headers={'Accept-Language': 'en-US,en;q=0.5'}).addCallback(self.bestreams, link, ck).addErrback(self.errorload)

			elif re.search('vidto\.me/', data, re.S):
				# http://vidto.me/embed-u1etw7z2o50u-640x360.html
				if re.search('vidto\.me/embed-', data, re.S):
					link = data
				else:
					id = re.search('vidto\.me/(\w+)', data)
					if id:
						link = "http://vidto.me/embed-%s-640x360.html" % id.group(1)
				if config_mp.mediaportal.premiumize_use.value and not self.fallback:
					self.rdb = 0
					self.prz = 1
					self.callPremium(link)
				else:
					ck.update({'referer':'%s' % link })
					getPage(link, cookies=ck).addCallback(self.vidto).addErrback(self.errorload)


			elif re.search('vidoza\.net/', data, re.S):
				link = data.replace('https','http')
				twAgentGetPage(link).addCallback(self.vidoza).addErrback(self.errorload)

			elif re.search('vidspot\.net/', data, re.S):
				if re.search('vidspot\.net/embed', data, re.S):
					link = data
				else:
					id = re.findall('vidspot\.net/(.*?)$', data)
					if id:
						link = "http://vidspot.net/embed-%s.html" % id[0]
				getPage(link).addCallback(self.vidspot).addErrback(self.errorload)

			elif re.search('kodik\.biz/', data, re.S):
				link = data
				getPage(link).addCallback(self.kodik).addErrback(self.errorload)

			elif re.search('(docs|drive)\.google\.com/|youtube\.googleapis\.com|googleusercontent.com', data, re.S):
				if 'youtube.googleapis.com' in data:
					docid = re.search('docid=([\w]+)', data)
					link = 'https://drive.google.com/file/d/%s/edit' % docid.groups(1)
				else:
					link = data
				mp_globals.player_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
				self.google_ck = {}
				if "googleusercontent.com" in link:
					import requests
					s = requests.session()
					try:
						page = s.head(link, allow_redirects=False, timeout=15)
						link = page.headers['Location']
						self.google_ck = requests.utils.dict_from_cookiejar(s.cookies)
						headers = '&Cookie=%s' % ','.join(['%s=%s' % (key, urllib.quote_plus(self.google_ck[key])) for key in self.google_ck])
						url = link.replace("\u003d","=").replace("\u0026","&") + '#User-Agent='+mp_globals.player_agent+headers
						self._callback(url)
					except:
						pass
				else:
					getPage(link, agent=mp_globals.player_agent, cookies=self.google_ck).addCallback(self.google).addErrback(self.errorload)

			elif re.search('rapidvideo\.com', data, re.S):
				link = data.replace('rapidvideo.com/e/', 'rapidvideo.com/v/')
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					id = re.findall('rapidvideo\.com/v/(.*?)$', link)
					if id:
						link = "http://rapidvideo.com/embed/%s" % id[0]
					getPage(link).addCallback(self.rapidvideocom).addErrback(self.errorload)

			elif re.search('openload\.(?:co|io|link)|oload\.(?:tv|stream|site|xyz|win|download|cloud|cc)', data, re.S):
				link = data
				id = re.search('http[s]?://(?:openload\.(?:co|io|link)|oload\.(?:tv|stream|site|xyz|win|download|cloud|cc))\/[^/]+\/(.*?)(\/.*?)?$', link, re.S)
				if id:
					link = 'https://openload.co/embed/' + id.group(1)
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					url = "https://api.openload.co/1/streaming/get?file=" + id.group(1)
					getPage(url).addCallback(self.openload, link).addErrback(self.errorload)

			elif re.search('thevideo\.me|thevideo\.cc', data, re.S):
				if (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value) and not self.fallback:
					if (re.search('thevideo(\.me|\.cc)/embed-', data, re.S) or re.search('640x360.html', data, re.S)):
						id = re.findall('thevideo(?:\.me|\.cc)/(?:embed-|)(.*?)(?:\.html|-\d+x\d+\.html)', data)
						if id:
							link = "https://www.thevideo.me/%s" % id[0]
					else:
						link = data
					self.rdb = 1
					self.prz = 1
					self.callPremium(link)
				else:
					if (re.search('thevideo(\.me|\.cc)/embed-', data, re.S) or re.search('640x360.html', data, re.S)):
						id = re.findall('thevideo(?:\.me|\.cc)/(?:embed-|)(.*?)(?:\.html|-\d+x\d+\.html)', data)
						if id:
							link = "https://thevideo.me/embed-%s-640x360.html" % id[0]
							twAgentGetPage(link, agent='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36').addCallback(self.thevideome).addErrback(self.errorload)

			elif re.search('exashare\.com', data, re.S):
				if re.search('exashare\.com/embed-', data, re.S):
					link = data
				else:
					id = re.findall('exashare\.com/(.*?)$', data)
					if id:
						link = "http://www.exashare.com/embed-%s-620x330.html" % id[0]
				getPage(link).addCallback(self.exashare).addErrback(self.errorload)

			elif re.search('powvideo\.net/', data, re.S):
				id = re.search('powvideo\.net/(embed-|)(\w+)', data)
				if id:
					referer = "http://powvideo.net/embed-%s-954x562.html" % id.group(2)
					link = "http://powvideo.net/iframe-%s-954x562.html" % id.group(2)
					getPage(link, headers={'Referer':referer, 'Accept-Language': 'en-US,en;q=0.5'}).addCallback(self.powvideo).addErrback(self.errorload)

			elif re.search('my\.pcloud\.com', data, re.S):
				getPage(data).addCallback(self.mypcloud).addErrback(self.errorload)

			elif re.search('ok\.ru', data, re.S):
				id = data.split('/')[-1]
				url = "http://www.ok.ru/dk"
				mp_globals.player_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36 OPR/34.0.2036.50'
				dataPost = {'cmd': 'videoPlayerMetadata', 'mid': str(id)}
				getPage(url, method='POST', agent=mp_globals.player_agent, cookies=ck, postdata=urlencode(dataPost), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.okru).addErrback(self.errorload)

			elif re.search('mail\.ru', data, re.S):
				id_raw = re.findall('mail.ru/video/embed/(\d+)$', data)
				if id_raw:
					url = "https://my.mail.ru/+/video/meta/%s" % id_raw[0]
					spezialagent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
					mp_globals.player_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
					kekse = {}
					getPage(url, agent=spezialagent, cookies=kekse).addCallback(self.mailru, kekse).addErrback(self.errorload)
				else:
					self.stream_not_found()

			elif re.search('vidzi\.tv/', data, re.S):
				link = data
				getPage(link, cookies=ck).addCallback(self.vidzi).addErrback(self.errorload)

			elif re.search('vidlox\.tv/', data, re.S):
				if re.search('vidlox\.tv/embed-', data, re.S):
					link = data
				else:
					id = re.search('vidlox\.tv/(\w+)', data)
					if id:
						link = "https://vidlox.tv/embed-%s.html" % id.group(1)
				if mp_globals.isDreamOS or not mp_globals.requests:
					twAgentGetPage(link).addCallback(self.vidlox).addErrback(self.errorload)
				else:
					data = self.grabpage(link)
					if data == "error":
						message = self.session.open(MessageBoxExt, _("Mandatory Python module python-requests is missing!"), MessageBoxExt.TYPE_ERROR)
					else:
						self.vidlox(data)

			elif re.search('vidcloud\.co', data, re.S):
				fid = re.search('vidcloud\.co/embed/(.*?)/', data, re.S)
				if fid:
					link = "https://vidcloud.co/player?fid=%s&page=embed" % fid.group(1)
					agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36 OPR/34.0.2036.50'
					mp_globals.player_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36 OPR/34.0.2036.50'
					twAgentGetPage(link, agent=agent).addCallback(self.vidcloud).addErrback(self.errorload)
				else:
					self.stream_not_found()

			elif re.search('xdrive\.cc', data, re.S):
				link = data.replace('https','http')
				agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36 OPR/34.0.2036.50'
				mp_globals.player_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36 OPR/34.0.2036.50'
				twAgentGetPage(link, agent=agent).addCallback(self.xdrive).addErrback(self.errorload)

			elif re.search('streamango\.com|streamcherry\.com', data, re.S):
				link = data
				spezialagent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
				twAgentGetPage(link, agent=spezialagent).addCallback(self.streamango).addErrback(self.errorload)

			else:
				message = self.session.open(MessageBoxExt, _("No supported Stream Hoster, try another one!"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			message = self.session.open(MessageBoxExt, _("Invalid Stream link, try another Stream Hoster!"), MessageBoxExt.TYPE_INFO, timeout=5)
		self.fallback = False

	def stream_not_found(self):
		message = self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)

	def only_premium(self):
		if not (config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value):
			message = self.session.open(MessageBoxExt, _("This hoster is only working with enabled Premium support."), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			message = self.session.open(MessageBoxExt, _("This Stream link is currently not available via Premium, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)

	def errorload(self, error):
		printl('[streams]: ' + str(error),'','E')
		message = self.session.open(MessageBoxExt, _("Unknown error, check MP logfile."), MessageBoxExt.TYPE_INFO, timeout=5)

##############################################################################################################

	def mypcloud(self, data):
		m = re.search('publink.set_download_link\(\'(.*?)\'\)', data)
		if m and m.group(1):
			self._callback(unquote(m.group(1)))
		else:
			self.stream_not_found()

	def allmyvids(self, data):
		stream_url = re.findall('file"\s:\s"(.*?)",', data)
		if stream_url:
			self._callback(stream_url[0])
		else:
			self.stream_not_found()

	def streamcloud(self, data):
		id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data)
		fname = re.findall('<input type="hidden" name="fname".*?alue="(.*?)">', data)
		if id and fname:
			url = "http://streamcloud.eu/%s" % id[0]
			post_data = urllib.urlencode({'op': 'download1', 'usr_login': '', 'id': id[0], 'fname': fname[0], 'referer': url, 'hash': '', 'imhuman':'Weiter zum Video'})
			reactor.callLater(10, self.streamcloud_getpage, url, post_data)
			message = self.session.open(MessageBoxExt, _("Stream starts in 10 sec."), MessageBoxExt.TYPE_INFO, timeout=10)
		else:
			self.stream_not_found()

	def streamcloud_getpage(self, url, post_data):
		spezialagent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
		getPage(url, method='POST', cookies=ck, agent=spezialagent, postdata=post_data, headers={'Content-Type':'application/x-www-form-urlencoded', 'Referer': url, 'Origin':'http://streamcloud.eu'}).addCallback(self.streamcloud_data, url).addErrback(self.errorload)

	def streamcloud_data(self, data, url):
		stream_url = re.findall('file:\s"(.*?)",', data)
		if stream_url:
			mp_globals.player_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
			headers = '&Referer=' + url
			stream = stream_url[0] + '#User-Agent='+mp_globals.player_agent+headers
			self._callback(stream)
		elif re.search('This video is encoding now', data, re.S):
			self.session.open(MessageBoxExt, _("This video is encoding now. Please check back later."), MessageBoxExt.TYPE_INFO, timeout=10)
		else:
			self.stream_not_found()

	def userporn_tv(self, link):
		fx = self.Userporn()
		stream_url = fx.get_media_url(link)
		if stream_url:
			self._callback(stream_url)
		else:
			self.stream_not_found()