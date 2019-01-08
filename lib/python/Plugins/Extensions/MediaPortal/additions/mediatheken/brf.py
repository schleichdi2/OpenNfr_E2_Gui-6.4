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

default_cover = "file://%s/brf.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class brfGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("BRF Mediathek")
		self['ContentTitle'] = Label("Genre:")

		self.suchString = ''
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.filmliste.append(("Suche", '', default_cover))
		self.filmliste.append(("Blickpunkt", 'https://m.brf.be/blickpunkt/page/'))
		self.filmliste.append(("Beiträge", 'https://m.brf.be/beitraege/page/'))
		self.filmliste.append(("Reportagen", 'https://m.brf.be/reportagen/page/'))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "Suche":
			self.suchen()
		else:
			self.session.open(brfListScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback
			Name = "Suche"
			Link = callback.replace(' ', '+')
			self.session.open(brfListScreen, Link, Name)

class brfListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("BRF Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.lastpage = 1
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		if self.Name == "Suche":
			url = "https://m.brf.be/page/%s?s=%s" % (str(self.page), self.Link)
		else:
			url = self.Link + str(self.page)
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if ">Weitere laden</a>" in data:
			self.lastpage = self.page + 1
		self['page'].setText(str(self.page) + " / " + str(self.lastpage))
		raw = re.findall('class="thumb-wrapper">.*?href="(.*?)"\stitle="(.*?)".*?<img.*?src="(.*?)\-\d+x\d+\.jpg".*?<time>(.*?)</time>', data, re.S)
		if raw:
			for (Url, Title, Image, Date) in raw:
				Image = Image + ".jpg"
				self.filmliste.append((decodeHtml(Title), Url, Image, Date))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"), None, default_cover, ""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page+1, self.lastpage, mode=1, pagefix=-1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		handlung = "Datum: " + self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			getPage(url).addCallback(self.getDataStream).addErrback(self.dataError)

	def getDataStream(self, data):
		videopage = re.findall('jQuery.get\("(.*?)"\)', data, re.S)
		if videopage:
			getPage(videopage[0]).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		stream = re.findall('<source src="(.*?)"', data, re.S)
		if stream:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(title, stream[0])], showPlaylist=False, ltype='brf')