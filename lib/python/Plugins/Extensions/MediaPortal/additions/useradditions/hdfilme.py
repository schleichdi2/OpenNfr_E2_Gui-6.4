# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

try:
	from Plugins.Extensions.MediaPortal.resources import cfscrape
except:
	cfscrapeModule = False
else:
	cfscrapeModule = True

try:
	import requests
except:
	requestsModule = False
else:
	requestsModule = True

import urlparse
import thread

hf_cookies = CookieJar()
hf_ck = {}
hf_agent = ''
BASE_URL = 'http://hdfilme.tv'

class hdfilmeMain(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin')

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("HDFilme")

		self.streamList = []
		self.suchString = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onFirstExecBegin.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		thread.start_new_thread(self.get_tokens,("GetTokens",))
		self['name'].setText(_("Please wait..."))

	def get_tokens(self, threadName):
		if requestsModule and cfscrapeModule:
			printl("Calling thread: %s" % threadName,self,'A')
			global hf_ck
			global hf_agent
			if hf_ck == {} or hf_agent == '':
				hf_ck, hf_agent = cfscrape.get_tokens(BASE_URL)
				requests.cookies.cookiejar_from_dict(hf_ck, cookiejar=hf_cookies)
			else:
				try:
					s = requests.session()
					url = urlparse.urlparse(BASE_URL)
					headers = {'user-agent': hf_agent}
					page = s.get(url.geturl(), cookies=hf_cookies, headers=headers)
					if page.status_code == 503 and page.headers.get("Server", "").startswith("cloudflare") and b"jschl_vc" in page.content and b"jschl_answer" in page.content:
						hf_ck, hf_agent = cfscrape.get_tokens(BASE_URL)
						requests.cookies.cookiejar_from_dict(hf_ck, cookiejar=hf_cookies)
				except:
					pass
			self.keyLocked = False
			reactor.callFromThread(self.getPage)
		else:
			reactor.callFromThread(self.hf_error)

	def hf_error(self):
		message = self.session.open(MessageBoxExt, _("Mandatory depends python-requests and/or python-pyexecjs and nodejs are missing!"), MessageBoxExt.TYPE_ERROR)
		self.keyCancel()

	def getPage(self):
		twAgentGetPage('%s/movie-movies' % BASE_URL, agent=hf_agent, cookieJar=hf_cookies).addCallback(self.loadPage).addErrback(self.dataError)

	def loadPage(self, data):
		self.keyLocked = True
		parse = re.search('>Genre</option>(.*?)</select>', data, re.S)
		if parse:
			cats = re.findall('<option value="(\d+)"\s+>\s+(.*?)\s\s', parse.group(1), re.S)
			if cats:
				for tagid, name in cats:
					self.streamList.append(("%s" % name, "%s/movie-movies?cat=%s&country=&order_f=last_update&order_d=desc&page=" % (BASE_URL, str(tagid))))
		self.streamList.sort(key=lambda t : t[0].lower())
		self.streamList.insert(0, ("Serien","%s/movie-series?page=" % BASE_URL))
		self.streamList.insert(0, ("Kinofilme","%s/movie-movies?page=" % BASE_URL))
		self.streamList.insert(0, ("--- Search ---", "search"))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		genre = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if genre == "--- Search ---":
			self.suchen(auto_text_init=True)
		else:
			self.session.open(hdfilmeParsing, genre, url)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.strip()
			url = '%s/movie-search?key=%s&page_film=' % (BASE_URL, urllib.quote_plus(self.suchString))
			genre = self['liste'].getCurrent()[0][0]
			self.session.open(hdfilmeParsing, genre, url)

class hdfilmeParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		MPScreen.__init__(self, session, skin='MP_Plugin')
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("HDFilme")
		self['Page'] = Label(_("Page:"))
		self['ContentTitle'] = Label(genre)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = self.url+str(self.page)
		twAgentGetPage(url, agent=hf_agent, cookieJar=hf_cookies).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, '', '</i>\s*Seite.*?/\s*(\d+)')
		movies = re.findall('data-popover="movie-data.*?">\s*<a href="(.*?)">\s*<img.*?src="(.*?)".*?alt="(.*?)"', data, re.I)
		if movies:
			for url,bild,title in movies:
				self.streamList.append((decodeHtml(title),url,bild))
		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), None, None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page, self.lastpage, agent=hf_agent, cookies=hf_ck)
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		self.coverurl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(self.coverurl, agent=hf_agent, cookieJar=hf_cookies)
		self['name'].setText(title)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(hdfilmeStreams, title, url, cover)

