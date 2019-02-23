# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

default_cover = "file://%s/pornfromczech.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

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

pfcz_cookies = CookieJar()
pfcz_ck = {}
pfcz_agent = ''

BASE_URL = "http://www.pornfromczech.com"

class pornCzechGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("PornFromCzech.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

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
			global pfcz_ck
			global pfcz_agent
			if pfcz_ck == {} or pfcz_agent == '':
				pfcz_ck, pfcz_agent = cfscrape.get_tokens(BASE_URL)
				requests.cookies.cookiejar_from_dict(pfcz_ck, cookiejar=pfcz_cookies)
			else:
				try:
					s = requests.session()
					url = urlparse.urlparse(BASE_URL)
					headers = {'user-agent': pfcz_agent}
					page = s.get(url.geturl(), cookies=pfcz_cookies, headers=headers, timeout=15, allow_redirects=False)
					if page.status_code == 503 and page.headers.get("Server", "").startswith("cloudflare") and b"jschl_vc" in page.content and b"jschl_answer" in page.content:
						pfcz_ck, pfcz_agent = cfscrape.get_tokens(BASE_URL)
						requests.cookies.cookiejar_from_dict(pfcz_ck, cookiejar=pfcz_cookies)
				except:
					pass
			self.keyLocked = False
			reactor.callFromThread(self.getGenres)
		else:
			reactor.callFromThread(self.pfcz_error)

	def pfcz_error(self):
		message = self.session.open(MessageBoxExt, _("Mandatory depends python-requests and/or python-pyexecjs and nodejs are missing!"), MessageBoxExt.TYPE_ERROR)
		self.keyCancel()

	def getGenres(self):
		url = BASE_URL
		twAgentGetPage(url, agent=pfcz_agent, cookieJar=pfcz_cookies).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('<ul id="menu-category"(.*?)</ul>', data, re.S)
		Cats = re.findall('<a href="(.*?)">(.*?)</a>', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = Url + "page/"
				self.genreliste.append((decodeHtml(Title), Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Newest", "http://pornfromczech.com/page/", default_cover))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = urllib.quote(callback).replace(' ', '+')
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			self.session.open(pornCzechFilmScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornCzechFilmScreen, Link, Name)

class pornCzechFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("PornFromCzech.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://www.pornfromczech.com/page/" + str(self.page) + "/?s=" + self.Link
		else:
			url = self.Link + str(self.page)
		twAgentGetPage(url, agent=pfcz_agent, cookieJar=pfcz_cookies).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', "class='pages'>.*?of\s(.*?)<")
		Movies = re.findall('<div\sclass="thumb">.*?<a\shref="(.*?)".*?title="(.*?)">.*?<img\ssrc="(.*?)".*?<p class="duration">(.*?)</p>', data, re.S)
		if Movies:
			for (Url, Title, Image, Duration) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image, Duration))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None, ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		runtime = self['liste'].getCurrent()[0][3]
		self['handlung'].setText("Runtime: %s" % (runtime))
		self['name'].setText(title)
		pic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		if url:
			self.session.open(pornCzechFilmAuswahlScreen, title, url, image)

class pornCzechFilmAuswahlScreen(MPScreen):

	def __init__(self, session, genreName, genreLink, cover):
		self.genreLink = genreLink
		self.genreName = genreName
		self.cover = cover
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0": self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("PornFromCzech.com")
		self['ContentTitle'] = Label("Streams")
		self['name'] = Label(self.genreName)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		twAgentGetPage(self.genreLink, agent=pfcz_agent, cookieJar=pfcz_cookies).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		streams = re.findall('<iframe.*?src=[\'|"](http[s]?://(.*?)\/.*?)[\'|"|\&|<]', data, re.S|re.I)
		if streams:
			for (stream, hostername) in streams:
				if isSupportedHoster(hostername, True):
					hostername = hostername.replace('www.','').replace('embed.','').replace('play.','')
					self.filmliste.append((hostername, stream))
				if hostername == "www.strdef.world":
					hostername = "Openload"
					self.filmliste.append((hostername, stream))
			# remove duplicates
			self.filmliste = list(set(self.filmliste))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			if "strdef.world" in url:
				url = url.replace('https','http')
				twAgentGetPage(url, headers={'Referer':BASE_URL}, agent=pfcz_agent, cookieJar=pfcz_cookies).addCallback(self.parseOL).addErrback(self.dataError)
			else:
				get_stream_link(self.session).check_link(url, self.got_link)

	def parseOL(self, data):
		try:
			import execjs
			node = execjs.get("Node")
		except:
			printl('nodejs not found',self,'E')
			self.session.open(MessageBoxExt, _("This plugin requires packages python-pyexecjs and nodejs."), MessageBoxExt.TYPE_INFO)
			return
		script = re.findall('<script language="JavaScript" type="text/javascript">(.*?)</script>', data, re.S)
		if script:
			func = re.findall('function\s(.*?)\(', data, re.S)[0]
			js = script[0].replace(func, 'decrypt').replace('document.write', 'video_url=') + "return video_url;"
			data = str(node.exec_(js))
			script = re.findall('<script language="JavaScript" type="text/javascript">(.*?)</script>', data, re.S)
			if script:
				func = re.findall('function\s(.*?)\(', data, re.S)[0]
				js = script[0].replace(func, 'decrypt').replace('document.write', 'video_url=') + "return video_url;"
				data = str(node.exec_(js))
				stream = re.findall('<iframe.*?src=[\'|"](http[s]?://.*?\/.*?)[\'|"|\&|<]', data, re.S|re.I)
				get_stream_link(self.session).check_link(stream[0], self.got_link)

	def got_link(self, stream_url):
		title = self.genreName
		self.session.open(SimplePlayer, [(title, stream_url, self.cover)], showPlaylist=False, ltype='pornCzech', cover=True)