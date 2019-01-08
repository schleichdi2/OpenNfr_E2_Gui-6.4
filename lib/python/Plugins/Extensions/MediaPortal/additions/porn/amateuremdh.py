# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.DelayedFunction import DelayedFunction

myagent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'

default_cover = "file://%s/amateuremdh.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class amaMDHtoGenreScreen(MPScreen):

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

		self['title'] = Label("Amateure-MyDirtyHobby")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.genreliste.insert(0, ("Pornstars - Most Viewed", "https://amateure.mydirtyhobby.to/pornstars?o=mv&page="))
		self.genreliste.insert(0, ("Pornstars - Top Rated", "https://amateure.mydirtyhobby.to/pornstars?o=tr&page="))
		self.genreliste.insert(0, ("Pornstars - Most Recent", "https://amateure.mydirtyhobby.to/pornstars?o=mr&page="))
		self.genreliste.insert(0, ("Being Watched", "https://amateure.mydirtyhobby.to/videos?o=bw&type=public&page="))
		self.genreliste.insert(0, ("Most Viewed", "https://amateure.mydirtyhobby.to/videos?o=mv&type=public&page="))
		self.genreliste.insert(0, ("Top Rated", "https://amateure.mydirtyhobby.to/videos?o=tr&type=public&page="))
		self.genreliste.insert(0, ("Most Recent", "https://amateure.mydirtyhobby.to/videos?o=mr&type=public&page="))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		else:
			self.session.open(amaMDHtoFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = self.suchString.replace(' ', '+')
			self.session.open(amaMDHtoFilmScreen, Link, Name)

class amaMDHtoFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber,
			"yellow" : self.keyRelated
		}, -1)

		self['title'] = Label("Amateure-MyDirtyHobby")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		if not self.Name.startswith("Pornstar"):
			self['F3'] = Label(_("Related"))

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
			url = "https://amateure.mydirtyhobby.to/search/videos?search_query=%s&type=public&page=%s" % (self.Link, str(self.page))
		else:
			url = self.Link + str(self.page)
		getPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</div>', '.*[>|=](\d+)[<|&|\/span]')
		if self.Name.startswith("Pornstar"):
			Pornstars = re.findall('<div class="col-xs-6 col-sm-3 col-lg-2b model-pad">.*?class="model-sh" href="(.*?)">.*?<img class="img-responsive" src="(.*?)"/>.*?class="model-title title-small">(.*?)</span>.*?class="pull-left model-stat title-tiny"><i class="fa fa-film"></i>\s{0,1}(\d+)</span>', data, re.S)
			if Pornstars:
				for (Url, Image, Title, Count) in Pornstars:
					if int(Count) < 1:
						continue
					Url = "https://amateure.mydirtyhobby.to" + Url + "?page="
					Image = "https://amateure.mydirtyhobby.to" + Image
					self.filmliste.append((decodeHtml(Title), Url, Image, "star"))
			if len(self.filmliste) == 0:
				self.filmliste.append((_('No pornstars found!'), '', None, "star"))
		else:
			Movies = re.findall('class="well well-sm.*?href="(.*?)".*?img\ssrc="(.*?)"\stitle="(.*?)"', data, re.S)
			if Movies:
				for (Url, Image, Title) in Movies:
					Url = "https://amateure.mydirtyhobby.to" + Url
					self.filmliste.append((decodeHtml(Title), Url, Image, "video"))
			if len(self.filmliste) == 0:
				self.filmliste.append((_('No videos found!'), '', None, "video"))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1, agent=myagent)
		self.showInfos()
		self.keyLocked = False

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic, agent=myagent)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		type = self['liste'].getCurrent()[0][3]
		if type == "video":
			self.keyLocked = True
			getPage(Link, agent=myagent).addCallback(self.getVideoUrl).addErrback(self.dataError)
		else:
			self.session.open(amaMDHtoFilmScreen, Link, Name)

	def keyRelated(self):
		if self.Name.startswith("Pornstar"):
			return
		Link = self['liste'].getCurrent()[0][0]
		if " - " in Link:
			Link = Link.split(' - ')[0]
			Name = "--- Search ---"
			self.session.open(amaMDHtoFilmScreen, Link, Name)

	def getVideoUrl(self, data):
		if "This is a premium video" in data:
			self.session.open(MessageBoxExt, _("Sorry this is a premium video which is not available."), MessageBoxExt.TYPE_INFO, timeout=5)
			self.keyLocked = False
			return
		url = re.findall('iframe\ssrc="(.*?)"', data, re.S|re.I)
		if url:
			get_stream_link(self.session).check_link(url[0], self.got_link)
			self.keyLocked = False

	def got_link(self, url):
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='amateuremdh')