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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
from Plugins.Extensions.MediaPortal.resources.debuglog import printlog as printl

BASE_URL = "http://api.tvnow.de/v3/"
nowAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
default_cover = "file://%s/tvnow.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class tvnowFirstScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("TVNOW")
		self['ContentTitle'] = Label(_("Stations:"))
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.senderliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)

	def genreData(self):
		self.senderliste.append(("RTL", "rtl", default_cover))
		self.senderliste.append(("VOX", "vox", default_cover))
		self.senderliste.append(("RTL2", "rtl2", default_cover))
		self.senderliste.append(("NITRO", "nitro",  default_cover))
		self.senderliste.append(("SUPER RTL", "superrtl", default_cover))
		self.senderliste.append(("n-tv", "ntv", default_cover))
		self.senderliste.append(("RTLplus", "rtlplus",  default_cover))
		self.senderliste.append(("Watchbox", "watchbox",  "file://%s/watchbox.png" % (config_mp.mediaportal.iconcachepath.value + "logos")))
		self.ml.setList(map(self._defaultlistcenter, self.senderliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.senderliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)
		Name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_("Selection:") + " " + Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Image = self['liste'].getCurrent()[0][2]
		self.session.open(tvnowSubGenreScreen, Link, Name, Image)

class tvnowSubGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Image):
		self.Link = Link
		self.Name = Name
		self.Image = Image
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

		self['title'] = Label("TVNOW")
		self['ContentTitle'] = Label(_("Selection:"))
		self['name'] = Label(_("Selection:") + " " + self.Name)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		if self.Link == "watchbox":
			cats = "%22serie%22,%22film%22"
		else:
			cats = "%22serie%22,%22news%22"
		url = BASE_URL + "formats?fields=title,seoUrl,icon,defaultImage169Logo,defaultImage169Format&filter=%7B%22Station%22:%22" + self.Link + "%22,%22Disabled%22:%220%22,%22CategoryId%22:%7B%22containsIn%22:%5B" + cats + "%5D%7D%7D&maxPerPage=500&page=1"
		getPage(url, agent=nowAgent).addCallback(self.parseData).addErrback(self.dataError)
		if self.Link == "watchbox":
			url = BASE_URL + "formats?fields=title,seoUrl,icon,defaultImage169Logo,defaultImage169Format&filter=%7B%22Station%22:%22" + self.Link + "%22,%22Disabled%22:%220%22,%22CategoryId%22:%7B%22containsIn%22:%5B" + cats + "%5D%7D%7D&maxPerPage=500&page=2"
			getPage(url, agent=nowAgent).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		nowdata = json.loads(data)
		for node in nowdata["items"]:
			if str(node["icon"]) == "new" or str(node["icon"]) == "free":
				image = str(node["defaultImage169Logo"])
				if image == "":
					image = str(node["defaultImage169Format"])
				if image == "":
					image = self.Image
				self.filmliste.append((str(node["title"]), str(node["seoUrl"]), image))
		self.filmliste.sort(key=lambda t : t[0].lower())
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)
		Name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_("Selection:") + " " + self.Name + ":" + Name)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Name = self.Name + ":" + self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Image = self['liste'].getCurrent()[0][2]
		self.session.open(tvnowStaffelScreen, Link, Name, Image)

