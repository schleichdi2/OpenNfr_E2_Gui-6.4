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

config_mp.mediaportal.itunestrailersquality = ConfigText(default="720p", fixed_size=False)

default_cover = "file://%s/itunesmovietrailers.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class itunestrailersGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"yellow": self.keyQuality
		}, -1)

		self.quality = config_mp.mediaportal.itunestrailersquality.value

		self['title'] = Label("iTunes Movie Trailers")
		self['ContentTitle'] = Label(_("Selection:"))
		self['F3'] = Label(self.quality)

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste = []
		self.genreliste.append(("Top Trailers", "https://trailers.apple.com/appletv/us/index.xml"))
		self.genreliste.append(("Calendar", "https://trailers.apple.com/appletv/us/calendar.xml"))
		self.genreliste.append(("Genres", "https://trailers.apple.com/appletv/us/browse.xml"))
		self.genreliste.append(("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = 'https://trailers.apple.com/trailers/global/atv/search.php?q=%s' % self.suchString
			Name = self['liste'].getCurrent()[0][0]
			self.session.open(itunestrailersFilmScreen, Link, Name, "Search")

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		if Name == "Genres" or Name == "Top Trailers" or Name == "Calendar":
			self.session.open(itunestrailersSubGenreScreen, Link, Name)

	def keyQuality(self):
		if self.keyLocked:
			return
		self.keyLocked = True
		if self.quality == "720p":
			self.quality = "1080p"
			config_mp.mediaportal.itunestrailersquality.value = "1080p"
		elif self.quality == "1080p":
			self.quality = "480p"
			config_mp.mediaportal.itunestrailersquality.value = "480p"
		elif self.quality == "480p":
			self.quality = "720p"
			config_mp.mediaportal.itunestrailersquality.value = "720p"

		config_mp.mediaportal.itunestrailersquality.save()
		configfile_mp.save()
		self['F3'].setText(self.quality)
		self.layoutFinished()

class itunestrailersSubGenreScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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

		self['title'] = Label("iTunes Movie Trailers")
		self['ContentTitle'] = Label(self.Name+":")
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		getPage(self.Link).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if self.Name == "Genres":
			raw = re.findall('<label>(.*?)</label>.*?<link>(.*?)</link>', data, re.S)
			if raw:
				for (Title, Url) in raw:
					self.genreliste.append((Title, Url, "Genres"))
		else:
			raw = re.findall('<collectionDivider.*?accessibilityLabel="(.*?)">', data, re.S)
			if raw:
				for Label in raw:
					self.genreliste.append((Label, self.Link, self.Name))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Cat = self['liste'].getCurrent()[0][2]
		self.session.open(itunestrailersFilmScreen, Link, Name, Cat)

class itunestrailersFilmScreen(MPScreen):

	def __init__(self, session, Link, Name, Cat):
		self.Link = Link
		self.Name = Name
		self.Cat = Cat
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("iTunes Movie Trailers")
		self['ContentTitle'] = Label(_("Movie Selection"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = self.Link
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if self.Cat == "Search":
			Movies = re.findall('MenuItem.*?loadURL\(\'(.*?)\'\).*?<label>(.*?)</label>.*?<image>(.*?)</image>', data, re.S|re.I)
		elif self.Cat == "Genres":
			Movies = re.findall('loadTrailerDetailPage\(\'(.*?)\'\);.*?<title>(.*?)</title>.*?<image>(.*?)</image>', data, re.S)
		elif self.Cat == "Top Trailers" or self.Cat == "Calendar":
			parse = re.search('<title>%s</title>(.*?)</shelf>' % self.Name, data, re.S)
			Movies = re.findall('loadTrailerDetailPage\(\'(.*?)\'\);.*?<title>(.*?)</title>.*?<image>(.*?)</image>', parse.group(1), re.S)
		if Movies:
			for (Url, Title, Image) in Movies:
				self.filmliste.append((decodeHtml(Title).replace('&amp;','&'), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(coverUrl)
		getPage(url).addCallback(self.getDescription).addErrback(self.dataError)

	def getDescription(self, data):
		description = re.search('<summary>(.*?)</summary>', data, re.S)
		if description:
			self['handlung'].setText(decodeHtml(description.group(1)))

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Cover = self['liste'].getCurrent()[0][2]
		self.session.open(itunestrailersSubFilmScreen, Link, Title, Cover)

class itunestrailersSubFilmScreen(MPScreen):

	def __init__(self, session, Link, Name, Cover):
		self.Link = Link
		self.Name = Name
		self.Cover = Cover
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("iTunes Movie Trailers")
		self['ContentTitle'] = Label(self.Name)

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		url = self.Link
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if re.search('id="more"', data):
			url = re.search('id="more".onSelect="atv.loadURL\(\'(.*?)\'\)', data, re.S|re.I)
			getPage(url.group(1)).addCallback(self.loadData2).addErrback(self.dataError)
		else:
			url = re.search('id="play".onSelect="atv.loadURL\(\'(.*?)\'\)', data, re.S|re.I)
			self.filmliste.append(("Trailer", url.group(1), self.Cover))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.showInfos()

	def loadData2(self, data):
		Movies = re.findall('MenuItem.*?loadURL\(\'(.*?)\'\).*?<label>(.*?)</label>.*?<image>(.*?)</image>', data, re.S|re.I)
		if Movies:
			for (Url, Title, Image) in Movies:
				if Title != "Related":
					self.filmliste.append((decodeHtml(Title).replace('&amp;','&'), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(coverUrl)
		getPage(url).addCallback(self.getDescription).addErrback(self.dataError)

	def getDescription(self, data):
		description = re.search('<description>(.*?)</description>', data, re.S)
		if description:
			self['handlung'].setText(decodeHtml(description.group(1)))

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getVideo).addErrback(self.dataError)

	def getVideo(self, data):
		video = re.search('<mediaURL>(.*?)</mediaURL>', data, re.S)
		Link = video.group(1)
		if config_mp.mediaportal.itunestrailersquality.value == "720p":
			Link = Link.replace('a720p.m4v','h720p.mov')
		elif config_mp.mediaportal.itunestrailersquality.value == "1080p":
			Link = Link.replace('a720p.m4v','h1080p.mov')
			Link = Link.replace('h720p.mov','h1080p.mov')
		elif config_mp.mediaportal.itunestrailersquality.value == "480p":
			Link = Link.replace('a720p.m4v','h480p.mov')
			Link = Link.replace('h720p.mov','h480p.mov')
		Title = self['liste'].getCurrent()[0][0]
		mp_globals.player_agent = "QuickTime/7.6.2 (qtver=7.6.2;os=Windows NT 5.1Service Pack 3)"
		self.session.open(SimplePlayer, [(self.Name + " - " + Title, Link, self.Cover)], showPlaylist=False, ltype='itunestrailers', cover=True)