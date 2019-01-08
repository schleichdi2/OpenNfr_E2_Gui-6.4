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
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

BASE_URL = 'http://www.kindertube.de/'

default_cover = "file://%s/kindertube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class kindertubeMain(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("KinderTube")
		self['ContentTitle'] = Label(_("Genre Selection"))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.streamList.append(("0-2 jährige", BASE_URL+'/kleinkind-filme-0-2-jahre.html'))
		self.streamList.append(("Kleinkinder", BASE_URL+'/serien-für-kleinkinder.html'))
		self.streamList.append(("Lehrfilme", BASE_URL+'/lehrfilme-für-kinder.html'))
		self.streamList.append(("Musik", BASE_URL+'/musik-für-kinder.html'))
		self.streamList.append(("Alle Filme", BASE_URL+'/alle-filme-und-serien.html'))
		self.streamList.append(("Serien von früher", BASE_URL+'/alte-kinderserien.html'))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.showInfos()

	def keyOK(self):
		auswahl = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(kindertubeParsing, auswahl, url)

class kindertubeParsing(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("KinderTube")
		self['ContentTitle'] = Label("%s" % self.genre)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList.append((_('Please wait...'), None))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		self.streamList = []
		getPage(self.url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		pls = re.findall('<a href="(.*?)" class="col.*?"><div class="thumb"><img src="(image.*?)" alt="" class="img-thumbnail"></div><span class="title">(.*?)\n</span></a>', data)
		if pls:
			for (url, image, title) in pls:
				title = title.replace(' - alte kinderserien', '')
				image = BASE_URL+'/'+image
				self.streamList.append((decodeHtml(title), url, image))

		if len(self.streamList) == 0:
			self.streamList.append((_('Parsing error!'), None, None))
			self.keyLocked = True
		else:
			self.keyLocked = False

		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream_name = self['liste'].getCurrent()[0][0]
		movie_url = self['liste'].getCurrent()[0][1]
		cover_url = self['liste'].getCurrent()[0][2]
		self.session.open(kindertubeEpisoden, stream_name, movie_url, cover_url)

	def showInfos(self):
		filmName = self['liste'].getCurrent()[0][0]
		self['name'].setText(filmName)

class kindertubeEpisoden(MPScreen, ThumbsHelper):

	def __init__(self, session, genre, url, cover):
		self.genre = genre
		self.url = url
		self.cover = cover
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0": self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("KinderTube")
		self['ContentTitle'] = Label("%s" % self.genre)

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		CoverHelper(self['coverArt']).getCover(self.cover)
		self.streamList.append((_('Please wait...'), None))
		self.ml.setList(map(self._defaultlistcenter, self.streamList))
		getPage(self.url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.streamList = []
		videos = re.findall('<a href="#" data-video="(.*?)" data-video-site="(.*?)" class=".*?"> <div class="thumb"><img src="(.*?)" class="img-thumbnail"></div><span class="title">(.*?)\n</span></a>', data)
		if videos:
			# ('xuF0AGaUhb8', 'yt', 'images/xuF0AGaUhb8.jpg', 'Der Kuckuck und der Esel - Kinderlieder zum Mitsingen | Sing Kinderlieder')
			for (id, type, image, title) in videos:
				image = BASE_URL+'/'+image
				self.streamList.append((title, id, image, type))
		if len(self.streamList) == 0:
			self.streamList.append((_('Parsing error!'), None, '', ''))
			self.keyLocked = True
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1)
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		video_name = self['liste'].getCurrent()[0][0]
		video_id = self['liste'].getCurrent()[0][1]
		video_cover = self['liste'].getCurrent()[0][2]
		video_type = self['liste'].getCurrent()[0][3]
		if video_type == 'yt' and video_id:
			self.session.open(YoutubePlayer, [(video_name, video_id, video_cover)], playAll = False, showPlaylist=False, showCover=False)

		else:
			self.session.open(MessageBoxExt, _("Stream not found, try another Stream Hoster."), MessageBoxExt.TYPE_INFO, timeout=5)