class tvnowStaffelScreen(MPScreen):

	def __init__(self, session, Link, Name, Image):
		self.Link = Link
		self.Name = Name
		self.Image = Image
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

		self['title'] = Label("TVNOW")
		self['ContentTitle'] = Label(_("Seasons:"))
		self['name'] = Label(_("Selection:") + " " + self.Name)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = BASE_URL + "formats/seo?fields=*,formatTabs.*,annualNavigation.*&name=" + self.Link + ".php"
		getPage(url, agent=nowAgent).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		nowdata = json.loads(data)
		if not nowdata["tabSeason"]:
			from datetime import date
			id = str(nowdata['id'])
			for node in nowdata['annualNavigation']['items']:
				year = int(node["year"])
				months = node['months']
				for m in range(1, 13, 1):
					m1 = (m + 1)
					if m1 > 12: m1 = m1 % 12
					days = (date(year + m/12, m1, 1)  - date(year, m, 1)).days
					m = str(m)
					if not m in months:
						continue
					month = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
					title = '%s %s' % (month[int(m)-1], year)
					url = BASE_URL + 'movies?fields=*,format,pictures,broadcastStartDate&filter=%7B%22BroadcastStartDate%22:%7B%22between%22:%7B%22start%22:%22{0}-{1}-{2}+00:00:00%22,%22end%22:+%22{3}-{4}-{5}+23:59:59%22%7D%7D,+%22FormatId%22+:+{6}%7D&maxPerPage=500&order=BroadcastStartDate+desc'.format(year, m.zfill(2), '01', year, m.zfill(2), str(days).zfill(2), id)
					self.filmliste.append((title, url))
			self.filmliste.reverse()
		else:
			try:
				for node in nowdata["formatTabs"]["items"]:
					self.filmliste.append((str(node["headline"]), str(node["id"])))
			except:
				pass
		if len(self.filmliste) == 0:
			self.filmliste.append((_('Currently no seasons available!'), None, None, None))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
		else:
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False
		CoverHelper(self['coverArt']).getCover(self.Image)
		self.showInfos()

	def showInfos(self):
		Name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_("Selection:") + " " + self.Name + ":" + Name)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		Name = self.Name + ":" + self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Link:
			self.session.open(tvnowEpisodenScreen, Link, Name, self.Image)

class tvnowEpisodenScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Image):
		self.Link = Link
		self.Name = Name
		self.Image = Image
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

		self['title'] = Label("TVNOW")
		self['ContentTitle'] = Label(_("Episodes:"))
		self['name'] = Label(_("Selection:") + " " + self.Name)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.container = 0

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		if BASE_URL in self.Link:
			self.container += 1
			getPage(self.Link, agent=nowAgent).addCallback(self.parseContainer, id=True, annual=True).addErrback(self.dataError)
		else:
			url = BASE_URL + "formatlists/" + self.Link + "?fields=*,formatTabPages.*,formatTabPages.container.*,formatTabPages.container.movies.format.*,formatTabPages.container.movies.pictures"
			getPage(url, agent=nowAgent).addCallback(self.parseData).addErrback(self.dataError)

	def loadContainer(self, id):
		url = BASE_URL + "containers/" + id + "/movies?fields=*,format.*,pictures&maxPerPage=500"
		getPage(url, agent=nowAgent).addCallback(self.parseContainer, id=True).addErrback(self.dataErrorContainer)

	def parseData(self, data):
		nowdata = json.loads(data)
		try:
			for node in nowdata["formatTabPages"]["items"]:
				try:
					try:
						containerid = str(node["container"]["id"])
						if containerid:
							self.container += 1
							self.loadContainer(containerid)
					except:
						for nodex in node["container"]["movies"]["items"]:
							try:
								if nodex["free"] and not nodex["isDrm"]:
									try:
										image = "http://ais.tvnow.de/rtlnow/%s/660x660/formatimage.jpg" % nodex["pictures"]["default"][0]["id"]
									except:
										image = self.Image
									if nodex.has_key("broadcastStartDate"):
										date = str(nodex["broadcastStartDate"])
									else:
										date = ""
									if nodex.has_key("episode"):
										episode = str(nodex["episode"])
									else:
										episode = ""
									descr = ""
									if date != "":
										date = re.findall('(\d{4})-(\d{2})-(\d{2}) (.*?)$', date)
										date = date[0][2] + "." + date[0][1] + "." + date[0][0] + ", " + date[0][3]
										descr = "Datum: " + date + "\n"
									if (episode != "None" and episode != ""):
										descr = descr + "Episode: " + episode + "\n"
									if descr != "":
										descr = descr + "\n"
									descrlong = str(nodex["articleLong"])
									if descrlong == "":
										descrshort = str(nodex["articleShort"])
									if descrlong != "":
										descr = descr + descrlong
									else:
										descr = descr + descrshort
									self.filmliste.append((str(nodex["title"]), str(nodex["id"]), descr, image))
							except:
								continue
				except:
					continue
			self.parseContainer("", False)
		except:
			pass

	def dataErrorContainer(self, error):
		self.container -= 1
		printl(error,self,"E")
		self.parseContainer("", False)

	def parseContainer(self, data, id=False, annual=False):
		if id:
			self.container -= 1
			nowdata = json.loads(data)
			try:
				for nodex in nowdata["items"]:
					try:
						if nodex["free"] and not nodex["isDrm"]:
							try:
								image = "http://ais.tvnow.de/rtlnow/%s/660x660/formatimage.jpg" % nodex["pictures"]["default"][0]["id"]
							except:
								image = self.Image
							if nodex.has_key("broadcastStartDate"):
								date = str(nodex["broadcastStartDate"])
							else:
								date = ""
							descr = ""
							if date != "":
								date = re.findall('(\d{4})-(\d{2})-(\d{2}) (.*?)$', date)
								date = date[0][2] + "." + date[0][1] + "." + date[0][0] + ", " + date[0][3]
								descr = "Datum: " + date + "\n"
							if nodex.has_key("season"):
								season = str(nodex["season"])
							else:
								season = ""
							if nodex.has_key("episode"):
								episode = str(nodex["episode"])
							else:
								episode = ""
							if (season != "None" and season != ""):
								descr = descr + "Staffel: " + season + "\n"
							if (episode != "None" and episode != ""):
								descr = descr + "Episode: " + episode + "\n"
							if descr != "":
								descr = descr + "\n"
							descrlong = str(nodex["articleLong"])
							if descrlong == "":
								descrshort = str(nodex["articleShort"])
							if descrlong != "":
								descr = descr + descrlong
							else:
								descr = descr + descrshort
							self.filmliste.append((str(nodex["title"]), str(nodex["id"]), descr, image))
					except:
						continue
			except:
				pass
			if annual:
				self.parseContainer("", False)
		printl(self.container,self,"I")
		if self.container == 0:
			if len(self.filmliste) == 0:
				self.filmliste.append((_('Currently no playable/free episodes available!'), None, None, None))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
			self.showInfos()

	def showInfos(self):
		Descr = self['liste'].getCurrent()[0][2]
		Image = self['liste'].getCurrent()[0][3]
		if Descr:
			self['handlung'].setText(Descr)
		CoverHelper(self['coverArt']).getCover(Image)
		Name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_("Selection:") + " " + self.Name + ":" + Name)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		id = self['liste'].getCurrent()[0][1]
		if id:
			url = 'http://api.tvnow.de/v3/movies/%s?fields=manifest' % id
			getPage(url, agent=nowAgent).addCallback(self.get_stream).addErrback(self.dataError)

	def get_stream(self, data):
		nowdata = json.loads(data)
		format = None
		dashclear = nowdata["manifest"]["dashclear"]
		url = str(dashclear.replace('dash', 'hls').replace('.mpd','fairplay.m3u8'))
		if "?" in url:
			url = url.split('?')[0]
		getPage(url, agent=nowAgent).addCallback(self.loadplaylist, url).addErrback(self.dataError)

	def loadplaylist(self, data, baseurl):
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
		url = baseurl.replace('fairplay.m3u8', '') + best[1]
		Name = self['liste'].getCurrent()[0][0]
		mp_globals.player_agent = nowAgent
		self.session.open(SimplePlayer, [(Name, url)], showPlaylist=False, ltype='tvnow')