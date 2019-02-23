# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

glob_cookies = CookieJar()
agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
BASE_URL = 'https://pornfree.tv'
default_cover = "file://%s/pornfreetv.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class pornfreetvGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("PornFreeTV")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.getData)

	def getData(self):
		self['name'].setText(_('Please wait...'))
		url = BASE_URL + "/categories/"
		twAgentGetPage(url, agent=agent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		cats = re.findall('<center><a href="(https://pornfree.tv/categories.*?)">(.*?)\s\(\d+ videos\)</a', data, re.S)
		if cats:
			for (url, title) in cats:
				self.genreliste.append((title, url))
			self.genreliste.sort()
		self.genreliste.insert(0, ("Years", "years"))
		self.genreliste.insert(0, ("Studios", "studios"))
		self.genreliste.insert(0, ("Most Commented", "?order_post=comments"))
		self.genreliste.insert(0, ("Most Liked", "?order_post=liked"))
		self.genreliste.insert(0, ("Most Viewed", "?order_post=viewed"))
		self.genreliste.insert(0, ("Newest", "?order_post=latest"))
		self.genreliste.insert(0, ("--- Search ---", None))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self['name'].setText("")

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = urllib.quote(callback).replace(' ', '+')
			Link = self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(pornfreetvFilmScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Studios" or Name == "Years":
			self.session.open(pornfreetvSubGenreScreen, Link, Name)
		else:
			self.session.open(pornfreetvFilmScreen, Link, Name)

class pornfreetvSubGenreScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("PornFreeTV")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		twAgentGetPage(BASE_URL, agent=agent).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = None
		if self.Name == "Studios":
			preparse = re.search('>Studios</span(.*?)</ul>', data, re.S|re.I)
			if preparse:
				parse = re.findall('href="(.*?)".*?ubermenu-target-text">(.*?)</span', preparse.group(1), re.S)
		elif self.Name == "Years":
			preparse = re.search('By Year</h2>(.*?)</div>', data, re.S|re.I)
			if preparse:
				parse = re.findall('href="(.*?)">(.*?)</a>', preparse.group(1), re.S)
		if parse:
			for (Url, Title) in parse:
				if not re.match('http', Url):
					Url = "%s%s" % (BASE_URL, Url)
				self.genreliste.append((decodeHtml(Title), Url))
			self.genreliste.sort()
		if len(self.genreliste) == 0:
			self.filmliste.append((_('Nothing found!'), ''))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self['name'].setText("")

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(pornfreetvFilmScreen, Link, Name)

class pornfreetvFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("PornFreeTV")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
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
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "%s/page/%s/?s=%s" % (BASE_URL, str(self.page), self.Link)
		elif "?order_post=" in self.Link:
			url = BASE_URL + "/page/" + str(self.page) + "/" + self.Link
		else:
			url = self.Link + "page/" + str(self.page) + "/"
		twAgentGetPage(url, agent=agent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</ul>', '.*>((?:\d+,|)\d+)<')
		preparse = re.search('.*?class="section-header">(.*?)$', data, re.S)
		if preparse:
			Movies = re.findall('item-img">.*?src="(.*?)"\sclass="img-responsive.*?<h3><a href="(https://pornfree.tv/video/(.*?)/)">(.*?)</a>.*?class="date">(.*?)</span.*?fa-eye"></i>(.*?)</span', preparse.group(1), re.S)
			if Movies:
				for (Image, Url, Filename, Title, Added, Views) in Movies:
					if "&hellip;" in Title:
						tmp1 = stripAllTags(Title).split(' ')[0]
						tmp2 = Filename.lower().replace(tmp1.lower(),'').replace('-',' ').strip()
						tmp3 = stripAllTags(Title).split('(')[-1]
						Title = tmp1 + " " + tmp2 + " (" + tmp3
						Title = ' '.join(s[:1].upper() + s[1:] for s in stripAllTags(Title).split(' '))
					if not re.match('http', Url):
						Url = BASE_URL + "/" + Url
					self.filmliste.append((stripAllTags(decodeHtml(Title)), Url, Image, Views, Added))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=0)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		Views = self['liste'].getCurrent()[0][3]
		Added = self['liste'].getCurrent()[0][4]
		handlung = "Added: %s\nViews: %s" % (Added, Views)
		self['name'].setText(Title)
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Image = self['liste'].getCurrent()[0][2]
		if Link == None:
			return
		self.session.open(pornfreetvStreamListeScreen, Link, Title, Image)

class pornfreetvStreamListeScreen(MPScreen):

	def __init__(self, session, Link, Name, Image):
		self.Link = Link
		self.Name = Name
		self.Image = Image
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("PornFreeTV")
		self['ContentTitle'] = Label("Streams:")

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'] = Label(_("Please wait..."))
		self.keyLocked = True
		CoverHelper(self['coverArt']).getCover(self.Image)
		twAgentGetPage(self.Link, cookieJar=glob_cookies, agent=agent).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		streams = re.findall('(http[s]?://(.*?)\/.*?)[\'|"|\&|<]', data, re.S)
		if streams:
			for (stream, hostername) in streams:
				if isSupportedHoster(hostername, True):
					hostername = hostername.replace('www.','')
					self.filmliste.append((hostername, stream))
			# remove duplicates
			self.filmliste = list(set(self.filmliste))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No supported streams found!"), None))
		self.filmliste = list(set(self.filmliste))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False
		self['name'].setText(self.Name)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		self.session.open(SimplePlayer, [(self.Name, stream_url, self.Image)], showPlaylist=False, ltype='pornfreetv', cover=True)