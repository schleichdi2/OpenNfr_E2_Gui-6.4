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

dreiurl = "http://www.3sat.de"
baseurl = "http://www.3sat.de/mediathek/"
default_cover = "file://%s/3sat.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class dreisatGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
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
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("3sat Mediathek")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.suchString = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = baseurl + "?mode=sendungenaz0"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.filmliste.append(("Suche", '', default_cover))
		self.filmliste.append(("Sendung verpasst!?", '', default_cover))
		raw = re.findall('class="mediatheklistbox.*?_hover".*?href="(.*?)".*?img\sclass=.*?MediathekListPic"\salt="(.*?)"\ssrc="(.*?)"', data, re.S)
		if raw:
			for (Url, Title, Image) in raw:
				Image = dreiurl + Image.replace('161x90','946x532')
				if not Url.startswith('http'):
					Url = 'http:' + Url
				self.filmliste.append((decodeHtml(Title), Url, Image))
		url = baseurl + "?mode=sendungenaz1"
		getPage(url).addCallback(self.parseData2).addErrback(self.dataError)

	def parseData2(self, data):
		raw = re.findall('class="mediatheklistbox.*?_hover".*?href="(.*?)".*?img\sclass=.*?MediathekListPic"\salt="(.*?)"\ssrc="(.*?)"', data, re.S)
		if raw:
			for (Url, Title, Image) in raw:
				Image = dreiurl + Image.replace('161x90','946x532')
				if not Url.startswith('http'):
					Url = 'http:' + Url
				self.filmliste.append((decodeHtml(Title), Url, Image))
				self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		ImageUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(ImageUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "Suche":
			self.suchen()
		elif Name == 'Sendung verpasst!?':
			self.session.open(dreisatDateScreen, Link, Name)
		else:
			self.session.open(dreisatListScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '-')
			Name = "Suche"
			Link = '%s?mode=suche&query=%s' % (baseurl, self.suchString)
			self.session.open(dreisatListScreen, Link, Name)

class dreisatDateScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("3sat Mediathek")
		self['ContentTitle'] = Label("Sendung verpasst!?")
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		today = datetime.date.today()
		for daynr in range(0,356):
			day1 = today - datetime.timedelta(days=daynr)
			dateselect = day1.strftime('%Y-%m-%d')
			link = '%sindex.php?datum=%s&cx=133' % (baseurl, day1.strftime('%Y%m%d'))
			self.filmliste.append((dateselect, link, ''))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(dreisatListScreen, Link, Name)

class dreisatListScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("3sat Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 0
		self.lastpage = 0
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = self.Link + "&mode=verpasst" + str(self.page)
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		lastpage = re.search('class="ClnNextNblEnd".*?mode=(suche|verpasst)([\d]+)\&amp;', data, re.S)
		if lastpage:
			self.lastpage = int(lastpage.group(2))+1
			self['page'].setText("%s / %s" % (str(self.page+1), str(self.lastpage)))
		else:
			lastpage = re.search('ClnInfo.*?class="mediathek_menu_.*?([\d]+)&nbsp;.*?class="ClnNextLock', data, re.S)
			if lastpage:
				self.lastpage = int(lastpage.group(1))
				self['page'].setText("%s / %s" % (str(self.page+1), str(self.lastpage)))
			else:
				self.lastpage = 0
				self['page'].setText("%s / 1" % str(self.page+1))
		raw = re.findall('BoxPicture.*?src="(.*?)".*?BoxHeadline.*?href=".*?obj=(.*?)">(.*?)<.*?FloatText.*?href=".*?">(.*?)</a>', data, re.S)
		if raw:
			for (Image, id, Title, Handlung) in raw:
				Image = dreiurl + "%s" % Image.replace('161x90','946x532')
				Handlung = Handlung.replace('<b>','').replace('</b>','')
				self.filmliste.append((decodeHtml(Title), id, Image, Handlung))
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
		handlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText(decodeHtml(handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyPageDown(self):
		if self.keyLocked:
			return
		if not self.page < 1:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.keyLocked:
			return
		if self.page+1 < self.lastpage:
			self.page += 1
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		self.title = self['liste'].getCurrent()[0][0]
		id = self['liste'].getCurrent()[0][1]
		if id:
			url = baseurl + "xmlservice/web/beitragsDetails?ak=web&id=%s" % id.replace('amp;','')
			getPage(url).addCallback(self.getDataStream).addErrback(self.dataError)

	def getDataStream(self, data):
		stream = re.findall('basetype="h264_aac_mp4_http_na_na"(?:\sisDownload="false"|)>.<quality>veryhigh</quality>.<url>(http://[tvdl|nrodl|rodl].*?zdf.de.*?.mp4)</url>', data, re.S)
		if stream:
			url = stream[0]
			playlist = []
			playlist.append((self.title, url))
			self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='3sat')