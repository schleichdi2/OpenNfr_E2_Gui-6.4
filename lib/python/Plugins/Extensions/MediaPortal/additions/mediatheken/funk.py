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
default_cover = "file://%s/funk.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

headers = {
	'Authorization':'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoid2ViYXBwLXYzMSIsInNjb3BlIjoic3RhdGljLWNvbnRlbnQtYXBpLGN1cmF0aW9uLWFwaSxuZXh4LWNvbnRlbnQtYXBpLXYzMSx3ZWJhcHAtYXBpIn0.mbuG9wS9Yf5q6PqgR4fiaRFIagiHk9JhwoKES7ksVX4',
	'Accept-Encoding':'deflate',
}

BASE_URL = 'https://www.funk.net/api/v4.0'

class funkGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("FUNK")
		self['ContentTitle'] = Label("Auswahl: Kanäle")
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self.keyLocked = True
		url = BASE_URL + "/channels/?size=100&page=%s" % str(self.page-1)
		getPage(url, headers=headers).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		json_data = json.loads(data)
		if json_data.has_key('page'):
			if int(json_data["page"]["totalPages"])>1:
				self.lastpage = int(json_data["page"]["totalPages"])
				self['Page'].setText(_("Page:"))
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		for item in json_data["_embedded"]["channelDTOList"]:
			if item.has_key('imageUrlOrigin') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlOrigin"]:
				image = str(item["imageUrlOrigin"])
			elif item.has_key('imageUrlLandscape') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlLandscape"]:
				image = str(item["imageUrlLandscape"])
			elif item.has_key('imageUrlPortrait') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlPortrait"]:
				image = str(item["imageUrlPortrait"])
			elif item.has_key('imageUrlSquare') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlSquare"]:
				image = str(item["imageUrlSquare"])
			else:
				image = None
			title = decodeHtml(str(item["title"]))
			if item.has_key('description'):
				descr = decodeHtml(str(item["description"]))
			else:
				descr = ""
			url = BASE_URL + "/playlists/byChannelAlias/" + str(item["alias"]) + "?sort=language,ASC"
			if title not in ("Doctor Who", "Uncle", "Threesome", "Orange is the new Black", "The Job Lot"):
				self.filmliste.append((title, image, url, descr))
		self.filmliste.sort(key=lambda t : t[0].lower())
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][1]
		descr = self['liste'].getCurrent()[0][3]
		self['name'].setText(Title)
		self['handlung'].setText(descr)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][2]
		self.session.open(funkSeasonsScreen, url, Name)

class funkSeasonsScreen(MPScreen):

	def __init__(self, session, url, name):
		self.url = url
		self.Name = name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("FUNK")
		self['ContentTitle'] = Label("Auswahl: %s" % self.Name)
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self.keyLocked = True
		url = self.url + "&page=%s" % str(self.page-1)
		getPage(url, headers=headers).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		json_data = json.loads(data)
		if json_data.has_key('page'):
			if int(json_data["page"]["totalPages"])>1:
				self.lastpage = int(json_data["page"]["totalPages"])
				self['Page'].setText(_("Page:"))
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		if not json_data.has_key('_embedded'):
			if json_data["parent"].has_key('imageUrlOrigin') and not "8415ad90686d2c75aca239372903a45e" in json_data["parent"]["imageUrlOrigin"]:
				image = str(json_data["parent"]["imageUrlOrigin"])
			elif json_data["parent"].has_key('imageUrlLandscape') and not "8415ad90686d2c75aca239372903a45e" in json_data["parent"]["imageUrlLandscape"]:
				image = str(json_data["parent"]["imageUrlLandscape"])
			elif json_data["parent"].has_key('imageUrlPortrait') and not "8415ad90686d2c75aca239372903a45e" in json_data["parent"]["imageUrlPortrait"]:
				image = str(json_data["parent"]["imageUrlPortrait"])
			elif json_data["parent"].has_key('imageUrlSquare') and not "8415ad90686d2c75aca239372903a45e" in json_data["parent"]["imageUrlSquare"]:
				image = str(json_data["parent"]["imageUrlSquare"])
			else:
				image = None
			title = decodeHtml(str(json_data["parent"]["title"]))
			if json_data["parent"].has_key('description'):
				descr = decodeHtml(str(json_data["parent"]["description"]))
			else:
				descr = ""
			url = BASE_URL + "/videos/byChannelAlias/" + str(json_data["parent"]["alias"]) + "?filterFsk=false&sort=creationDate,desc&size=100"
			self.filmliste.append((title, image, url, descr))
		else:
			for item in json_data["_embedded"]["playlistDTOList"]:
				if item.has_key('imageUrlOrigin') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlOrigin"]:
					image = str(item["imageUrlOrigin"])
				elif item.has_key('imageUrlLandscape') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlLandscape"]:
					image = str(item["imageUrlLandscape"])
				elif item.has_key('imageUrlPortrait') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlPortrait"]:
					image = str(item["imageUrlPortrait"])
				elif item.has_key('imageUrlSquare') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlSquare"]:
					image = str(item["imageUrlSquare"])
				else:
					image = None
				title = decodeHtml(str(item["title"]))
				if item.has_key('description'):
					descr = decodeHtml(str(item["description"]))
				else:
					descr = ""
				url = BASE_URL + "/videos/byPlaylistAlias/" + str(item["alias"]) + "?filterFsk=false&size=100&sort=episodeNr,ASC"
				self.filmliste.append((title, image, url, descr))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][1]
		descr = self['liste'].getCurrent()[0][3]
		self['name'].setText(Title)
		self['handlung'].setText(descr)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][2]
		self.session.open(funkEpisodesScreen, url, Name)