class hdfilmeStreams(MPScreen):
	new_video_formats = (
			{
				'1080' : 4, #MP4 1080p
				'720' : 3, #MP4 720p
				'480' : 2, #MP4 480p
				'360' : 1, #MP4 360p
			},
			{
				'1080' : 4, #MP4 1080p
				'720' : 3, #MP4 720p
				'480' : 1, #MP4 480p
				'360' : 2, #MP4 360p
			},
			{
				'1080' : 1, #MP4 1080p
				'720' : 2, #MP4 720p
				'480' : 3, #MP4 480p
				'360' : 4, #MP4 360p
				'0' : 5, #MP4
			}
		)

	def __init__(self, session, title, url, cover):
		self.movietitle = title
		self.url = url
		self.cover = cover
		MPScreen.__init__(self, session, skin='MP_Plugin')

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"green" : self.keyTrailer,
		}, -1)

		self['title'] = Label("HDFilme")
		self['leftContentTitle'] = Label(_("Stream Selection"))
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.movietitle)

		self.trailer = None
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		twAgentGetPage(self.url, agent=hf_agent, cookieJar=hf_cookies).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		m = re.search('<a class="btn.*?href="(.*?)">.{0,1}Trailer\s{0,1}[</a>|<i]', data, re.S)
		if m:
			self.trailer = m.group(1)
			self['F2'].setText('Trailer')

		servers = re.findall('<a.+?href="#(.*?)"\srole="tab" data-toggle="tab"><b>(.*?)</b></a>', data, re.S)
		if servers:
			for tab, server in servers:
				m = re.search('<div\srole="tabpanel"\sclass="tab-pane.*?"\sid="%s">(.*?)</div>' % tab, data, re.S)
				if m:
					streams = re.findall('_episode="(\d+)" _link(?:=""|) _sub(?:=""|)\s+href="(.*?)"', m.group(1), re.S)
					if streams:
						folge = 'Folge ' if len(streams) > 1 and len(servers) == 1 else server.strip()
						for (epi_num, link) in streams:
							if not folge[0] == 'F': epi_num = ''
							self.streamList.append((folge+epi_num, link.replace('&amp;','&'), epi_num))
		if not len(self.streamList):
			streams = re.findall('_episode=".*?" _link(?:=""|) _sub(?:=""|)\s+href="(.*?)">', data, re.S)
			if streams:
				for link in streams:
					epi_num = re.findall('episode=(\d+)(?:\&amp|)', link)
					if epi_num:
						epi_num = epi_num[0]
						if re.search('staffel ', self.movietitle, re.I):
							folge = 'Folge '
							_epi_num = epi_num.strip(' \t\n\r')
						else:
							folge = 'Stream '
							_epi_num = ''
						self.streamList.append((folge+epi_num, link.replace('&amp;','&'), _epi_num))

		if len(self.streamList) == 0:
			self.streamList.append((_('No supported streams found!'), None, None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlisthoster, self.streamList))
		CoverHelper(self['coverArt']).getCover(self.cover, agent=hf_agent, cookieJar=hf_cookies)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		link = self['liste'].getCurrent()[0][1]
		twAgentGetPage(link, agent=hf_agent, cookieJar=hf_cookies).addCallback(self.getStreamUrl).addErrback(self.dataError)

	def makeTitle(self):
		episode = self['liste'].getCurrent()[0][2]
		if episode:
			title = "%s - Folge %s" % (self.movietitle, episode)
		else:
			title = self.movietitle
		return title

	def getStreamUrl(self, data):
		parse = re.findall('initPlayer\(\s+\"(\d+)\",\s+\"(\d+)\",', data, re.S)
		if parse:
			url = BASE_URL + "/movie/getlink/"+str(parse[0][0])+"/"+str(parse[0][1])
			twAgentGetPage(url, agent=hf_agent, cookieJar=hf_cookies).addCallback(self.extractStreams).addErrback(self.dataError)

	def extractStreams(self, data, videoPrio=2):
		try:
			import base64
			data = base64.b64decode(data)
		except:
			self.stream_not_found()
		try:
			d = json.loads(data)
			links = {}
			if d['playinfo']:
				for stream in d['playinfo']:
					key = str(stream.get('label'))
					if key:
						key = key.strip('p')
						if self.new_video_formats[videoPrio].has_key(key):
							links[self.new_video_formats[videoPrio][key]] = stream.get('file')
						else:
							print 'no format prio:', key
				try:
					video_url = links[sorted(links.iterkeys())[0]]
				except (KeyError,IndexError):
					self.stream_not_found()
				else:
					self.play(str(video_url))
			else:
				self.stream_not_found()
		except:
			try:
				d = json.loads(data)
				links = {}
				if d['playinfo']:
					stream = d['playinfo']
					self.play(str(stream))
				else:
					self.stream_not_found()
			except:
				self.stream_not_found()

	def play(self, url):
		title = self.makeTitle()
		self.session.open(SimplePlayer, [(title, url, self.cover)], showPlaylist=False, ltype='hdfilme', cover=True)

	def stream_not_found(self):
		self.session.open(MessageBoxExt, _("Sorry, can't extract a stream url."), MessageBoxExt.TYPE_INFO, timeout=5)

	def keyTrailer(self):
		if self.trailer:
			twAgentGetPage(self.trailer, agent=hf_agent, cookieJar=hf_cookies).addCallback(self.playTrailer).addErrback(self.dataError)

	def playTrailer(self, data):
		from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
		m = re.search('//www.youtube\.com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		if m:
			trailerId = m.group(2)
			title = self.movietitle
			self.session.open(
				YoutubePlayer,
				[(title+' - Trailer', trailerId, self.cover)],
				playAll = False,
				showPlaylist=False,
				showCover=True
				)
		else:
			self.stream_not_found()