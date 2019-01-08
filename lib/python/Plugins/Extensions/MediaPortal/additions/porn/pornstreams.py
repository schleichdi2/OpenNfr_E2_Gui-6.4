# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

myagent = 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'

default_cover = "file://%s/pornstreams.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class PornStreamsGenreScreen(MPScreen):

	def __init__(self, session, mode=''):
		self.mode = mode
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("PornStreams.eu")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		if self.mode == "Studios":
			url = "http://pornstreams.eu/studios/"
		else:
			url = "http://pornstreams.eu/"
		twAgentGetPage(url, agent=myagent, gzip_decoding=True).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		if self.mode == 'Studios':
			Cats =  re.findall('<a\stitle="(.*?)"\shref="(.*?)">.*?</a>', data, re.S)
			if Cats:
				for (Title, Url) in Cats:
					Url = Url + 'page/'
					if not Title.startswith('['):
						if not '.png' in Title:
							if not '%d1%81lips4sale' in Url:
								self.genreliste.append((decodeHtml(Title), Url))
		else:
			parse = re.search('<span>Categories</span>(.*?)</div>', data, re.S)
			Cats = re.findall('cat-item-\d+"><a\shref="(.*?)"\s{0,1}>(.*?)(?:\sVideos|\sPorn|)</a>', parse.group(1), re.S)
			if Cats:
				for (Url, Title) in Cats:
					Url = Url + 'page/'
					self.genreliste.append((decodeHtml(Title), Url))
		# remove duplicates
		self.genreliste = list(set(self.genreliste))
		self.genreliste.sort(key=lambda t : t[0].lower())
		if self.mode != "Studios":
			self.genreliste.insert(0, ("Studios", None, None))
			self.genreliste.insert(0, ("Newest", "http://pornstreams.eu/page/", None))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			self.session.open(PornStreamsFilmScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Studios":
			self.session.open(PornStreamsGenreScreen, "Studios")
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(PornStreamsFilmScreen, Link, Name)

class PornStreamsFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("PornStreams.eu")
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
			url = "http://www.pornstreams.eu/page/" + str(self.page) + "/?s=" + self.Link
		else:
			url = self.Link + str(self.page)
		if "/page/1" in url: url = url.replace('/page/1','')
		twAgentGetPage(url, agent=myagent, gzip_decoding=True).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', ">Page.*?of\s(.*?)</span")
		Movies = re.findall('class="featured-image">.*?href="(.*?)"\stitle="(.*?)"><img.*?srcset="(.*?)(?:\s|")', data, re.S)
		if Movies:
			for (Url, Title, Image) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None))
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
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		if url:
			self.session.open(PornStreamsFilmAuswahlScreen, title, url, image)

class PornStreamsFilmAuswahlScreen(MPScreen):

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
		self['title'] = Label("PornStreams.eu")
		self['ContentTitle'] = Label("Streams")
		self['name'] = Label(self.genreName)

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		twAgentGetPage(self.genreLink, agent=myagent, gzip_decoding=True).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		streams = re.findall('(?:src|href)=[\'|"](http[s]?://(?!(pornstreams.eu))(.*?)\/.*?)[\'|"|\&|<]', data, re.S|re.I)
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

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			get_stream_link(self.session).check_link(url, self.got_link)

	def got_link(self, stream_url):
		title = self.genreName
		self.session.open(SimplePlayer, [(title, stream_url, self.cover)], showPlaylist=False, ltype='pornstreams', cover=True)