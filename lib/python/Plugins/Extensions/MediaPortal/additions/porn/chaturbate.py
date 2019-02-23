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

BASEURL = "https://chaturbate.com/"

config_mp.mediaportal.chaturbate_filter = ConfigText(default="all", fixed_size=False)
default_cover = "file://%s/chaturbate.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class chaturbateGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"yellow": self.keyFilter
		}, -1)

		self.filter = config_mp.mediaportal.chaturbate_filter.value

		self['title'] = Label("Chaturbate.com")
		self['ContentTitle'] = Label("Genre:")
		self['F3'] = Label(self.filter)

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		if config_mp.mediaportal.chaturbate_filter.value == "all":
			filter = ""
		else:
			filter = config_mp.mediaportal.chaturbate_filter.value + "/"
		url = BASEURL + 'tags/' + filter
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		self.genreliste = []
		parse = re.search('id="tag_table">(.*?)class="paging">', data, re.S)
		if parse:
			tags = re.findall('class="tag_row">.{0,5}<span class="tag">.{0,5}<a\shref="(.*?)"\stitle="(.*?)"', parse.group(1), re.S)
		if tags:
			for (Url, Title) in tags:
				self.genreliste.append(("#"+Title, Url.strip('/')))
		self.genreliste.sort()
		self.genreliste.insert(0, ("Exhibitionist", "exhibitionist-cams"))
		self.genreliste.insert(0, ("Other Region", "other-region-cams"))
		self.genreliste.insert(0, ("South American", "south-american-cams"))
		self.genreliste.insert(0, ("Asian", "asian-cams"))
		self.genreliste.insert(0, ("Philippines", "philippines-cams"))
		self.genreliste.insert(0, ("Euro Russian", "euro-russian-cams"))
		self.genreliste.insert(0, ("North American", "north-american-cams"))
		self.genreliste.insert(0, ("Mature (50+)", "mature-cams"))
		self.genreliste.insert(0, ("30 to 50", "30to50-cams"))
		self.genreliste.insert(0, ("20 to 30", "20to30-cams"))
		self.genreliste.insert(0, ("18 to 21", "18to21-cams"))
		self.genreliste.insert(0, ("Teen (18+)", "teen-cams"))
		self.genreliste.insert(0, ("HD", "hd-cams"))
		if (self.filter == "female" or self.filter == "couple"):
			self.genreliste.insert(0, ("Couple", "couple-cams"))
			self.genreliste.insert(0, ("Female", "female-cams"))
		elif self.filter == "male":
			self.genreliste.insert(0, ("Male", "male-cams"))
		elif self.filter == "trans":
			self.genreliste.insert(0, ("Transsexual", "trans-cams"))
		self.genreliste.insert(0, ("Featured", ""))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(chaturbateFilmScreen, Link, Name)

	def keyFilter(self):
		if self.filter == "all":
			self.filter = "female"
			config_mp.mediaportal.chaturbate_filter.value = "female"
		elif self.filter == "female":
			self.filter = "couple"
			config_mp.mediaportal.chaturbate_filter.value = "couple"
		elif self.filter == "couple":
			self.filter = "male"
			config_mp.mediaportal.chaturbate_filter.value = "male"
		elif self.filter == "male":
			self.filter = "trans"
			config_mp.mediaportal.chaturbate_filter.value = "trans"
		elif self.filter == "trans":
			self.filter = "all"
			config_mp.mediaportal.chaturbate_filter.value = "all"
		else:
			self.filter = "all"
			config_mp.mediaportal.chaturbate_filter.value = "all"

		config_mp.mediaportal.chaturbate_filter.save()
		configfile_mp.save()
		self['F3'].setText(self.filter)
		self.layoutFinished()

class chaturbateFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		if config_mp.mediaportal.chaturbate_filter.value == "all":
			self.filter = ""
		else:
			self.filter = config_mp.mediaportal.chaturbate_filter.value + "/"
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

		self['title'] = Label("Chaturbate.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if self.Name == "Featured":
			url = BASEURL + "?page=%s" % self.page
		else:
			if self.Name == "Female" or self.Name == "Couple" or self.Name == "Male" or self.Name == "Transsexual" or "tag/" in self.Link:
				url = BASEURL + "%s/?page=%s" % (self.Link, self.page)
			else:
				url = BASEURL + "%s/%s?page=%s" % (self.Link, self.filter, self.page)
		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()

	def loadPageData(self, data):
		self.ml.moveToIndex(0)
		self.getLastPage(data, 'class="paging">(.*?)</ul>')
		preparse = re.search('id="room_list"(.*?)class="banner">', data, re.S)
		Movies = re.findall('<li class="room_list_room.*?>.<a\shref="(.*?)".*?<img\ssrc=".*?".*?gender(\w)">(\d+)</span>.*?<li\stitle(?:="(.*?)"|)>.*?location.*?>(.*?)</li>.*?class="cams">(.*?)</li>.*?</div>.*?</li>', preparse.group(1), re.S)
		if Movies:
			for (Url, Gender, Age, Description, Location, Viewers) in Movies:
				if not Description:
					Description = ""
				Title = Url.strip('\/')
				Image = "https://cbjpeg.stream.highwebmedia.com/stream?room=" + Url.strip('\/') + "&f=" + str(random.random())
				self.filmliste.append((Title, Url, Image, decodeHtml(Description), Gender, Age, decodeHtml(Location), Viewers))
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
		desc = self['liste'].getCurrent()[0][3]
		gender = self['liste'].getCurrent()[0][4]
		age = self['liste'].getCurrent()[0][5]
		location = self['liste'].getCurrent()[0][6]
		viewers = self['liste'].getCurrent()[0][7]
		self['name'].setText(title)
		if gender == "f":
			gender = "female"
		elif gender == "m":
			gender = "male"
		elif gender == "c":
			gender = "couple"
		elif gender == "s":
			gender = "transsexual"
		self['handlung'].setText("Age: %s, Gender: %s, Location: %s\n%s\n%s" % (age, gender, location, viewers, desc))

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][0]
		self['name'].setText(_('Please wait...'))
		url = "https://chaturbate.com/" + name
		getPage(url).addCallback(self.getplaylist).addErrback(self.dataError)

	def getplaylist(self, data):
		url = re.findall('(http[s]?://edge.*?.stream.highwebmedia.com.*?m3u8)', data)
		if url:
			getPage(url[0]).addCallback(self.loadplaylist, url[0]).addErrback(self.dataError)
		else:
			self.session.open(MessageBoxExt, _("Cam is currently offline."), MessageBoxExt.TYPE_INFO)

	def loadplaylist(self, data, baseurl):
		self.bandwith_list = []
		match_sec_m3u8=re.findall('BANDWIDTH=(\d+).*?RESOLUTION=(\d+).*?\n(.*?m3u8)', data, re.S)
		max = 0
		for x in match_sec_m3u8:
			if (int(x[0]) > max) and (int(x[1]) <= 1920):
				max = int(x[0])
		videoPrio = int(config_mp.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			bw = max
		elif videoPrio == 1:
			bw = max/2
		else:
			bw = max/3
		for each in match_sec_m3u8:
			bandwith,res,url = each
			if int(res) <= 1920:
				self.bandwith_list.append((int(bandwith),url))
		_, best = min((abs(int(x[0]) - bw), x) for x in self.bandwith_list)

		url = baseurl.replace('playlist.m3u8','') + best[1]
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='chaturbate')