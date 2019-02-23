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
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

default_cover = "file://%s/twitch.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': '6r2dhbo9ek6mm1gab2snj0navo4sgqy'}
limit = 25

class twitchMainScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("Twitch")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Favorites", "favorites"))
		self.genreliste.append(("Top Games", "topgames"))
		self.genreliste.append(("Featured Streams", "featuredstreams"))
		self.genreliste.append(("Streams", "streams"))
		self.genreliste.append(("Videos", "videos"))
		self.genreliste.append(("--- Search for Games ---", "searchgames"))
		self.genreliste.append(("--- Search for Streams ---", "searchstreams"))
		self.genreliste.append(("--- Search for Channels ---", "searchchannels"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name.startswith("--- Search"):
			self.suchen()
		else:
			ID = self['liste'].getCurrent()[0][1]
			self.session.open(twitchGames, '', Name, ID)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = self['liste'].getCurrent()[0][0]
			ID = self['liste'].getCurrent()[0][1]
			self.suchString = urllib.quote(callback).replace(' ', '%20')
			self.session.open(twitchGames, self.suchString, Name, ID)

class twitchGames(MPScreen):

	def __init__(self, session, SearchString, Name, ID, Game='', Lang=_('any'), ChannelID=''):
		self.SearchString = SearchString
		self.ID = ID
		self.Name = Name
		self.Game = Game
		self.ChannelID = ChannelID
		if Lang == _('any'):
			self.Lang = ''
		else:
			self.Lang = Lang
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"red" : self.keyFav,
			"green" : self.keyPageNumber,
			"yellow" : self.keyYellow,
			"blue" : self.keyBlue
		}, -1)

		self['title'] = Label("Twitch")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		if (self.ID == "searchchannels" or self.ID == "searchstreams" or self.ID == "streams" or self.ID == "featuredstreams"):
			self['F1'] = Label(_("Add to Favorites"))
		elif self.ID == "favorites":
			self['F1'] = Label(_("Delete"))
		self['F2'] = Label(_("Page"))
		if (self.ID == "searchgames" or self.ID == "topgames" or self.ID == "searchchannels" or self.ID == "favorites"):
			self['F3'] = Label(_("Videos"))
		if (self.ID == "streams" or self.ID == "videos" or self.ID == "channelvideos"):
			if self.Lang == '':
				lang = _('any')
			else:
				lang = self.Lang
			self['F4'] = Label(_("Language")+": %s" % lang)

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1

		self.gameList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.gameList = []
		self.keyLocked = True
		if self.ID == "searchgames":
			url = "https://api.twitch.tv/kraken/search/games?query=%s&limit=%s&offset=%s&live=true" % (self.SearchString, str(limit), str((self.page-1) * limit))
		elif self.ID == "searchstreams":
			url = "https://api.twitch.tv/kraken/search/streams?query=%s&limit=%s&offset=%s&hls=true" % (self.SearchString, str(limit), str((self.page-1) * limit))
		elif self.ID == "searchchannels":
			url = "https://api.twitch.tv/kraken/search/channels?query=%s&limit=%s&offset=%s" % (self.SearchString, str(limit), str((self.page-1) * limit))
		elif self.ID == "streams":
			url = "https://api.twitch.tv/kraken/streams?limit=%s&offset=%s&language=%s&game=%s&stream_type=live" % (str(limit), str((self.page-1) * limit), self.Lang, self.Game)
		elif self.ID == "featuredstreams":
			url = "https://api.twitch.tv/kraken/streams/featured?limit=100"
		elif self.ID == "topgames":
			url = "https://api.twitch.tv/kraken/games/top?limit=%s&offset=%s" % (str(limit), str((self.page-1) * limit))
		elif self.ID == "videos":
			url = "https://api.twitch.tv/kraken/videos/top?limit=%s&offset=%s&language=%s&game=%s" % (str(limit), str((self.page-1) * limit), self.Lang, self.Game)
		elif self.ID == "channelvideos":
			url = "https://api.twitch.tv/kraken/channels/%s/videos?limit=%s&offset=%s&language=%s" % (self.ChannelID, str(limit), str((self.page-1) * limit), self.Lang)
		if self.ID != "favorites":
			twAgentGetPage(url, agent=agent, headers=headers).addCallback(self.parseData).addErrback(self.dataError)
		else:
			self.parseData('')

	def parseData(self, data):
		if self.ID != "favorites":
			jsondata = json.loads(data)
			if (self.ID == "searchgames" or self.ID == "featuredstreams"):
				self.lastpage = 1
				self['page'].setText('1 / 1')
			elif self.ID == "videos":
				self.lastpage = 21
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
			else:
				try:
					lastp = round((float(jsondata["_total"]) / limit) + 0.5)
					self.lastpage = int(lastp)
					self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
				except:
					self.lastpage = 999
					self['page'].setText(str(self.page))
		else:
			self.lastpage = 1
			self['page'].setText('1 / 1')
		if self.ID == "favorites":
			if not fileExists(config_mp.mediaportal.watchlistpath.value+"mp_twitch_favorites"):
				open(config_mp.mediaportal.watchlistpath.value+"mp_twitch_favorites","w").close()
			if fileExists(config_mp.mediaportal.watchlistpath.value+"mp_twitch_favorites"):
				path = config_mp.mediaportal.watchlistpath.value+"mp_twitch_favorites"
			if fileExists(path):
				read = open(path,"r")
				for rawData in read.readlines():
					data = re.findall('"(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
					if data:
						(Title, Name, Id) = data[0]
						self.gameList.append((Title, '', default_cover, Name, '', Title, Id))
				self.gameList.sort()
				read.close()
			if len(self.gameList) == 0:
				self.gameList.append((_('No entries found!'), None, default_cover))
				self.ml.setList(map(self._defaultlistleft, self.gameList))
			else:
				self.ml.setList(map(self._defaultlistleft, self.gameList))
				self.keyLocked = False
		elif self.ID == "searchgames":
			try:
				for node in jsondata["games"]:
					title = str(node["name"])
					image = str(node["box"]["template"]).replace('{width}x{height}','600x800')
					self.gameList.append((title, '', image))
			except:
				pass
			if len(self.gameList) == 0:
				self.gameList.append((_('No games found!'), None, None))
				self.ml.setList(map(self._defaultlistleft, self.gameList))
			else:
				self.ml.setList(map(self._defaultlistleft, self.gameList))
				self.keyLocked = False
		elif (self.ID == "streams" or self.ID == "searchstreams"):
			for node in jsondata["streams"]:
				game = str(node["game"])
				id = str(node["channel"]["_id"])
				language = str(node["channel"]["language"])
				title = str(node["channel"]["display_name"])
				name = str(node["channel"]["name"])
				image = str(node["preview"]["template"]).replace('{width}x{height}','800x450')
				self.gameList.append((game + " - " + title, language, image, name, game, title, id))
			if len(self.gameList) == 0:
				self.gameList.append((_('No streams found!'), None, None))
				self.ml.setList(map(self._defaultlistleft, self.gameList))
			else:
				self.ml.setList(map(self.twitchListEntry, self.gameList))
				self.keyLocked = False
		elif self.ID == "featuredstreams":
			for node in jsondata["featured"]:
				game = str(node["stream"]["game"])
				id = str(node["stream"]["channel"]["_id"])
				language = str(node["stream"]["channel"]["language"])
				title = str(node["stream"]["channel"]["display_name"])
				name = str(node["stream"]["channel"]["name"])
				image = str(node["stream"]["preview"]["template"]).replace('{width}x{height}','800x450')
				self.gameList.append((game + " - " + title, language, image, name, game, title, id))
			if len(self.gameList) == 0:
				self.gameList.append((_('No streams found!'), None, None))
				self.ml.setList(map(self._defaultlistleft, self.gameList))
			else:
				self.ml.setList(map(self.twitchListEntry, self.gameList))
				self.keyLocked = False
		elif self.ID == "topgames":
			for node in jsondata["top"]:
				title = str(node["game"]["name"])
				image = str(node["game"]["box"]["template"]).replace('{width}x{height}','600x800')
				self.gameList.append((title, '', image))
			if len(self.gameList) == 0:
				self.gameList.append((_('No games found!'), None, None))
				self.ml.setList(map(self._defaultlistleft, self.gameList))
			else:
				self.ml.setList(map(self._defaultlistleft, self.gameList))
				self.keyLocked = False
		elif self.ID == "videos":
			for node in jsondata["vods"]:
				language = str(node["language"])
				title = str(node["channel"]["display_name"])
				vidtitle = str(node["title"])
				game = str(node["game"])
				try:
					image = str(node["thumbnails"]["template"][0]["url"]).replace('{width}x{height}','800x450')
				except:
					image = None
				id = str(node["_id"])
				self.gameList.append((game + " - " + title + " - " + vidtitle, language, image, id, game, title + " - " + vidtitle))
			if len(self.gameList) == 0:
				self.gameList.append((_('No videos found!'), None, None))
				self.ml.setList(map(self._defaultlistleft, self.gameList))
			else:
				self.ml.setList(map(self.twitchListEntry, self.gameList))
				self.keyLocked = False
		elif self.ID == "channelvideos":
			for node in jsondata["videos"]:
				language = str(node["language"])
				title = str(node["channel"]["display_name"])
				vidtitle = str(node["title"])
				game = str(node["game"])
				try:
					image = str(node["thumbnails"]["template"][0]["url"]).replace('{width}x{height}','800x450')
				except:
					image = None
				id = str(node["_id"])
				self.gameList.append((game + " - " + title + " - " + vidtitle, language, image, id, game, title + " - " + vidtitle))
			if len(self.gameList) == 0:
				self.gameList.append((_('No videos found!'), None, None))
				self.ml.setList(map(self._defaultlistleft, self.gameList))
			else:
				self.ml.setList(map(self.twitchListEntry, self.gameList))
				self.keyLocked = False
		elif self.ID == "searchchannels":
			for node in jsondata["channels"]:
				id = str(node["_id"])
				game = str(node["game"])
				language = str(node["language"])
				title = str(node["display_name"])
				name = str(node["name"])
				image = str(node["logo"])
				self.gameList.append((title, language, image, name, game, title, id))
			if len(self.gameList) == 0:
				self.gameList.append((_('No channels found!'), None, None))
				self.ml.setList(map(self._defaultlistleft, self.gameList))
			else:
				self.ml.setList(map(self.twitchListEntry, self.gameList))
				self.keyLocked = False
		self.ml.moveToIndex(0)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked or self['liste'].getCurrent() == None:
			return
		if (self.ID == "streams" or self.ID == "searchstreams" or self.ID == "featuredstreams" or self.ID == "searchchannels" or self.ID == "favorites"):
			self.channelName = self['liste'].getCurrent()[0][3]
			self.gameName = self['liste'].getCurrent()[0][4]
			self.displayName = self['liste'].getCurrent()[0][5]
			url = "https://api.twitch.tv/api/channels/" + self.channelName + "/access_token"
			twAgentGetPage(url, agent=agent, headers=headers).addCallback(self.parseAccessToken).addErrback(self.dataError)
		if (self.ID == "videos" or self.ID == "channelvideos"):
			self.vodid = self['liste'].getCurrent()[0][3]
			self.gameName = self['liste'].getCurrent()[0][4]
			self.displayName = self['liste'].getCurrent()[0][5]
			url = "https://api.twitch.tv/api/vods/" + self.vodid + "/access_token"
			twAgentGetPage(url, agent=agent, headers=headers).addCallback(self.parseAccessToken).addErrback(self.dataError)
		elif (self.ID == "topgames" or self.ID == "searchgames"):
			Game = self['liste'].getCurrent()[0][0].replace(' ', '%20')
			self.session.open(twitchGames, '', "Streams", "streams", Game, '')

	def keyBlue(self):
		if (self.ID == "streams" or self.ID == "videos" or self.ID == "channelvideos"):
			rangelist = [[_('any'),], ['de',], ['en',], ['en-gb',], ['fr',], ['es',], ['it',], ['pt',], ['pt-br',], ['nl',], ['da',], ['no',], ['sv',], ['fi',], ['pl',], ['cs',], ['sk',], ['hu',], ['el',], ['ru',], ['bg',], ['ro',], ['tr',], ['ar',], ['th',], ['vi',], ['zh-tw',], ['ko',], ['ja',]]
			self.session.openWithCallback(self.keyLangAction, ChoiceBoxExt, title=_('Select language'), list = rangelist)

	def keyYellow(self):
		if (self.ID == "searchgames" or self.ID == "topgames"):
			if self.keyLocked:
				return
			Game = self['liste'].getCurrent()[0][0].replace(' ', '%20')
			self.session.open(twitchGames, '', "Videos", "videos", Game, '')
		elif (self.ID == "searchchannels" or self.ID == "favorites"):
			if self.keyLocked:
				return
			Game = self['liste'].getCurrent()[0][4].replace(' ', '%20')
			id = self['liste'].getCurrent()[0][6]
			self.session.open(twitchGames, '', "Videos", "channelvideos", Game, '', id)

	def keyLangAction(self, result):
		if result:
			if result[0] == _('any'):
				self.Lang = ''
				lang = _('any')
			else:
				self.Lang = result[0]
				lang = result[0]
			self['F4'].setText(_("Language")+": %s" % lang)
			self.loadPage()

	def keyFav(self):
		if (self.ID == "searchchannels" or self.ID == "searchstreams" or self.ID == "streams" or self.ID == "featuredstreams"):
			if self.keyLocked:
				return
			Title = self['liste'].getCurrent()[0][5]
			Name = self['liste'].getCurrent()[0][3]
			Id = self['liste'].getCurrent()[0][6]
			fn = config_mp.mediaportal.watchlistpath.value+"mp_twitch_favorites"
			if not fileExists(fn):
				open(fn,"w").close()
			try:
				writePlaylist = open(fn, "a")
				writePlaylist.write('"%s" "%s" "%s"\n' % (Title, Name, Id))
				writePlaylist.close()
				message = self.session.open(MessageBoxExt, _("Selection was added to the favorites."), MessageBoxExt.TYPE_INFO, timeout=3)
			except:
				pass
		elif self.ID == "favorites":
			exist = self['liste'].getCurrent()
			if self.keyLocked or exist == None:
				return
			i = self['liste'].getSelectedIndex()
			j = 0
			l = len(self.gameList)
			fn = config_mp.mediaportal.watchlistpath.value+"mp_twitch_favorites"
			try:
				f1 = open(fn, 'w')
				while j < l:
					if j != i:
						(Title, x1, x2, Name, x3, x4, Id) = self.gameList[j]
						f1.write('"%s" "%s" "%s"\n' % (Title, Name, Id))
					j += 1
				f1.close()
				self.loadPage()
			except:
				pass

	def parseAccessToken(self, data):
		token = json.loads(data)
		if (self.ID == "videos" or self.ID == "channelvideos"):
			url = "http://usher.ttvnw.net/vod/{channel}.m3u8?player=twitchweb&token={token}&sig={sig}&allow_source=true"
		else:
			url = "http://usher.twitch.tv/api/channel/hls/{channel}.m3u8?player=twitchweb&token={token}&sig={sig}&allow_source=true"
		url = url.replace("{sig}", str(token["sig"]))
		url = url.replace("{token}", urllib.quote(str(token["token"])))
		if (self.ID == "videos" or self.ID == "channelvideos"):
			url = url.replace("{channel}", str(self.vodid[1:]))
		else:
			url = url.replace("{channel}", str(self.channelName))
		twAgentGetPage(url, agent=agent).addCallback(self.parseM3U).addErrback(self.dataError)

	def parseM3U(self, data):
		if "error_code" in data:
			self.session.open(MessageBoxExt, _("There is currently no live stream available on this channel."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.session.open(twitchStreamQuality, data, self.displayName, self.gameName)

class twitchStreamQuality(MPScreen):

	def __init__(self, session, m3u8, channel, game):
		self.m3u8 = str(m3u8)
		self.channel = channel
		self.game = game
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Twitch")
		self['ContentTitle'] = Label("Quality:")

		self.qualityList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.parseData)

	def parseData(self):
		result = re.findall('NAME="(.*?)".*?(http://.*?)\n', self.m3u8, re.S)
		for (quality, url) in result:
			if quality != "Mobile":
				self.qualityList.append((quality, url))
		self.ml.setList(map(self._defaultlistleft, self.qualityList))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked or self['liste'].getCurrent() == None:
			return
		url = self['liste'].getCurrent()[0][1]
		title = self.game + " - " + self.channel
		title = title.strip(" - ")
		self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='twitch')