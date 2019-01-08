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

default_cover = "file://%s/sporttotal.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class sporttotalGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("sporttotal.tv")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "http://www.sporttotal.tv/live"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		preparse = re.search('<nav class="sport-selector">(.*?)</nav>', data, re.S)
		raw = re.findall('a\shref="(.*?)">(.*?)</a>', preparse.group(1), re.S)
		if raw:
			for (Url, Title) in raw:
				Url = "https://www.sporttotal.tv/live" + Url
				self.filmliste.append((decodeHtml(Title.strip()), Url))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False
		self['name'].setText('')

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(sporttotalSubGenreScreen, Link, Name)

class sporttotalSubGenreScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("sporttotal.tv")
		self['ContentTitle'] = Label("%s Livespiele:" % self.Name)

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		url = self.Link
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		pre1 = re.findall('id="livegames" class="livegame-table">(.*?)class="pagination live-pagnation">', data, re.S)
		pre2 = re.findall('id="upcoming-games" class="livegame-table">(.*?)class="pagination upcoming-pagnation">', data, re.S)
		if pre1:
			info = re.findall('class="table-link".*?tableLink\(\'(.*?)\'.*?class="date-filter">(.*?)</.*?class="teams">(.*?)</.*?class="division">(.*?)</', pre1[0], re.S)
			if info:
				for (url, date, teams, season) in info:
					match = "%s: %s, %s" % (season.strip(), date.strip(), stripAllTags(teams).strip())
					url = 'http://www.sporttotal.tv' + url
					self.genreliste.append((decodeHtml(match), url))
		if pre2:
			info = re.findall('class="table-link".*?tableLink\(\'(.*?)\'.*?class="date-filter">(.*?)</.*?class="teams">(.*?)</.*?class="division">(.*?)</', pre2[0], re.S)
			if info:
				for (url, date, teams, season) in info:
					match = "%s: %s, %s" % (season.strip(), date.strip(), stripAllTags(teams).strip())
					url = 'http://www.sporttotal.tv' + url
					self.genreliste.append((decodeHtml(match), url))
		if not pre1 and not pre2:
			self.genreliste.append((_("Currently no streams available"), None))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		self['name'].setText('')

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			getPage(url).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		streams = re.findall('file:\s"(.*?)",', data, re.S)
		if not streams:
			streams = re.findall('<source\ssrc="(.*?)"\stype="', data, re.S)
		if streams:
			url = streams[0]
			getPage(url).addCallback(self.loadplaylist, url).addErrback(self.dataError)

	def loadplaylist(self, data, baseurl):
		self.bandwith_list = []
		match_sec_m3u8=re.findall('#EXT-X-STREAM-INF:BANDWIDTH=(\d+).*?\n(.*?m3u8.*?)\n', data, re.S)
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
		if '/RECORD' in baseurl:
			url = baseurl.split('/RECORD')[0] + best[1]
		else:
			url = baseurl.split('index.m3u8')[0] + best[1]
		Name = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Name, url)], showPlaylist=False, ltype='sporttotal')