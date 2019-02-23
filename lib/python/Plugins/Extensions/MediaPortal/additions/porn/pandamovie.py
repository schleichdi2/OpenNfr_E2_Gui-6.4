# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
default_cover = "file://%s/pandamovie.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class pandamovieGenreScreen(MPScreen):

	def __init__(self, session, mode='Genres'):
		self.mode = mode
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("PandaMovie")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.suchString = ''

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "https://pandamovies.pw/"
		twAgentGetPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('<a href="#">%s</a>(.*?)</ul>' % self.mode, data, re.S)
		if parse:
			raw = re.findall('href="(.*?)">(.*?)</a', parse.group(1), re.S)
			if raw:
				for (Url, Title) in raw:
					if Url.startswith('//'):
						Url = "https:" + Url
					Url = Url + "/page/"
					self.filmliste.append((decodeHtml(Title), Url))
				self.filmliste.sort()
		if self.mode == "Genres":
			self.filmliste.insert(0, ("Years", "Years", None))
			self.filmliste.insert(0, ("Studios", "Studios", None))
			self.filmliste.insert(0, ("HD", "https://pandamovies.pw/watch-hd-movies-online-free/page/", None))
			self.filmliste.insert(0, ("Most Popular (All Time)", "https://pandamovies.pw/popular-movies/page/", None))
			self.filmliste.insert(0, ("Most Popular (Monthly)", "https://pandamovies.pw/popular-movies-in-last-30-days/page/", None))
			self.filmliste.insert(0, ("Most Popular (Weekly)", "https://pandamovies.pw/popular-movies-last-7-days/page/", None))
			self.filmliste.insert(0, ("Most Popular (Daily)", "https://pandamovies.pw/popular-movies-in-last-24-hours/page/", None))
			self.filmliste.insert(0, ("Featured", "https://pandamovies.pw/watch-featured-movies-online-free/page/", None))
			self.filmliste.insert(0, ("Clips & Scenes", "https://pandamovies.pw/watch-clips-scenes-porn-movies-online-free/page/", None))
			self.filmliste.insert(0, ("Japanese Movies", "https://pandamovies.pw/watch-japanese-porn-movies-online-free/page/", None))
			self.filmliste.insert(0, ("Italian Movies", "https://pandamovies.pw/watch-italian-porn-movies-online-free/page/", None))
			self.filmliste.insert(0, ("Spanish Movies", "https://pandamovies.pw/watch-spanish-porn-movies-online-free/page/", None))
			self.filmliste.insert(0, ("German Movies", "https://pandamovies.pw/watch-german-porns-movies-online-free/page/", None))
			self.filmliste.insert(0, ("Newest Movies", "https://pandamovies.pw/list-movies/page/", None))
			self.filmliste.insert(0, ("--- Search ---", "callSuchen", None))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self['name'].setText("")

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = urllib.quote(callback).replace(' ', '+')
			Link = self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(pandamovieListScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			if Name == "Studios" or Name == "Years":
				self.session.open(pandamovieGenreScreen, Link)
			else:
				self.session.open(pandamovieListScreen, Link, Name)

class pandamovieListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
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

		self['title'] = Label("PandaMovie")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.lastpage = 1
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_("Please wait..."))
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "https://pandamovies.pw/page/%s?s=%s" % (str(self.page), self.Link)
		else:
			url = self.Link + str(self.page)
		twAgentGetPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if "results for your search" in data:
			lastp = re.search('About\s(.*?)\sresults for your search', data, re.S)
			if lastp:
				lastp = lastp.group(1).replace(',','')
				lastp = round((float(lastp) / 18) + 0.5)
				self.lastpage = int(lastp)
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		elif "/director" in self.Link:
			lastp = re.search('- Page \d+ of (\d+) -', data, re.S)
			if lastp:
				lastp = lastp.group(1)
				self.lastpage = int(lastp)
			else:
				self.lastpage = self.page + 1
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self.getLastPage(data, "class='pagination'>(.*?)</nav>")
		raw = re.findall('class="ml-item.*?.*?href="(.*?)".*?data-original="(.*?)".*?mli-info">(.*?)</span', data, re.S)
		if raw:
			for (link, image, title) in raw:
				title = stripAllTags(title).strip()
				self.filmliste.append((decodeHtml(title), link, image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][0]
		if Link:
			Title = self['liste'].getCurrent()[0][1]
			Cover = self['liste'].getCurrent()[0][2]
			self.session.open(StreamAuswahl, Link, Title, Cover)

class StreamAuswahl(MPScreen):

	def __init__(self, session, Title, Link, Cover):
		self.Link = Link
		self.Title = Title
		self.Cover = Cover
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("PandaMovie")
		self['ContentTitle'] = Label("%s" %self.Title)
		self['name'] = Label(_("Please wait..."))

		self.filmliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.Cover)
		self.keyLocked = True
		url = self.Link
		twAgentGetPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('div id="pettabs">(.*?)</div', data, re.S)
		streams = re.findall('href=[\'|"](http[s]?://(?!(pandamovie.\w+|pandanetwork.\w+))(.*?)\/.*?)[\'|"|\&|<]', parse.group(1), re.S|re.I)
		if streams:
			for (stream, dummy, hostername) in streams:
				if isSupportedHoster(hostername, True):
					hostername = hostername.replace('www.','').replace('embed.','').replace('play.','')
					self.filmliste.append((hostername, stream))
			# remove duplicates
			self.filmliste = list(set(self.filmliste))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlisthoster, self.filmliste))
		self.keyLocked = False
		self['name'].setText("")

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		title = self.Title
		self.session.open(SimplePlayer, [(self.Title, stream_url, self.Cover)], showPlaylist=False, ltype='pandamovie', cover=True)