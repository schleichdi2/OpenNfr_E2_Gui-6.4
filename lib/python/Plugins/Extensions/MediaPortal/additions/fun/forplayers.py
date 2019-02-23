# -*- coding: utf-8 -*-
##############################################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2019
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
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.api import ForPlayersApi, SYSTEMS

api = ForPlayersApi()

default_cover = "file://%s/4players.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class forPlayersGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("4Players")
		self['ContentTitle'] = Label(_("Selection:"))
		self.selectionListe = []
		self.suchString = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.selectionListe.append(("Aktuelle Videos", "1"))
		self.selectionListe.append(("Meistgesehene Videos", "2"))
		self.selectionListe.append(("Letzte Reviews", "3"))
		self.selectionListe.append(("Videos nach Spiel suchen", "4"))
		self.ml.setList(map(self._defaultlistcenter, self.selectionListe))

	def keyOK(self):
		self.selectionLink = self['liste'].getCurrent()[0][1]
		print 'SelektionLink: ', self.selectionLink
		if self.selectionLink == "4":
			limit = int(150)
			api.set_systems(SYSTEMS)
			self.suchen()
		else:
			self.session.open(forPlayersVideoScreen, self.selectionLink, '')

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback
			self.session.open(forPlayersVideoScreen, self.selectionLink, self.suchString)

class forPlayersVideoScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, selectionLink, searchData):
		self.selectionLink = selectionLink
		self.searchData = searchData
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.page = 1
		self.lastpage = 999
		self.keyLocked = True
		self['title'] = Label("4Players")

 		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")
		self.juengstTS = ''
		self.videosListe = []
		self.videosQueue = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadVideos)

	def loadVideos(self):
		self['page'].setText(str(self.page))
		if self.selectionLink == '1':
			try:
				limit = int(50)
				api.set_systems(SYSTEMS)
				videos = api.get_latest_videos(limit)
				self.videosQueue.append((self.page, videos))
				self.juengstTS = min((v['ts'] for v in videos))
				self.showData(videos)
			except:
				self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
				self.ml.setList(map(self._defaultlistleft, self.videosListe))
		elif self.selectionLink == '2':
			try:
				limit = int(150)
				api.set_systems(SYSTEMS)
				videos = api.get_popular_videos(limit)
				self.showData(videos)
			except:
				self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
				self.ml.setList(map(self._defaultlistleft, self.videosListe))
		elif self.selectionLink == '3':
			try:
				limit = int(150)
				api.set_systems(SYSTEMS)
				videos = api.get_latest_reviews(older_than=0)
				self.showData(videos)
			except:
				self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
				self.ml.setList(map(self._defaultlistleft, self.videosListe))
		elif self.selectionLink == "4":
			videos = []
			try:
				searchStr = str(self.searchData)
				try:
					videos = api.get_games(searchStr)
					if videos == None:
						self.videosListe.append(('Keine Videos gefunden....', "", "", ""))
						self.ml.setList(map(self._defaultlistleft, self.videosListe))
					else:
						self.showSearchData(videos)
				except:
					self.videosListe.append(('Keine Videos gefunden....', "", "", ""))
			except:
				self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
				self.ml.setList(map(self._defaultlistleft, self.videosListe))

	def showSearchData(self, videos):
		for video in videos:
			gameTitel = video['title'].encode('utf-8')
			gameID = video['id']
			videoPic = video['thumb']
			gameStudio = video['studio']
			self.videosListe.append((gameTitel, "empty", str(videoPic), gameTitel, gameID, gameStudio, gameTitel))
		self.ml.setList(map(self._defaultlistleft, self.videosListe))
		self.keyLocked = False

	def showData(self, videos):
		for video in videos:
			gameTitle = video['game']['title'].encode('utf-8')
			videoTitle = video['video_title'].encode('utf-8')
			videoStreamUrl = video['streams']['hq']['url'].encode('utf-8')
			videoDate = video['date']
			videoPic = video['thumb']
			gameId = video['game']['id']
			gameStudio = video['game']['studio']
			videoTitleConv = gameTitle + ' - ' + videoTitle + ' ' + '(' + videoDate + ')'
			self.videosListe.append((videoTitleConv, videoStreamUrl, str(videoPic), videoTitle, gameId, gameStudio, gameTitle))
		self.ml.setList(map(self._defaultlistleft, self.videosListe))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.videosListe, 0, 1, 2, None, None, self.page, 999, mode=1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(str(Title))
		if self.selectionLink == '1':
			self['page'].setText(str(self.page))
		CoverHelper(self['coverArt']).getCover(Image)
		self.keyInfo()

	def loadPage(self):
		if self.selectionLink == '1':
			self.videosListe = []
			self.queuedVideoList = []
			for queuedEntry in self.videosQueue:
				if queuedEntry[0] == self.page:
					self.queuedVideoList = queuedEntry[1]
			if self.queuedVideoList:
				self.showData(self.queuedVideoList)
			else:
				try:
						api.set_systems(SYSTEMS)
						videos = api.get_latest_videos(older_than=self.juengstTS)
						self.juengstTS = min((v['ts'] for v in videos))
						self.videosQueue.append((self.page, videos))
						self.showData(videos)
				except:
						self.videosListe.append(('4Players nicht verfügbar....', "", "", ""))
						self.ml.setList(map(self._defaultlistleft, self.videosListe))

	def keyInfo(self):
		text = []
		gameStudio = self['liste'].getCurrent()[0][5]
		gameId = self['liste'].getCurrent()[0][4]
		gameTitle = self['liste'].getCurrent()[0][6]
		gameInfoCol = api._get_game_info(gameId)
		text.append('Titel: ' + str(gameTitle))
		text.append('\n')
		text.append('Studion: ' + str(gameStudio))
		text.append('\n')
		for info in gameInfoCol:
			gamePub = info['publisher']
			text.append('Publisher: ' + str(gamePub))
			text.append('\n')
			for system in info['systeme']:
				gameSys = system['system']
				text.append('Plattform: ' + str(gameSys))
				text.append('\n')
				text.append('Release: ' + str(system['releasetag']) + '.' + str(system['releasemonat']) + '.' + str(system['releasejahr']))
				text.append('\n')
				text.append('USK: ' + str(system['usk']))
				text.append('\n')
		sText = ''.join(text)
		self['handlung'].setText(sText)
		#self.session.open(MessageBoxExt,sText, MessageBoxExt.TYPE_INFO)

	def keyOK(self):
		playersUrl = self['liste'].getCurrent()[0][1]
		if playersUrl == "empty":
			game_id = self['liste'].getCurrent()[0][4]
			game_id_int = int(game_id)
			try:
				searchVideos = api.get_videos_by_game(older_than=0, game_id=game_id)
				self.session.open(forPlayersSearchListScreen, searchVideos)
			except:
				pass
		else:
			streamUrl = str(playersUrl)
			playersTitle = self['liste'].getCurrent()[0][3]
			playersTitleStr = str(playersTitle)
			if playersUrl:
				self.session.open(SimplePlayer, [(playersTitleStr, streamUrl)], showPlaylist=False, ltype='4players')

class forPlayersSearchListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, videosListe):
		self.searchVideoListe = videosListe
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight
		}, -1)

		self.page = 1
		self.lastpage = 999
		self.keyLocked = True
		self['title'] = Label("4Players")

 		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")
		self.juengstTS = ''
		self.videosListe = []
		self.videosQueue = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadSearchVideos)

	def loadSearchVideos(self):
		videos = self.searchVideoListe
		for video in videos:
			gameTitle = video['game']['title'].encode('utf-8')
			videoTitle = video['video_title'].encode('utf-8')
			videoStreamUrl = video['streams']['hq']['url'].encode('utf-8')
			videoDate = video['date']
			videoPic = video['thumb']
			gameId = video['game']['id']
			gameStudio = video['game']['studio']
			videoTitleConv = gameTitle + ' - ' + videoTitle + ' ' + '(' + videoDate + ')'
			self.videosListe.append((videoTitleConv, videoStreamUrl, str(videoPic), videoTitle, gameId, gameStudio, gameTitle))
		self.ml.setList(map(self._defaultlistleft, self.videosListe))
		self.keyLocked = False
		self.th_ThumbsQuery(self.videosListe, 0, 1, 2, None, None, self.page, 999, mode=1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(str(Title))
		self['page'].setText(str(self.page))
		CoverHelper(self['coverArt']).getCover(Image)
		self.keyInfo()

	def keyInfo(self):
		text = []
		gameStudio = self['liste'].getCurrent()[0][5]
		gameId = self['liste'].getCurrent()[0][4]
		gameTitle = self['liste'].getCurrent()[0][6]
		gameInfoCol = api._get_game_info(gameId)
		text.append('Titel: ' + str(gameTitle))
		text.append('\n')
		text.append('Studion: ' + str(gameStudio))
		text.append('\n')
		for info in gameInfoCol:
			gamePub = info['publisher']
			text.append('Publisher: ' + str(gamePub))
			text.append('\n')
			for system in info['systeme']:
				gameSys = system['system']
				text.append('Plattform: ' + str(gameSys))
				text.append('\n')
				text.append('Release: ' + str(system['releasetag']) + '.' + str(system['releasemonat']) + '.' + str(system['releasejahr']))
				text.append('\n')
				text.append('USK: ' + str(system['usk']))
				text.append('\n')
		sText = ''.join(text)
		self['handlung'].setText(sText)
		#self.session.open(MessageBoxExt,sText, MessageBoxExt.TYPE_INFO)

	def keyOK(self):
		playersUrl = self['liste'].getCurrent()[0][1]
		streamUrl = str(playersUrl)
		playersTitle = self['liste'].getCurrent()[0][3]
		playersTitleStr = str(playersTitle)
		if playersUrl:
			self.session.open(SimplePlayer, [(playersTitleStr, streamUrl)], showPlaylist=False, ltype='4players')