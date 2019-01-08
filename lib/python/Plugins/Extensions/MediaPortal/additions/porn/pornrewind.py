# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

myagent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'
default_cover = "file://%s/pornrewind.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class pornrewindGenreScreen(MPScreen):

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

		self['title'] = Label("PornRewind.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "https://www.pornrewind.com/categories/?sort_by=title"
		twAgentGetPage(url, agent=myagent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('thumb-categories"\shref="(.*?)"\stitle="(.*?)".*?data-src="(.*?)"', data, re.S)
		if Cats:
			for (Url, Title, Image) in Cats:
				Url = Url + "%s/"
				self.genreliste.append((Title, Url, Image))
		self.genreliste.sort()
		self.genreliste.insert(0, ("Top Rated", "https://www.pornrewind.com/videos/%s/?sort_by=rating", default_cover))
		self.genreliste.insert(0, ("Most Popular", "https://www.pornrewind.com/videos/%s/?sort_by=video_viewed", default_cover))
		self.genreliste.insert(0, ("Most Recent", "https://www.pornrewind.com/videos/%s/?sort_by=post_date", default_cover))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '-')
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			self.session.open(pornrewindFilmScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(pornrewindFilmScreen, Link, Name)

class pornrewindFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("PornRewind.com")
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
			url = "https://www.pornrewind.com/search/%s/%s/?mode=async&function=get_block&block_id=list_videos_common_videos_list" % (self.Link, str(self.page))
		else:
			url = self.Link % str(self.page)
		twAgentGetPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</ul>')
		Movies = re.findall('class="thumb"\shref="(.*?)"\stitle="(.*?)".*?data-src="(.*?)".*?thumb-time">[\t\n\r\s]+<span>(.*?)</span.*?thumb-added">[\t\n\r\s]+<span>(.*?)</span.*?thumb-viewed">[\t\n\r\s]+<span>(.*?)</span', data, re.S)
		if Movies:
			for (Url, Title, Image, Runtime, Added, Views) in Movies:
				Views = Views.strip().replace(' ','')
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

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		if url:
			self.session.open(pornrewindFilmAuswahlScreen, title, url, image)

class pornrewindFilmAuswahlScreen(MPScreen):

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
		self['title'] = Label("PornRewind.com")
		self['ContentTitle'] = Label("Streams")
		self['name'] = Label(self.genreName)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		twAgentGetPage(self.genreLink, agent=myagent).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		streams = re.findall('iframe (?:src|href)=[\'|"](http[s]?://(.*?)\/.*?)[\'|"|\&|<]', data, re.S|re.I)
		if streams:
			for (stream, hostername) in streams:
				if isSupportedHoster(hostername, True):
					hostername = hostername.replace('www.','').replace('embed.','').replace('play.','')
					self.filmliste.append((hostername, stream))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No supported streams found!'), None))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		CoverHelper(self['coverArt']).getCover(self.cover)

	def keyOK(self):
		if self.keyLocked:
			return
		hoster = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if url:
			url = url.replace('&amp;','&').replace('&#038;','&')
			get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		title = self.genreName
		self.session.open(SimplePlayer, [(title, stream_url)], showPlaylist=False, ltype='pornrewind')