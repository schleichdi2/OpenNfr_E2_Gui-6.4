# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

myagent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'
default_cover = "file://%s/javhd.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class javhdGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("JavHD.today")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://javhd.today/categories/"
		twAgentGetPage(url, agent=myagent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('class="category".*?href="(.*?)".*?img\ssrc="(.*?)".*?title">(.*?)</div', data, re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				Url = 'http://javhd.today/' + Url
				Image = 'http://javhd.today/' + Image
				self.genreliste.append((Title, Url, Image, True))
		self.genreliste.sort()
		self.genreliste.insert(0, ("Being Watched", "http://javhd.today/watched/", default_cover, False))
		self.genreliste.insert(0, ("Longest", "http://javhd.today/longest/", default_cover, False))
		self.genreliste.insert(0, ("Most Downloaded", "http://javhd.today/downloaded/", default_cover, False))
		self.genreliste.insert(0, ("Most Discussed", "http://javhd.today/discussed/", default_cover, False))
		self.genreliste.insert(0, ("Top Rated", "http://javhd.today/rated/", default_cover, False))
		self.genreliste.insert(0, ("Most Popular", "http://javhd.today/popular/", default_cover, False))
		self.genreliste.insert(0, ("Most Recent", "http://javhd.today/recent/", default_cover, False))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover, False))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			self.session.open(javhdFilmScreen, Link, Name, False)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			Cat = self['liste'].getCurrent()[0][3]
			self.session.open(javhdFilmScreen, Link, Name, Cat)

class javhdFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Cat):
		self.Link = Link
		self.Name = Name
		self.Cat = Cat
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

		self['title'] = Label("JavHD.today")
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
			url = "http://javhd.today/search/video/?s=%s&page=%s" % (self.Link, str(self.page))
		else:
			if self.page > 1:
				if self.Cat:
					cat = "recent/"
				else:
					cat = ""
				url = self.Link + cat + str(self.page) + "/"
			else:
				url = self.Link
		twAgentGetPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination(.*?)</ul>')
		Movies = re.findall('class="video".*?href="(.*?)"\stitle="(.*?)".*?img\ssrc="(.*?)".*?class="video-overlay.*?>(.*?)</span.*?pull-left">(.*?)</span.*?text-right">(\d+)', data, re.S)
		if Movies:
			for (Url, Title, Image, Runtime, Added, Views) in Movies:
				Url = "http://javhd.today" + Url
				if not Image.startswith('http'):
					Image = "http://javhd.today" + Image
				Runtime = Runtime.strip()
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Added, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None, None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		Url = self['liste'].getCurrent()[0][1]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		added = self['liste'].getCurrent()[0][4]
		views = self['liste'].getCurrent()[0][5]
		self['handlung'].setText("Runtime: %s\nAdded: %s\nViews: %s" % (runtime, added, views))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		if url:
			self.keyLocked = True
			twAgentGetPage(url, agent=myagent).addCallback(self.loadStream).addErrback(self.dataError)

	def loadStream(self, data):
		streams = re.findall('<iframe.*?src="(https://www.fembed.com/v/.*?)\s{0,1}"', data, re.S)
		if streams:
			get_stream_link(self.session).check_link(streams[0], self.got_link)
		else:
			streams = re.findall('(?:src|href)=[\'|"](http[s]?://(?!(?:www.|m.|)javhd.today)(.*?)\/.*?)[\'|"|\&|<]', data, re.S|re.I)
			if streams:
				for (stream, hostername) in streams:
					if isSupportedHoster(hostername, True):
						url = stream.replace('&amp;','&').replace('&#038;','&').strip()
						get_stream_link(self.session).check_link(url, self.got_link)
		self.keyLocked = False

	def got_link(self, stream_url):
		title = self['liste'].getCurrent()[0][0]
		cover = self['liste'].getCurrent()[0][2]
		self.session.open(SimplePlayer, [(title, stream_url, cover)], showPlaylist=False, ltype='javhd', cover=True)