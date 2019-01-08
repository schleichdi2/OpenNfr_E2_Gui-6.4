# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
default_cover = "file://%s/vidz7.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class Vidz7GenreScreen(MPScreen):

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

		self['title'] = Label("Vidz7.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = 'http://www.vidz7.com/tags/'
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		cats = re.findall('<li><a href="(.*?)(?:\?kd=4)">(.*?)</a><span>(.*?)</span></li>', data, re.S)
		if cats:
			for (url, title, count) in cats:
				if int(count.strip()) > 250:
					url = url + "page/$$PAGE$$/"
					self.genreliste.append((decodeHtml(title).title(), url, default_cover))
		self.genreliste.sort()
		self.genreliste.insert(0, ("Longest", "http://www.vidz7.com/page/$$PAGE$$/?orderby=duration", default_cover))
		self.genreliste.insert(0, ("Most Viewed", "http://www.vidz7.com/page/$$PAGE$$/?orderby=view", default_cover))
		self.genreliste.insert(0, ("Newest", "http://www.vidz7.com/page/$$PAGE$$/?orderby=date", default_cover))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(Vidz7FilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = '%s' % self.suchString.replace(' ', '+')
			self.session.open(Vidz7FilmScreen, Link, Name)

class Vidz7FilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("Vidz7.com")
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
		i = 0
		url = ''
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://www.vidz7.com/page/%s/?s=%s"  % (str(self.page), self.Link)
		else:
			url = self.Link.replace('$$PAGE$$',str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '<nav class="pagination(.*?)</nav>')
		videos = re.findall('<article.*?href=\'(.*?)\'.*?image:url\("(.*?)"\).*?class="duration">(.*?)</div.*?class=\'info-card\'>(.*?)</a.*?class="video-date".*?">(.*?)</time.*?<span>(?:\s/\s)(.*?)\sviews</span', data, re.S)
		if videos:
			for (url, image, runtime, title, date, views) in videos:
				title = stripAllTags(title).strip()
				if title.endswith('...') or title == "":
					tmp1 = stripAllTags(title).split(' ')[0]
					tmp2 = url.split('/')[6].lower().replace(tmp1.lower(),'').replace('_',' ').replace('-',' ').strip()
					title = tmp1 + " " + tmp2
					title = ' '.join(s[:1].upper() + s[1:] for s in stripAllTags(title).split(' '))
					title = title.strip()
				self.filmliste.append((decodeHtml(title), url, image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link:
			getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('<iframe src="(.*?)"', data, re.S|re.I)
		if videoPage:
			get_stream_link(self.session).check_link(str(videoPage[0]), self.got_link)

	def got_link(self, stream_url):
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Title, stream_url)], cover=False, showPlaylist=False, ltype='vidz7')