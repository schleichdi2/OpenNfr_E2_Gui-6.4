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

BASEURL = "https://cam4.com/"

config_mp.mediaportal.cam4_filter = ConfigText(default="all", fixed_size=False)
default_cover = "file://%s/cam4.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
cam4Agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 8_0_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12A366 Safari/600.1.4"

class cam4GenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"yellow": self.keyFilter
		}, -1)

		self.filter = config_mp.mediaportal.cam4_filter.value

		self['title'] = Label("Cam4.com")
		self['ContentTitle'] = Label("Genre:")
		self['F3'] = Label(self.filter)

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.genreliste.append(("Trending", ""))
		self.genreliste.append(("Couple", ""))
		self.genreliste.append(("USA", "&country=us"))
		self.genreliste.append(("Germany", "&country=de"))
		self.genreliste.append(("Brazil", "&country=br"))
		self.genreliste.append(("Italy", "&country=it"))
		self.genreliste.append(("Spain", "&country=es"))
		self.genreliste.append(("France", "&country=fr"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(cam4FilmScreen, Link, Name)

	def keyFilter(self):
		if self.filter == "all":
			self.filter = "female"
			config_mp.mediaportal.cam4_filter.value = "female"
		elif self.filter == "female":
			self.filter = "male"
			config_mp.mediaportal.cam4_filter.value = "male"
		elif self.filter == "male":
			self.filter = "shemale"
			config_mp.mediaportal.cam4_filter.value = "shemale"
		elif self.filter == "shemale":
			self.filter = "all"
			config_mp.mediaportal.cam4_filter.value = "all"

		config_mp.mediaportal.cam4_filter.save()
		configfile_mp.save()
		self['F3'].setText(self.filter)

class cam4FilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		if config_mp.mediaportal.cam4_filter.value == "all":
			self.filter = ""
		else:
			self.filter = config_mp.mediaportal.cam4_filter.value
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions2", "MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"upUp" : self.key_repeatedUp,
			"rightUp" : self.key_repeatedUp,
			"leftUp" : self.key_repeatedUp,
			"downUp" : self.key_repeatedUp,
			"upRepeated" : self.keyUpRepeated,
			"downRepeated" : self.keyDownRepeated,
			"rightRepeated" : self.keyRightRepeated,
			"leftRepeated" : self.keyLeftRepeated,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("Cam4.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 999

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if self.Name == "Couple":
			url = BASEURL + "directoryCams?directoryJson=true&online=true&url=true&broadcastType=male_female_group&page=%s" % self.page
		else:
			url = BASEURL + "directoryCams?directoryJson=true&online=true&url=true&gender=%s%s&page=%s" % (self.filter, self.Link, self.page)
		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()

	def loadPageData(self, data):
		self.ml.moveToIndex(0)
		self['page'].setText(str(self.page))
		jsondata = json.loads(data)
		for node in jsondata["users"]:
			Title = str(node["username"])
			Url = BASEURL + str(node["username"])
			Image = "https://snapshots.xcdnpro.com/thumbnails/%s?s=%s" % (str(node["username"]), str(node["thumbnailId"]))
			Gender = str(node["gender"])
			Location = str(node["countryCode"])
			from Plugins.Extensions.MediaPortal.resources import iso3166
			Location = str(iso3166.countries.get(Location))
			Location = re.search('.*?name=u\'(.*?)\'', Location, re.S).group(1)
			Viewers = str(node["viewers"])
			Couple = str(node["broadcastType"]).replace('_',' ')
			Preference = str(node["sexPreference"])
			Status = str(node["statusMessage"])
			if not node["mobile"] and not node["vrStream"] and not str(node["source"])=="mobile":
				self.filmliste.append((Title, Url, Image, Gender, Location, Viewers, Couple, Preference, Status))
		if len(self.filmliste):
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.loadPicQueued()
		else:
			self.filmliste.append((_('No livestreams found!'), None, None, None, None, None, None, None))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()
		self.keyLocked = False

	def showInfos(self):
		Url = self['liste'].getCurrent()[0][1]
		if Url == None:
			return
		title = self['liste'].getCurrent()[0][0]
		gender = self['liste'].getCurrent()[0][3]
		location = self['liste'].getCurrent()[0][4]
		viewers = self['liste'].getCurrent()[0][5]
		type = self['liste'].getCurrent()[0][6]
		preference = self['liste'].getCurrent()[0][7]
		status = self['liste'].getCurrent()[0][8]
		self['name'].setText(title)
		self['handlung'].setText("Gender: %s\nPreference: %s\nType: %s\nLocation: %s\nViewers: %s\n%s" % (gender, preference, type, location, viewers, status))

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_('Please wait...'))
		url = BASEURL + name
		getPage(url, agent=cam4Agent).addCallback(self.play_stream).addErrback(self.dataError)

	def play_stream(self, data):
		url = re.findall('hlsUrl: \'(http.*?)\'', data, re.S)
		if url:
			playlisturl = url[-1] + '?referer=cam4.com&timestamp=%s' % str(int(time()*1000))
			getPage(playlisturl, agent=cam4Agent).addCallback(self.loadplaylist, url[-1]).addErrback(self.dataError)
		else:
			self.session.open(MessageBoxExt, _("Cam is currently offline."), MessageBoxExt.TYPE_INFO)

	def loadplaylist(self, data, baseurl):
		print baseurl
		self.bandwith_list = []
		match_sec_m3u8=re.findall('BANDWIDTH=(\d+).*?\n(.*?m3u8)', data, re.S)
		max = 0
		for x in match_sec_m3u8:
			if int(x[0]) > max:
				max = int(x[0])
		videoPrio = int(config_mp.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			bw = max
		elif videoPrio == 1:
			bw = max/2
		else:
			bw = max/3
		for each in match_sec_m3u8:
			bandwith,url = each
			self.bandwith_list.append((int(bandwith),url))
		_, best = min((abs(int(x[0]) - bw), x) for x in self.bandwith_list)

		url = baseurl.replace('playlist.m3u8','') + best[1]
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		mp_globals.player_agent = cam4Agent
		self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='cam4')