# -*- coding: utf-8 -*-

from messageboxext import MessageBoxExt
import mp_globals
from twagenthelper import TwAgentHelper, twAgentGetPage
from cvevosignalgoextractor import decryptor
from imports import *

headers = {'Accept-Language': 'en-us,en;q=0.5',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0 (Chrome)',
			'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
			'Cookie': 'PREF=f1=50000000&hl=en',
		}

playing = False

class youtubeUrl(object):

  def __init__(self, session):
	global playing
	self.__callBack = None
	self.errBack = None
	self.session = session
	self.error = ""
	self.yt_dwnld_agent = None
	self.useProxy = (config_mp.mediaportal.sp_use_yt_with_proxy.value == 'proxy') and (config_mp.mediaportal.yt_proxy_host.value != 'example_proxy.com!')
	self.initDownloadAgent()
	self.tw_agent_hlp = TwAgentHelper(gzip_decoding=True, followRedirect=True, headers=headers)
	mp_globals.premiumize = self.useProxy
	playing = False

  def initDownloadAgent(self):
	self.proxyurl = None
	if self.useProxy:
		proxyhost = config_mp.mediaportal.yt_proxy_host.value
		proxyport = config_mp.mediaportal.yt_proxy_port.value
		self.puser = config_mp.mediaportal.yt_proxy_username.value
		self.ppass = config_mp.mediaportal.yt_proxy_password.value

		if '/noconnect' in proxyhost:
			proxyhost, option = proxyhost.split('/')[-2:]
		else:
			option = ''
		if not proxyhost.startswith('http'):
			self.proxyurl = 'http://%s:%s/%s' % (proxyhost, proxyport, option)
		else: self.proxyurl = '%s:%s/%s' % (proxyhost, proxyport, option)
	else:
		self.puser = None
		self.ppass = None

	self.yt_dwnld_agent = TwAgentHelper(proxy_url=self.proxyurl, p_user=self.puser, p_pass=self.ppass, gzip_decoding=True, followRedirect=True, headers=headers)

  def addCallback(self, cbFunc):
	self.__callBack = cbFunc

  def addErrback(self, errFunc):
	self.errBack = errFunc

  def dataError(self, error):
	self.error += str(error)
	self.errReturn()

  def errReturn(self, url=None):
	if self.errBack == None:
		self.session.openWithCallback(self.cbYTErr, MessageBoxExt,str(self.error), MessageBoxExt.TYPE_INFO, timeout=10)
	else:
		self.errBack(self.error)

  def cbYTErr(self, res):
	return

  def getVideoUrl(self, url, videoPrio=2, dash=None, fmt_map=None):
	dash = config_mp.mediaportal.youtubeenabledash.value
	# portions of this part is from mtube plugin

	if not self.__callBack:
		self.error = '[YoutubeURL] Error: no callBack set'
		self.errReturn()

	if fmt_map != None:
		self.VIDEO_FMT_PRIORITY_MAP = fmt_map
	elif videoPrio == 0: #360p
		self.VIDEO_FMT_PRIORITY_MAP = {
			'18'  : 1, #MP4 360p
			'34'  : 2, #FLV 360p
		}
	elif videoPrio == 1: #480p
		self.VIDEO_FMT_PRIORITY_MAP = {
			'35'  : 1, #FLV 480p
			'18'  : 3, #MP4 360p
			'34'  : 4, #FLV 360p
		}
		if config_mp.mediaportal.youtubeenabledash480p.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'135' : 2, #MP4 480p (DASH)
			})
	elif videoPrio == 2: #720p
		self.VIDEO_FMT_PRIORITY_MAP = {
			'22'  : 1, #MP4 720p
			'35'  : 3, #FLV 480p
			'18'  : 5, #MP4 360p
			'34'  : 6, #FLV 360p
		}
		if config_mp.mediaportal.youtubeenabledash480p.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'135' : 4, #MP4 480p (DASH)
			})
		if config_mp.mediaportal.youtubeenabledash720p.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'136' : 2, #MP4 720p (DASH)
			})
	elif videoPrio == 3: #1080p
		self.VIDEO_FMT_PRIORITY_MAP = {
			'299' : 3, #MP4 1080p60 (DASH)
			'137' : 4, #MP4 1080p (DASH)
			'22'  : 5, #MP4 720p
			'35'  : 7, #FLV 480p
			'18'  : 9, #MP4 360p
			'34'  : 10, #FLV 360p
		}
		if config_mp.mediaportal.youtubeenabledash480p.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'135' : 8, #MP4 480p (DASH)
			})
		if config_mp.mediaportal.youtubeenabledash720p.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'136' : 6, #MP4 720p (DASH)
			})
		if config_mp.mediaportal.youtubeenablevp9.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'303' : 1, #VP9 1080p60 (DASH)
			'248' : 2, #VP9 1080p (DASH)
			})
	elif videoPrio == 4: #1440p
		self.VIDEO_FMT_PRIORITY_MAP = {
			'299' : 5, #MP4 1080p60 (DASH)
			'137' : 6, #MP4 1080p (DASH)
			'22'  : 7, #MP4 720p
			'35'  : 9, #FLV 480p
			'18'  : 11, #MP4 360p
			'34'  : 12, #FLV 360p
		}
		if config_mp.mediaportal.youtubeenabledash480p.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'135' : 10, #MP4 480p (DASH)
			})
		if config_mp.mediaportal.youtubeenabledash720p.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'136' : 8, #MP4 720p (DASH)
			})
		if config_mp.mediaportal.youtubeenablevp9.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'308' : 1, #VP9 1440p60 (DASH)
			'271' : 2, #VP9 1440p (DASH)
			'303' : 3, #VP9 1080p60 (DASH)
			'248' : 4, #VP9 1080p (DASH)
			})
	elif videoPrio == 5: #2160p
		self.VIDEO_FMT_PRIORITY_MAP = {
			'299' : 7, #MP4 1080p60 (DASH)
			'137' : 8, #MP4 1080p (DASH)
			'22'  : 9, #MP4 720p
			'35'  : 11, #FLV 480p
			'18'  : 13, #MP4 360p
			'34'  : 14, #FLV 360p
		}
		if config_mp.mediaportal.youtubeenabledash480p.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'135' : 12, #MP4 480p (DASH)
			})
		if config_mp.mediaportal.youtubeenabledash720p.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'136' : 10, #MP4 720p (DASH)
			})
		if config_mp.mediaportal.youtubeenablevp9.value:
			self.VIDEO_FMT_PRIORITY_MAP.update({
			'315' : 1, #VP9 2160p60 (DASH)
			'313' : 2, #VP9 2160p (DASH)
			'308' : 3, #VP9 1440p60 (DASH)
			'271' : 4, #VP9 1440p (DASH)
			'303' : 5, #VP9 1080p60 (DASH)
			'248' : 6, #VP9 1080p (DASH)
			})

	self.AUDIO_FMT_PRIORITY_MAP = {
		'258' : 1, #AAC
		'256' : 2, #AAC
		'141' : 3, #AAC ABR256
		'140' : 4, #AAC ABR128
		'139' : 5, #AAC ABR48
		'172' : 6, #VORBIS 256
		'171' : 7, #VORBIS 128
	}

	self.video_url = None
	self.audio_url = None
	self.video_id = url
	self.videoPrio = videoPrio
	self.dash = dash

	# Getting video webpage
	#URLs for YouTube video pages will change from the format #http://www.youtube.com/watch?v=ylLzyHk54Z0 to http://www.youtube.com/watch#!v=ylLzyHk54Z0.
	watch_url = 'https://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1&bpctr=9999999999' % self.video_id
	self.error = "[YoutubeURL] Error: Unable to retrieve watchpage:\n%s\n" % watch_url
	self.yt_dwnld_agent.getWebPage(watch_url).addCallback(self.parseVInfo, watch_url).addErrback(self.dataError)

  def parseVInfo(self, videoinfo, watch_url):
	flashvars = self.extractFlashVars(videoinfo, 0)
	if not flashvars.has_key(u"url_encoded_fmt_stream_map"):
		playerUrl = re.search('.*src="(.*?)"\s+(?:type="text/javascript"\s|)name="player(?:_ias|)/base"', videoinfo, re.S)
		if playerUrl:
			playerUrl = playerUrl.group(1).replace('\/','/')
		else:
			playerUrl = None
		self.checkFlashvars(flashvars, videoinfo, True, playerUrl=playerUrl)
	else:
		links = {}
		audio = {}
		encoded_url_map = ""
		if self.dash and (self.videoPrio >= 3 or (config_mp.mediaportal.youtubeenabledash480p.value and self.videoPrio >= 1) or (config_mp.mediaportal.youtubeenabledash720p.value and self.videoPrio >= 2)):
			try:
				encoded_url_map += u"," + flashvars.get('adaptive_fmts', [])
			except:
				pass
		encoded_url_map += u"," + flashvars[u"url_encoded_fmt_stream_map"]
		for url_desc in encoded_url_map.split(u","):
			url_desc_map = parse_qs(url_desc)
			if not (url_desc_map.has_key(u"url") or url_desc_map.has_key(u"stream")):
				continue

			try:
				key = int(url_desc_map[u"itag"][0])
			except ValueError:
				continue

			url = u""
			if url_desc_map.has_key(u"url"):
				url = urllib.unquote(url_desc_map[u"url"][0])
			elif url_desc_map.has_key(u"conn") and url_desc_map.has_key(u"stream"):
				url = urllib.unquote(url_desc_map[u"conn"][0])
				if url.rfind("/") < len(url) -1:
					url = url + "/"
				url = url + urllib.unquote(url_desc_map[u"stream"][0])
			elif url_desc_map.has_key(u"stream") and not url_desc_map.has_key(u"conn"):
				url = urllib.unquote(url_desc_map[u"stream"][0])

			if url_desc_map.has_key(u"sig"):
				url = url + u"&signature=" + url_desc_map[u"sig"][0]
			elif url_desc_map.has_key(u"s"):
				sig = url_desc_map[u"s"][0]
				flashvars = self.extractFlashVars(videoinfo, 1)
				signature = decryptor.decryptSignature(sig, flashvars[u"js"])
				if not signature:
					self.error = "[YoutubeURL] Error: cannot decrypt url"
					self.errReturn(None)
					return
				else:
					url += u"&signature=" + signature

			try:
				links[self.VIDEO_FMT_PRIORITY_MAP[str(key)]] = url
			except KeyError:
				if self.dash and (self.videoPrio >= 3 or (config_mp.mediaportal.youtubeenabledash480p.value and self.videoPrio >= 1) or (config_mp.mediaportal.youtubeenabledash720p.value and self.videoPrio >= 2)):
					try:
						audio[self.AUDIO_FMT_PRIORITY_MAP[str(key)]] = url
					except KeyError:
						continue
				else:
					continue

		hlsdata = videoinfo.replace('\\/','/').replace('\\"','"')
		url = re.findall('hlsManifestUrl":"(http.*?\.m3u8)"(?:}|,)', hlsdata, re.S)
		if url:
			links = {}
			links[0] = url[-1]

		#print "#####################################################################################"
		#try:
		#	for i in links:
		#		type = re.search('.*?itag=(\d+)', links[i]).group(1)
		#		print type + "\t" + links[i]
		#except:
		#	pass
		#print "#####################################################################################"
		try:
			self.video_url = links[sorted(links.iterkeys())[0]].encode('utf-8')
			if self.dash:
				try:
					if int(re.search('.*?itag=(\d+)', self.video_url).group(1))>100:
						self.audio_url = audio[sorted(audio.iterkeys())[0]].encode('utf-8')
						#print "#####################################################################################"
						#for i in audio:
						#	type = re.search('.*?itag=(\d+)', audio[i]).group(1)
						#	print type + "\t" + audio[i]
						#print "#####################################################################################"
				except:
					pass
			#self.__callBack(self.video_url)
			self.callBack(self.video_url, self.audio_url)
		except (KeyError,IndexError):
			self.error = "[YoutubeURL] Error: no video url found"
			self.errReturn(self.video_url)

  def parseVInfo2(self, videoinfo, playerUrl=None):
	flashvars = parse_qs(videoinfo)
	if not flashvars.has_key(u"url_encoded_fmt_stream_map"):
		if 'hlsvp=' in videoinfo:
			url = urllib.unquote(re.search('hlsvp=(.*?\.m3u8)', videoinfo).group(1))
			self.__callBack(url)
		else:
			self.checkFlashvars(flashvars, videoinfo)
	else:
		video_fmt_map = {}
		fmt_infomap = {}
		tmp_fmtUrlDATA = flashvars['url_encoded_fmt_stream_map'][0].split(',')
		for fmtstring in tmp_fmtUrlDATA:
			fmturl = fmtid = fmtsig = ""
			if flashvars.has_key('url_encoded_fmt_stream_map'):
				try:
					for arg in fmtstring.split('&'):
						if arg.find('=') >= 0:
							key, value = arg.split('=')
							if key == 'itag':
								if len(value) > 3:
									value = value[:2]
								fmtid = value
							elif key == 'url':
								fmturl = value
							elif key == 'sig':
								fmtsig = value
							elif key == 's' and playerUrl != None:
								fmtsig = decryptor.decryptSignature(value, playerUrl)

					if fmtid != "" and fmturl != "" and self.VIDEO_FMT_PRIORITY_MAP.has_key(fmtid):
						video_fmt_map[self.VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl), 'fmtsig': fmtsig }
						fmt_infomap[int(fmtid)] = "%s&signature=%s" %(unquote_plus(fmturl), fmtsig)
					fmturl = fmtid = fmtsig = ""

				except:
					self.error = "[YoutubeURL] Error parsing fmtstring: %s" % fmtstring
					self.errReturn(self.video_url)
					return

			else:
				(fmtid,fmturl) = fmtstring.split('|')

			if self.VIDEO_FMT_PRIORITY_MAP.has_key(fmtid) and fmtid != "":
				video_fmt_map[self.VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl) }
				fmt_infomap[int(fmtid)] = unquote_plus(fmturl)

		if video_fmt_map and len(video_fmt_map):
			best_video = video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]
			if best_video['fmtsig']:
				self.video_url = "%s&signature=%s" %(best_video['fmturl'].split(';')[0], best_video['fmtsig'])
			else:
				self.video_url = "%s" %(best_video['fmturl'].split(';')[0])
			#self.__callBack(self.video_url)
			self.callBack(str(self.video_url))
		else:
			self.error = "[YoutubeURL] Error: no video url found"
			self.errReturn(self.video_url)

  def checkFlashvars(self, flashvars, videoinfo, get_info2=False, playerUrl=None):
	# Attempt to see if YouTube has issued an error message
	if not flashvars.has_key(u"reason"):
		from imports import decodeHtml
		pc = False
		if 'ypc-offer-title' in videoinfo:
			msg = re.search('ypc-offer-title">.*?<a.*?">(.*?)</a', videoinfo, re.S)
			if msg:
				pc = True
				self.error = '[YoutubeURL] Error: Paid Content'
				self.error += '\n: "%s"' % msg.group(1)
		elif 'itemprop="paid" content="True"' in videoinfo:
			msg = re.search('dir="ltr" title="(.*?)"', videoinfo, re.S)
			if msg:
				pc = True
				self.error = '[YoutubeURL] Error: Paid Content'
				self.error += ':\n"%s"' % decodeHtml(msg.group(1))

		msg = re.search('class="message">(.*?)</', videoinfo, re.S)
		if msg:
			txt = msg.group(1).strip()
			msg = re.search('class="submessage">(.*?)</', videoinfo, re.S)
			if msg:
				txt += '\n' + msg.group(1).strip()

			if not pc:
				self.error = '[YoutubeURL] Error: %s' % decodeHtml(txt)
			else:
				self.error += txt
		elif not pc:
			self.error = '[YoutubeURL] Error: unable to extract "url_encoded_fmt_stream_map" parameter for unknown reason'

		if not pc and get_info2 and 'og:restrictions:age' in videoinfo:
			el = '&el=embedded'
			info_url = ('https://www.youtube.com/get_video_info?video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (self.video_id, el))
			self.error = "[YoutubeURL] Error: Unable to retrieve videoinfo page:\n%s\n" % info_url
			self.yt_dwnld_agent.getWebPage(info_url).addCallback(self.parseVInfo2, playerUrl).addErrback(self.dataError)
			return
	else:
		from imports import stripAllTags
		reason = unquote_plus(flashvars['reason'][0])
		self.error = '[YoutubeURL] Error: YouTube said: %s' % stripAllTags(str(reason))

	self.errReturn(self.video_url)

  def removeAdditionalEndingDelimiter(self, data):
	pos = data.find("};")
	if pos != -1:
		data = data[:pos + 1]
	return data

  def normalizeUrl(self, url):
	if url[0:2] == "//":
		url = "https:" + url
	return url

  def extractFlashVars(self, data, assets):
	flashvars = {}
	found = False

	for line in data.split("\n"):
		if line.strip().find(";ytplayer.config = ") > 0:
			found = True
			p1 = line.find(";ytplayer.config = ") + len(";ytplayer.config = ") - 1
			p2 = line.rfind(";")
			if p1 <= 0 or p2 <= 0:
				continue
			data = line[p1 + 1:p2]
			break
	data = self.removeAdditionalEndingDelimiter(data)

	if found:
		data = json.loads(data)
		if assets:
			flashvars = data["assets"]
		else:
			flashvars = data["args"]

		for k in ["html", "css", "js"]:
			if k in flashvars:
				flashvars[k] = self.normalizeUrl(flashvars[k])

	return flashvars

  def callBack(self, url, suburi=None):
	if suburi and not '.m3u8' in url:
		self.__callBack(url, suburi=suburi)
	elif url.startswith('http') and not '.m3u8' in url:
		self.error = '[YoutubeURL] Playback error:'
		try:
			return self.tw_agent_hlp.getRedirectedUrl(url, True).addCallback(self.getRedirect, url).addErrback(self.dataError)
		except:
			self.__callBack(url)
	else:
		self.yt_dwnld_agent.getWebPage(url).addCallback(self.parseM3U8Playlist).addErrback(self.dataError)

  def parseM3U8Playlist(self, data):
	bandwith_list = []
	match_sec_m3u8=re.findall('BANDWIDTH=(\d+).*?\n(.*?m3u8)', data, re.S)
	if self.videoPrio >= 3:
		bw = int(match_sec_m3u8[-1][0])
	elif self.videoPrio == 2:
		bw = int(match_sec_m3u8[-1][0])/2
	elif self.videoPrio == 1:
		bw = int(match_sec_m3u8[-1][0])/3
	else:
		bw = int(match_sec_m3u8[-1][0])/4
	for each in match_sec_m3u8:
		bandwith,url = each
		bandwith_list.append((int(bandwith),url))
	_, best = min((abs(int(x[0]) - bw), x) for x in bandwith_list)
	url = best[1]
	url = url.replace('%2F','%252F').replace('%3D','%253D').replace('%2B','%252B').replace('%3B','%253B')
	self.__callBack(url)

  def getRedirect(self, redir_url, url):
	if 'Forbidden' in redir_url:
		if self.useProxy:
			self.__callBack(url, buffering=True, proxy=(self.proxyurl, self.puser, self.ppass))
		else:
			self.dataError(redir_url)
	else:
		self.__callBack(url)