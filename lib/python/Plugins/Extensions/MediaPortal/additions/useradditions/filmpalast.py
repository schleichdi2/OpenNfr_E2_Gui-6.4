# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

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

BASEURL = 'https://filmpalast.to'

fp_cookies = CookieJar()
fp_ck = {}
fp_agent = ''

default_cover = "file://%s/filmpalast.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class filmPalastMain(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.suchString = ''
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		thread.start_new_thread(self.get_tokens,("GetTokens",))
		self['name'].setText(_("Please wait..."))

	def getGenres(self):
		self.streamList.append(("--- Search ---", "callSuchen"))
		self.streamList.append(("Neueste Filme", "/movies/new/page/"))
		self.streamList.append(("Neueste Episoden", "/serien/view/page/"))
		self.streamList.append(("Serien", "/serien/view/page/"))
		self.streamList.append(("Abenteuer", "/search/genre/Abenteuer/"))
		self.streamList.append(("Action", "/search/genre/Action/"))
		self.streamList.append(("Adventure", "/search/genre/Adventure/"))
		self.streamList.append(("Animation", "/search/genre/Animation/"))
		self.streamList.append(("Biographie", "/search/genre/Biographie/"))
		self.streamList.append(("Comedy", "/search/genre/Comedy/"))
		self.streamList.append(("Crime", "/search/genre/Crime/"))
		self.streamList.append(("Documentary", "/search/genre/Documentary/"))
		self.streamList.append(("Drama", "/search/genre/Drama/"))
		self.streamList.append(("Familie", "/search/genre/Familie/"))
		self.streamList.append(("Fantasy", "/search/genre/Fantasy/"))
		self.streamList.append(("History", "/search/genre/History/"))
		self.streamList.append(("Horror", "/search/genre/Horror/"))
		self.streamList.append(("Komödie", "/search/genre/Kom%C3%B6die/"))
		self.streamList.append(("Krieg", "/search/genre/Krieg/"))
		self.streamList.append(("Krimi", "/search/genre/Krimi/"))
		self.streamList.append(("Musik", "/search/genre/Musik/"))
		self.streamList.append(("Mystery", "/search/genre/Mystery/"))
		self.streamList.append(("Romanze", "/search/genre/Romanze/"))
		self.streamList.append(("Sci-Fi", "/search/genre/Sci-Fi/"))
		self.streamList.append(("Sport", "/search/genre/Sport/"))
		self.streamList.append(("Thriller", "/search/genre/Thriller/"))
		self.streamList.append(("Western", "/search/genre/Western/"))
		self.streamList.append(("Zeichentrick", "/search/genre/Zeichentrick/"))
		self.streamList.append(("0-9", "/search/alpha/0-9/"))
		for c in xrange(26):
			self.streamList.append((chr(ord('A') + c), '/search/alpha/' + chr(ord('A') + c) + '/'))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def get_tokens(self, threadName):
		if requestsModule and cfscrapeModule:
			printl("Calling thread: %s" % threadName,self,'A')
			global fp_ck
			global fp_agent
			if fp_ck == {} or fp_agent == '':
				fp_ck, fp_agent = cfscrape.get_tokens(BASEURL)
				requests.cookies.cookiejar_from_dict(fp_ck, cookiejar=fp_cookies)
			else:
				try:
					s = requests.session()
					url = urlparse.urlparse(BASEURL)
					headers = {'user-agent': fp_agent}
					page = s.get(url.geturl(), cookies=fp_cookies, headers=headers)
					if page.status_code == 503 and page.headers.get("Server", "").startswith("cloudflare") and b"jschl_vc" in page.content and b"jschl_answer" in page.content:
						fp_ck, fp_agent = cfscrape.get_tokens(BASEURL)
						requests.cookies.cookiejar_from_dict(fp_ck, cookiejar=fp_cookies)
				except:
					pass
			self.keyLocked = False
			reactor.callFromThread(self.getGenres)
		else:
			reactor.callFromThread(self.fp_error)

	def fp_error(self):
		message = self.session.open(MessageBoxExt, _("Mandatory depends python-requests and/or python-pyexecjs and nodejs are missing!"), MessageBoxExt.TYPE_ERROR)
		self.keyCancel()

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Link = "%s/search/title/%s/" % (BASEURL, urllib.quote(callback).replace(' ', '%20'))
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(filmPalastParsing, Name, Link)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		url = BASEURL + self['liste'].getCurrent()[0][1]
		if auswahl == "--- Search ---":
			self.suchen()
		elif auswahl == "Serien":
			self.session.open(filmPalastSerieParsing, auswahl, url + "1")
		else:
			self.session.open(filmPalastParsing, auswahl, url)

class filmPalastSerieParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label("%s" % self.genre)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_("Please wait..."))
		twAgentGetPage(self.url, agent=fp_agent, cookieJar=fp_cookies).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		raw = re.findall('<section id="serien">(.*?)</section>', data, re.S)
		if raw:
			serien = re.findall('<a href="(%s/movies/view/.*?)">(.*?)<' % BASEURL, raw[0], re.S)
			if serien:
				for url,title in serien:
					self.streamList.append((decodeHtml(title), url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No shows found!'), None))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		url = self['liste'].getCurrent()[0][1]
		if url:
			coverUrl = url.replace('%smovies/view/' % BASEURL, '%s/files/movies/450/' % BASEURL) + '.jpg'
			CoverHelper(self['coverArt']).getCover(coverUrl, agent=fp_agent, cookieJar=fp_cookies)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if url:
			self.session.open(filmPalastEpisodenParsing, stream_name, url)

class filmPalastEpisodenParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label(_("Episode Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_("Please wait..."))
		twAgentGetPage(self.url, agent=fp_agent, cookieJar=fp_cookies).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		episoden = re.findall('<a id="staffId_" href="((?:https:|)//filmpalast.to/stream/.*?)" class="getStaffelStream".*?</i>(.*?)&', data, re.S)
		if episoden:
			for (Url, title) in episoden:
				if Url.startswith('//'):
					Url = "https:" + Url
				cover = Url.replace('%s/stream/' % BASEURL, '%s/files/movies/450/' % BASEURL) + '.jpg'
				self.streamList.append((decodeHtml(title).strip(), Url, cover))
		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), '', ''))
		self.streamList.sort()
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl, agent=fp_agent, cookieJar=fp_cookies)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(filmPalastStreams, stream_name, url, cover)

class filmPalastParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
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

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label("%s" % self.genre)

		self['Page'] = Label(_("Page:"))

		self.page = 1
		self.lastpage = 1
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_("Please wait..."))
		url = self.url+str(self.page)
		twAgentGetPage(url, agent=fp_agent, cookieJar=fp_cookies).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, 'id="paging">(.*?)</div>')
		movies = re.findall('<small class="rb">.*?<a href="((?:https:|)//filmpalast.to/.*?)" title="(.*?)"> <img(?: width="236px" height="338px"|) src="(.*?.jpg)"', data, re.S)
		if movies:
			for (Url, Title, Image) in movies:
				Image = BASEURL + Image
				if Url.startswith('//'):
					Url = "https:" + Url
				self.streamList.append((decodeHtml(Title), Url, Image))
		if len(self.streamList) == 0:
			self.streamList.append((_('No movies found!'), None, None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, self.page, self.lastpage)
		self.showInfos()

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl, agent=fp_agent, cookieJar=fp_cookies)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		cover = self['liste'].getCurrent()[0][2]
		if url and self.genre == "Neueste Episoden":
			self.session.open(filmPalastEpisodenParsing, stream_name, url)
		elif url:
			self.session.open(filmPalastStreams, stream_name, url, cover)

class filmPalastStreams(MPScreen):

	def __init__(self, session, stream_name, url, cover):
		self.stream_name = stream_name
		self.url = url
		self.cover = cover
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("FilmPalast.to")
		self['ContentTitle'] = Label(_("Stream Selection"))
		self['name'] = Label(self.stream_name)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		twAgentGetPage(self.url, agent=fp_agent, cookieJar=fp_cookies).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.streamList = []
		streams = re.findall('currentStreamLinks.*?class="hostName">(.*?)<.*?href="(.*?)"', data, re.S)
		if streams:
			for (Hoster, Url) in streams:
					if isSupportedHoster(Hoster, True):
						self.streamList.append((Hoster, Url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.streamList))
		CoverHelper(self['coverArt']).getCover(self.cover, agent=fp_agent, cookieJar=fp_cookies)
		self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			get_stream_link(self.session).check_link(url, self.playfile)
		else:
			message = self.session.open(MessageBoxExt, _("Broken URL parsing, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=3)

	def playfile(self, stream_url):
		self.session.open(SimplePlayer, [(self.stream_name, stream_url, self.cover)], showPlaylist=False, ltype='filmpalast', cover=True)