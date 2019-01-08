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

default_cover = "file://%s/autobild.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class autoBildGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Autobild.de")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Alle Videos", "videos/"))
		self.genreliste.append(("Tests", "videos/tests/"))
		self.genreliste.append(("Fahrberichte", "videos/fahrberichte/"))
		self.genreliste.append(("Neuvorstellungen", "videos/neuvorstellungen/"))
		self.genreliste.append(("Motorsounds", "videos/motorsounds/"))
		self.genreliste.append(("Erlkönige", "videos/erlkoenige/"))
		self.genreliste.append(("Klassik", "videos/klassik/"))
		self.genreliste.append(("Messen", "videos/messen/"))
		self.genreliste.append(("Ratgeber", "videos/ratgeber/"))
		self.genreliste.append(("Sportscars", "videos/sportscars/"))
		self.genreliste.append(("Aktionen", "videos/aktionen/"))
		self.genreliste.append(("Motorsport", "videos/motorsport/"))
		self.genreliste.append(("Michelin", "index_4365831.html"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		streamGenreLink = "http://www.autobild.de/" + self['liste'].getCurrent()[0][1] + "?page="
		self.session.open(autoBildFilmListeScreen, streamGenreLink, Name)

class autoBildFilmListeScreen(MPScreen, ThumbsHelper):
	def __init__(self, session, streamGenreLink, Name):
		self.streamGenreLink = streamGenreLink
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("Autobild.de")
		self['ContentTitle'] = Label("Spot Auswahl: %s" % self.Name)
		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.filmliste = []
		self.keckse = {}
		self.page = 1
		self.lastpage = 999
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "%s%s" % (self.streamGenreLink, str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		videos = re.findall('<div class="horizontal teaser clearfix">.*?<div class="pictureblock"><img src="(.*?)".*?<h2 class="kicker"><a href="(.*?)">(?:Video:\s|)(.*?)</a>.*?<p class="headline">(.*?)</p>.*?<p class="text">(.*?)</p>', data, re.S)
		if videos:
			self.filmliste = []
			for (image,url,title,headline,handlung) in videos:
				title = headline + " - " + title
				self.filmliste.append((decodeHtml(title), url, image, handlung))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		streamPic = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(streamName)
		self['handlung'].setText(decodeHtml(handlung))
		self['page'].setText(str(self.page))
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		url = "%s%s" % (streamLink ,"?getjson=1")
		getPage(url).addCallback(self.findStream).addErrback(self.dataError)

	def findStream(self, data):
		self.keyLocked = False
		streamname = self['liste'].getCurrent()[0][0]
		stream_url = re.findall('"src":"http[s]?:(.*?).mp4"', data, re.S)
		urlConv = 'http:' + stream_url[0].replace('\\', '') + '.mp4'
		if stream_url:
			self.session.open(SimplePlayer, [(streamname, urlConv)], showPlaylist=False, ltype='autobild')