class funkEpisodesScreen(MPScreen):

	def __init__(self, session, url, name):
		self.url = url
		self.Name = name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("FUNK")
		self['ContentTitle'] = Label("Auswahl: %s" % self.Name)
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self.keyLocked = True
		url = self.url + "&page=%s" % str(self.page-1)
		getPage(url, headers=headers).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		json_data = json.loads(data)
		if json_data.has_key('page'):
			if int(json_data["page"]["totalPages"])>1:
				self.lastpage = int(json_data["page"]["totalPages"])
				self['Page'].setText(_("Page:"))
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		try:
			for item in json_data["_embedded"]["videoDTOList"]:
				if item.has_key('imageUrlOrigin') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlOrigin"]:
					image = str(item["imageUrlOrigin"])
				elif item.has_key('imageUrlLandscape') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlLandscape"]:
					image = str(item["imageUrlLandscape"])
				elif item.has_key('imageUrlPortrait') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlPortrait"]:
					image = str(item["imageUrlPortrait"])
				elif item.has_key('imageUrlSquare') and not "8415ad90686d2c75aca239372903a45e" in item["imageUrlSquare"]:
					image = str(item["imageUrlSquare"])
				else:
					image = None
				title = decodeHtml(str(item["title"]))
				if item.has_key('description'):
					descr = decodeHtml(str(item["description"]))
				else:
					descr = ""
				if item.has_key('duration'):
					duration = int(item["duration"])
					m, s = divmod(duration, 60)
					duration = "Laufzeit: %02d:%02d\n" % (m, s)
				else:
					duration = ""
				if item.has_key('episodeNr'):
					episode = int(item["episodeNr"])
				else:
					episode = ""
				if item.has_key('seasonNr'):
					season = int(item["seasonNr"])
				else:
					season = ""
				if season and episode:
					if (season and episode) > 0:
						epi = "Staffel: " + str(season) + " Episode: " + str(episode) + "\n"
					else:
						epi = ""
				else:
					epi = ""
				if item.has_key('entityId'):
					id = str(item["entityId"])
				else:
					id = None
				if item.has_key('downloadUrl'):
					downld = str(item["downloadUrl"])
				else:
					downld = None

				self.filmliste.append((title, image, id, descr, epi, duration, downld))
		except Exception as e:
			printl(e,self,"E")
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No episodes found!'), None, None, "", "", "", None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][1]
		descr = self['liste'].getCurrent()[0][3]
		epi = self['liste'].getCurrent()[0][4]
		dur = self['liste'].getCurrent()[0][5]
		self['name'].setText(Title)
		self['handlung'].setText(dur+epi+descr)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		id = self['liste'].getCurrent()[0][2]
		Title = self['liste'].getCurrent()[0][0]
		downld = self['liste'].getCurrent()[0][6]
		videourl = None
		if id:
			from Plugins.Extensions.MediaPortal.resources import nexx
			videourl = nexx.getVideoUrl(id, downld)
		if videourl:
			if "m3u8" in videourl:
				self.session.open(SimplePlayer, [(Title, videourl)], showPlaylist=False, ltype='funk', forceGST=False)
			else:
				self.session.open(SimplePlayer, [(Title, videourl)], showPlaylist=False, ltype='funk')