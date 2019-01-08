# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
default_cover = "file://%s/freeomovie.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

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

free_cookies = CookieJar()
free_ck = {}
free_agent = ''

BASE_URL = "https://www.freeomovie.com"

class freeomovieGenreScreen(MPScreen):

	def __init__(self, session):

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self.language = "de"
		self.suchString = ''
		self['title'] = Label("freeomovie.com")
		self['ContentTitle'] = Label("Genres")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		thread.start_new_thread(self.get_tokens,("GetTokens",))

	def get_tokens(self, threadName):
		if requestsModule and cfscrapeModule:
			printl("Calling thread: %s" % threadName,self,'A')
			global free_ck
			global free_agent
			if free_ck == {} or free_agent == '':
				free_ck, free_agent = cfscrape.get_tokens(BASE_URL)
				requests.cookies.cookiejar_from_dict(free_ck, cookiejar=free_cookies)
			else:
				try:
					s = requests.session()
					url = urlparse.urlparse(BASE_URL)
					headers = {'user-agent': free_agent}
					page = s.get(url.geturl(), cookies=free_cookies, headers=headers, timeout=15, allow_redirects=False)
					if page.status_code == 503 and page.headers.get("Server", "").startswith("cloudflare") and b"jschl_vc" in page.content and b"jschl_answer" in page.content:
						free_ck, free_agent = cfscrape.get_tokens(BASE_URL)
						requests.cookies.cookiejar_from_dict(free_ck, cookiejar=free_cookies)
				except:
					pass
			self.keyLocked = False
			reactor.callFromThread(self.getGenres)
		else:
			reactor.callFromThread(self.free_error)

	def free_error(self):
		message = self.session.open(MessageBoxExt, _("Mandatory depends python-requests and/or python-pyexecjs and nodejs are missing!"), MessageBoxExt.TYPE_ERROR)
		self.keyCancel()

	def getGenres(self):
		url = BASE_URL
		twAgentGetPage(url, agent=free_agent, cookieJar=free_cookies).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('Categories</h2>(.*?)</div>', data, re.S)
		Cat = re.findall('href="(.*?)".*?>(.*?)</a>', parse.group(1), re.S)
		if Cat:
			for (Url, Title) in Cat:
				Url = Url + "page/"
				if Title not in ["XXX Comics", "XXX Games"]:
					self.genreliste.append((Title, Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Newest", "https://www.freeomovie.com/page/"))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			freeomovieUrl = '%s' % (self.suchString)
			freeomovieGenre = "--- Search ---"
			self.session.open(freeomovieFilmListeScreen, freeomovieUrl, freeomovieGenre)

	def keyOK(self):
		if self.keyLocked:
			return
		freeomovieGenre = self['liste'].getCurrent()[0][0]
		freeomovieUrl = self['liste'].getCurrent()[0][1]
		if freeomovieGenre == "--- Search ---":
			self.suchen()
		else:
			self.session.open(freeomovieFilmListeScreen, freeomovieUrl, freeomovieGenre)

class freeomovieFilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self['title'] = Label("freeomovie.com")
		self['ContentTitle'] = Label("%s" % self.genreName)
		self['name'] = Label("Film Auswahl")
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		if re.match(".*?Search", self.genreName):
			url = "https://www.freeomovie.com/page/%s/?s=%s" % (str(self.page),self.genreLink)
		else:
			url = "%s%s" % (self.genreLink,str(self.page))
		twAgentGetPage(url, agent=free_agent, cookieJar=free_cookies).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.getLastPage(data, 'class=[\"|\']wp-pagenavi[\"|\'](.*?)</div>')
		movies = re.findall('class="boxtitle">.*?<a href="(.*?)".*?title="(.*?)".*?<img src="(.*?)"', data, re.S)
		if movies:
			self.filmliste = []
			for (url,title,image) in movies:
				self.filmliste.append((decodeHtml(title),url,image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste,0,1,2,None,None,self.page,self.lastpage)
			self.showInfos()

	def showInfos(self):
		streamTitle = self['liste'].getCurrent()[0][0]
		streamUrl = self['liste'].getCurrent()[0][1]
		streamPic = self['liste'].getCurrent()[0][2]
		self['name'].setText(streamTitle)
		CoverHelper(self['coverArt']).getCover(streamPic)
		twAgentGetPage(streamUrl, agent=free_agent, cookieJar=free_cookies).addCallback(self.getDescription).addErrback(self.dataError)

	def getDescription(self, data):
		ddDescription = re.search('name="description"\scontent="(.*?)"', data, re.S)
		if ddDescription:
			self['handlung'].setText(decodeHtml(ddDescription.group(1)))
		else:
			self['handlung'].setText(_("No further information available!"))

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		self.session.open(freeomovieFilmAuswahlScreen, title, url, image)

class freeomovieFilmAuswahlScreen(MPScreen):

	def __init__(self, session, genreName, genreLink, cover):
		self.genreLink = genreLink
		self.genreName = genreName
		self.cover = cover
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("freeomovie.com")
		self['ContentTitle'] = Label("Streams")
		self['name'] = Label(self.genreName)


		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		twAgentGetPage(self.genreLink, agent=free_agent, cookieJar=free_cookies).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('class="videosection(.*?)class="textsection', data, re.S)
		streams = re.findall('(http[s]?://(.*?)\/.*?)[\'|"|\&|<]', parse.group(1) , re.S)
		if streams:
			for (stream, hostername) in streams:
				if isSupportedHoster(hostername, True):
					disc = re.search('.*?(CD-1|CD1|CD-2|CD2|_a.avi|_b.avi|-a.avi|-b.avi|DISC1|DISC2).*?', stream, re.S|re.I)
					if disc:
						discno = disc.group(1)
						discno = discno.replace('cd1','Teil 1').replace('cd2','Teil 2').replace('CD1','Teil 1').replace('CD2','Teil 2').replace('CD-1','Teil 1').replace('CD-2','Teil 2').replace('_a.avi','Teil 1').replace('_b.avi','Teil 2')
						discno = discno.replace('-a.avi','Teil 1').replace('-b.avi','Teil 2').replace('DISC1','Teil 1').replace('DISC2','Teil 2').replace('Disc1','Teil 1').replace('Disc2','Teil 2')
						hostername = hostername + ' (' + discno + ')'
					self.filmliste.append((hostername, stream))
			# remove duplicates
			self.filmliste = list(set(self.filmliste))
		if len(self.filmliste) == 0:
			self.filmliste.append(("No supported streams found!", None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			url = url.replace('&amp;','&').replace('&#038;','&')
			get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		title = self.genreName
		self.session.open(SimplePlayer, [(title, stream_url, self.cover)], showPlaylist=False, ltype='freeomovie', cover=True)