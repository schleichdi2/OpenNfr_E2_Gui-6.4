# -*- coding: utf-8 -*-
##############################################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2018
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding execution on hardware, you are permitted to execute this plugin on VU+ hardware
#  which is licensed by satco europe GmbH, if the VTi image is used on that hardware.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
##############################################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

myagent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0'
BASE_NAME = "Mofos.com"
default_cover = "file://%s/mofos.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class mofosGenreScreen(MPScreen):

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

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		url = "http://www.mofos.com/tour/categories/"
		getPage(url, agent=myagent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('<a\shref="(.*?)".*?class="tag-list-card".*?img\ssrc="(.*?)".*?alt="(.*?)"', data, re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				Url = 'http://www.mofos.com%s' % Url
				if Image.startswith('//'):
					Image = 'http:' + Image
				self.genreliste.append((decodeHtml(Title), Url, Image))
			self.genreliste.sort()
		self.genreliste.insert(0, ("Series", 'http://www.mofos.com/tour/series/', default_cover))
		self.genreliste.insert(0, ("Sites", 'http://www.mofos.com/tour/sites/', default_cover))
		self.genreliste.insert(0, ("Girls", 'http://www.mofos.com/tour/girls/all-videos/all-models/all-categories/thismonth/toprated/', default_cover))
		self.genreliste.insert(0, ("Most Commented", 'http://www.mofos.com/tour/videos/all-videos/all-models/all-categories/alltime/comments/', default_cover))
		self.genreliste.insert(0, ("Most Viewed", 'http://www.mofos.com/tour/videos/all-videos/all-models/all-categories/alltime/mostviewed/', default_cover))
		self.genreliste.insert(0, ("Top Rated", 'http://www.mofos.com/tour/videos/all-videos/all-models/all-categories/alltime/toprated/', default_cover))
		self.genreliste.insert(0, ("Release Date", 'http://www.mofos.com/tour/videos/all-videos/all-models/all-categories/alltime/bydate/', default_cover))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		if not config_mp.mediaportal.premiumize_use.value:
			message = self.session.open(MessageBoxExt, _("%s only works with enabled MP premiumize.me option (MP Setup)!" % BASE_NAME), MessageBoxExt.TYPE_INFO, timeout=10)
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Sites":
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(mofosSitesScreen, Link, Name)
		elif Name == "Series":
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(mofosSitesScreen, Link, Name)
		elif Name == "Girls":
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(mofosGirlsScreen, Link, Name)
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(mofosFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback
			Name = "--- Search ---"
			Link = self.suchString.replace(' ', '+')
			self.session.open(mofosFilmScreen, Link, Name)

class mofosSitesScreen(MPScreen, ThumbsHelper):

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
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		getPage(self.Link, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		Sites = re.findall('collection-[card|box].*?href="(.*?)".*?img\ssrc="(.*?)".*?alt="(.*?)(?: - Mofos|)".*?scene-count">(.*?)<var', data, re.S)
		if Sites:
			for (Url, Image, Title, Scenes) in Sites:
				Url = "http://www.mofos.com" + Url.replace('/toprated/','/bydate/')
				if Title == "Mofos World Wide":
					Url = Url.replace('/mofos-vault/','/mofos-world-wide/')
				elif Title == "Milfs Like It Black":
					Url = Url.replace('/mofos-vault/','/milfs-like-it-black/')
				elif Title == "Mofos Old School":
					Url = Url.replace('/mofos-vault/','/mofos-old-school/')
				elif Title == "Teens At Work":
					Url = Url.replace('/mofos-vault/','/teens-at-work/')
				elif Title == "In Gang We Bang":
					Url = Url.replace('/mofos-vault/','/in-gang-we-bang/')
				elif Title == "Can She Take It":
					Url = Url.replace('/mofos-vault/','/can-she-take-it/')
				if Title != "Liveshows":
					Title = Title + " - %s Scenes" % Scenes.strip()
					if Image.startswith('//'):
						Image = 'http:' + Image
					self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No sites/series found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(mofosFilmScreen, Link, Name)

class mofosGirlsScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label(BASE_NAME)
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
		url = "%s%s/" % (self.Link, str(self.page))
		getPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</nav>', '.*title="\d+">(\d+)</a>')
		Girls = re.findall('class="list-model-card.*?href="(.*?)"\stitle="(.*?)".*?src="(.*?.jpg)"', data, re.S)
		if Girls:
			for (Url, Title, Image) in Girls:
				Url = "http://www.mofos.com" + Url
				Title = Title.lower().title()
				if Image.startswith('//'):
					Image = 'http:' + Image
				self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No pornstars found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, self.page, int(self.lastpage), 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(mofosFilmScreen, Link, Name)

class mofosFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label(BASE_NAME)
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
			if self.page == 1:
				url = "http://www.mofos.com/tour/search/videos/%s/" % self.Link
			else:
				url = "http://www.mofos.com/tour/search/videos/%s/%s/" % (self.Link, str(self.page))
		else:
			if self.page == 1:
				url = self.Link
			else:
				url = "%s%s/" % (self.Link, str(self.page))
		getPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</nav>')
		Movies = re.findall('widget-release-card.*?href="(.*?)".*?src="(.*?jpg).*?alt="(.*?)".*?class="site-name".*?>(.*?)</.*?class="rating">(\d+)\s{0,20}%{0,1}</span.*?views-count":\s"(.*?)".*?date-added">(.*?)\s{0,2}</span', data, re.S)
		if Movies:
			for (Url, Image, Title, Collection, Rating, Views, Date) in Movies:
				if Image.startswith('//////'):
					Image = Image.replace('//////','//')
				if Image.startswith('//'):
					Image = "http:" + Image
				Url = "http://www.mofos.com" + Url
				self.filmliste.append((decodeHtml(Title), Url, Image, Date, Collection, Rating, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, int(self.lastpage), mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		date = self['liste'].getCurrent()[0][3]
		coll = self['liste'].getCurrent()[0][4]
		rating = self['liste'].getCurrent()[0][5]
		views = self['liste'].getCurrent()[0][6]
		self['handlung'].setText("Date: "+date+'\nSite: '+coll.strip()+'\nViews: '+views+'\nRating: '+rating+" %")
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		get_stream_link(self.session).check_link(Link, self.play)

	def play(self, url):
		title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(title, url.replace('%2F','%252F').replace('%3D','%253D').replace('%2B','%252B'))], showPlaylist=False, ltype='mofos')