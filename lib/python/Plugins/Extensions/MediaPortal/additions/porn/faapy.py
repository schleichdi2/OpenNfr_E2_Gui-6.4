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

default_cover = "file://%s/faapy.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class faapyGenreScreen(MPScreen):

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

		self['title'] = Label("Faapy.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://faapy.com"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="categories-drop">.*?<ul>(.*?)</ul>', data, re.S)
		Cats = re.findall('href="(.*?)"\stitle="(.*?)"', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				self.genreliste.append((Title, Url))
			self.genreliste.sort()
		self.genreliste.insert(0, ("Channels", "http://faapy.com/channels"))
		self.genreliste.insert(0, ("Top Rated (All Time)", "http://faapy.com/top-rated/"))
		self.genreliste.insert(0, ("Top Rated (Monthly)", "http://faapy.com/top-rated/month/"))
		self.genreliste.insert(0, ("Top Rated (Weekly)", "http://faapy.com/top-rated/week/"))
		self.genreliste.insert(0, ("Top Rated (Daily)", "http://faapy.com/top-rated/today/"))
		self.genreliste.insert(0, ("Most Popular (All Time)", "http://faapy.com/most-popular/"))
		self.genreliste.insert(0, ("Most Popular (Monthly)", "http://faapy.com/most-popular/month/"))
		self.genreliste.insert(0, ("Most Popular (Weekly)", "http://faapy.com/most-popular/week/"))
		self.genreliste.insert(0, ("Most Popular (Daily)", "http://faapy.com/most-popular/today/"))
		self.genreliste.insert(0, ("Latest", "http://faapy.com/"))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		elif Name == "Channels":
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(faapyChannelsScreen, Link, Name)
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(faapyFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = self.suchString
			self.session.open(faapyFilmScreen, Link, Name)

class faapyChannelsScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("Faapy.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)

		self.keyLocked = True
		self.page = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self['F2'].setText(_("Page"))
		self['Page'].setText(_("Page:"))

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = self.Link + "/%s/" % self.page
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</ul>')
		parse = re.search('class="heading">(.*?)class="footer', data, re.S)
		Movies = re.findall('<a\shref="(.*?/)"\stitle="(.*?)">.*?img\ssrc="(.*?)"', parse.group(1), re.S)
		if Movies:
			for (Url, Title, Image) in Movies:
				if Image.startswith('//'):
					Image = "http:" + Image
				self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('Parsing error!'), None))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage)
		self.showInfos()
		self.keyLocked = False

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(faapyFilmScreen, Link, Name)

class faapyFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("Faapy.com")
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
			url = "http://faapy.com/search/%s/?q=%s" % (str(self.page), self.Link)
		else:
			url = "%s%s/" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</ul>')
		Movies = re.findall('class="thumb".*?\s*href="(.*?)"\stitle="(.*?)".*?img\ssrc="(.*?)".*?class="icon-eye"></i>(\d+)\s*</span>', data, re.S)
		if Movies:
			for (Url, Title, Image, Views) in Movies:
				if Image.startswith('//'):
					Image = "http:" + Image
				self.filmliste.append((decodeHtml(Title), Url, Image, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()
		self.keyLocked = False

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		views = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText("Views: %s\n" % views)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link).addCallback(self.getVideoUrl).addErrback(self.dataError)

	def getVideoUrl(self, data):
		videoUrl = re.findall("video_url:\s'(.*?)',", data, re.S)
		if videoUrl:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, videoUrl[-1])], showPlaylist=False, ltype='faapy')