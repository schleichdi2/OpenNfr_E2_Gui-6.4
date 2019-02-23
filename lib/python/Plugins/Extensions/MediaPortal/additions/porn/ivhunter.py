# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

ivhagent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'

default_cover = "file://%s/ivhunter.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class ivhunterGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		if self.mode == "ivhunter":
			self.portal = "IVHUNTER"
			self.baseurl = "javdos.com"
			self.delim = "+"

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://%s/" % self.baseurl
		twAgentGetPage(url, agent=ivhagent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('href=[\'|\"].*?(\/studios\/.*?)[\'|\"].*?>(.*?)</a', data, re.S)
		if Cats:
			dup_items = set()
			for (Url, Title) in Cats:
				if not Url.startswith('http'):
					Url = 'http://' + self.baseurl + Url
				if Url.lower() not in dup_items:
					if Title != "Studios":
						self.genreliste.append((Title, Url.lower(), None))
						dup_items.add(Url.lower())
			self.genreliste = list(set(self.genreliste))
			self.genreliste.append(("Junior Idol", "http://%s/junior-idol/" % self.baseurl, None))
			self.genreliste.sort(key=lambda t : t[0].lower())
		self.genreliste.insert(0, ("HD", "http://%s/hd-video/" % self.baseurl, None))
		self.genreliste.insert(0, ("Newest", "http://%s/" % self.baseurl, None))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = urllib.quote(callback).replace(' ', self.delim)
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			self.session.open(ivhunterFilmScreen, Link, Name, self.portal, self.baseurl)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(ivhunterFilmScreen, Link, Name, self.portal, self.baseurl)

class ivhunterFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal, baseurl):
		self.Link = Link
		self.Name = Name
		self.portal = portal
		self.baseurl = baseurl
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions2", "MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"upUp" : self.key_repeatedUp,
			"rightUp" : self.key_repeatedUp,
			"leftUp" : self.key_repeatedUp,
			"downUp" : self.key_repeatedUp,
			"upRepeated" : self.keyUpRepeated,
			"downRepeated" : self.keyDownRepeated,
			"rightRepeated" : self.keyRightRepeated,
			"leftRepeated" : self.keyLeftRepeated,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label(self.portal)
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
			if self.page > 1:
				url = "http://%s/page/%s/?s=%s" % (self.baseurl, str(self.page), self.Link)
			else:
				url = "http://%s/?s=%s" % (self.baseurl, self.Link)
		else:
			if self.page > 1:
				url = self.Link + "page/" + str(self.page)
			else:
				url = self.Link
		twAgentGetPage(url, agent=ivhagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class=\'wp-pagenavi\'>(.*?)</div>', '.*\/page\/(\d+)')
		Movies = re.findall('id="post-\d+".*?clip-link.*?title="(.*?)"\shref="(.*?)".*?img\ssrc="(.*?)"', data, re.S)
		if Movies:
			for (Title, Url, Image) in Movies:
				if not Image and "/category/" in Url:
					pass
				else:
					if not Image.startswith('http'):
						Image = 'http://' + self.baseurl + Image
					Image = Image.replace('https://pics.dmm.co.jp','http://pics.dmm.co.jp').replace('https://pics.dmm.com','http://pics.dmm.co.jp')
					if not Url.startswith('http'):
						Url = 'http://' + self.baseurl + Url
					self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.loadPicQueued()

	def showInfos(self):
		CoverHelper(self['coverArt']).getCover(default_cover)
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)

	def loadPic(self):
		if self.picQ.empty():
			self.eventP.clear()
			return
		while not self.picQ.empty():
			self.picQ.get_nowait()
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		self.showInfos()
		self.updateP = 1
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		url = self['liste'].getCurrent()[0][1]
		if url:
			twAgentGetPage(url, agent=ivhagent).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		streams = re.findall('<iframe\ssrc="((?:http[s]?|)//javdos.com/embed.*?)"', data, re.S)
		if streams:
			url = streams[0]
			if url.startswith('//'):
				url = 'http:' + url
			twAgentGetPage(url, agent=ivhagent).addCallback(self.loadStreamData).addErrback(self.dataError)

	def loadStreamData(self, data):
		js = re.findall('<script type="text/javascript">(.*?)</script>', data, re.S)
		if js:
			for item in js:
				if "monday" in item:
					js = item
					break
			monday = re.findall('clientSide.init\((monday.*?\))\);', data, re.S)
			if monday:
				js = js + "vidurl = " + monday[0] + ";return vidurl;"
				try:
					import execjs
					node = execjs.get("Node")
					url = str(node.exec_(js))
					get_stream_link(self.session).check_link(url, self.got_link)
					self.keyLocked = False
				except:
					self.session.open(MessageBoxExt, _("This plugin requires packages python-pyexecjs and nodejs."), MessageBoxExt.TYPE_INFO)
			else:
				message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)
				self.keyLocked = False
		else:
			message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)
			self.keyLocked = False

	def got_link(self, stream_url):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		mp_globals.player_agent = ivhagent
		self.session.open(SimplePlayer, [(title, stream_url)], showPlaylist=False, ltype='ivhunter')