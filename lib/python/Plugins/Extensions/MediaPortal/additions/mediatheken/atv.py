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
default_cover = "file://%s/atv.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class atvGenreScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("ATV Mediathek")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		url = "http://atv.at/mediathek"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('class="mod_programs">(.*?)/mod_programs', data, re.S)
		if parse:
			raw = re.findall('href="(.*?)">.*?img\ssrc=".*?path=(.*?\.jpg).*?"\salt="(.*?)"', parse.group(), re.S)
			if raw:
				for (Url, ImageId, Title) in raw:
					Image = "https://static.atv.cdn.tvnext.tv/static/assets/cms/%s" % urllib.unquote(ImageId)
					self.filmliste.append((decodeHtml(Title), Url, Image))
				self.ml.setList(map(self._defaultlistcenter, self.filmliste))
				self.keyLocked = False
				self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
				self.showInfos()

	def showInfos(self):
		name = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(decodeHtml(name))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(atvListScreen, Link, Name)

class atvListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
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

		self['title'] = Label("ATV Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))

		self.filmliste = []
		self.handlung = ''
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		getPage(self.Link).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self['name'].setText(_("Please wait..."))
		parse = re.search('<!--\smod_teasers\s-->(.*?)<!--\s/mod_teasers\s-->', data, re.S)
		if not re.match('http://atv.at/uri/', self.Link):
			handlung = re.search('<meta\sname="description"\scontent="(.*?)"', data, re.S)
			if handlung:
				self.handlung = handlung.group(1)
		if parse:
			raw = re.findall('<li class="teaser">.*?href="(.*?)".*?img\ssrc=".*?path=(.*?\.jpg).*?class="title">(.*?)<', parse.group(), re.S)
			if raw:
				for (Url, ImageId, Title) in raw:
					Image = "https://static.atv.cdn.tvnext.tv/static/assets/cms/%s" % urllib.unquote(ImageId)
					self.filmliste.append((decodeHtml(Title), Url, Image))
		nextpage = re.search('data-jsb="url=(.*?)" style=.*?Weitere Folgen', data, re.S)
		if nextpage:
			self.Link = urllib.unquote_plus(nextpage.group(1))
			self.loadPage()
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"), "",""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None ,1 ,1, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		self['handlung'].setText(decodeHtml(self.handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link).addCallback(self.getStreamLink).addErrback(self.dataError)
		self['name'].setText(_("Please wait..."))

	def getStreamLink(self, data):
		Name = self['liste'].getCurrent()[0][0]
		Linkliste = []
		part = re.search('jsb_video/VideoPlaylist(.*?)/detail_content', data, re.S)
		if part:
			raw = re.findall('quot;(rtsp:\\\/\\\/109.68.230.208:1935\\\/vod\\\/_definst_\\\/.*?.mp4)', part.group(1), re.S)
			if not raw:
				raw = re.findall('quot;(http[s]?:\\\/\\\/(?:blocked.|)multiscreen.atv.cdn.tvnext.tv\\\/\d+\\\/\d+\\\/(?:HD|SD)\\\/hbbtv\\\/\d+(?:_\d|).mp4)', part.group(1), re.S)
				if not raw:
					raw = re.findall('quot;(http[s]?:\\\/\\\/(?:blocked.|)(?:multiscreen.atv.cdn.tvnext.tv|atv.at)\\\/\d+\\\/\d+\\\/(?:HD|SD)\\\/(?:\d+)(?:\\\/index)(?:_\d|).m3u8)', part.group(1), re.S)
			if raw:
				for Link in raw:
					Link = Link.replace('\/','/').replace('blocked.','').replace('blocked-','')
					Streampart = "Teil %s" % str(len(Linkliste)+1)
					Linkliste.append((Streampart, Link))
		self.keyLocked = False
		if len(Linkliste) == 1:
			self.session.open(SimplePlayer, [(Name, Linkliste[0][1])], showPlaylist=False, ltype='atv')
		elif len(Linkliste) >= 1:
			self.session.open(atvPartScreen, Name, Linkliste)
		self['name'].setText(Name)

class atvPartScreen(MPScreen):

	def __init__(self, session, Name, Linkliste):
		self.Linkliste = Linkliste
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
		}, -1)

		self['title'] = Label("ATV Mediathek")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.parseData)

	def parseData(self):
		self.ml.setList(map(self._defaultlistcenter, self.Linkliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self['name'] = Label("%s" % self.Name)

	def keyOK(self):
		if self.keyLocked:
			return
		playIdx = self['liste'].getSelectedIndex()
		self.session.open(SimplePlayer, self.Linkliste, playIdx=playIdx, showPlaylist=False, playAll=True, ltype='atv')