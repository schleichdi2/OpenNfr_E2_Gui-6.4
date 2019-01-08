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

default_cover = "file://%s/fail.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class failScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"left" : self.keyLeft,
			"right" : self.keyRight,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Fail.to")
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "http://www.fail.to/genre/1-videos/p-%s" % str(self.page)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.getLastPage(data, '', 'class="pagination">.*?<strong>(.*?)</strong>')
		parse = re.search('<body>(.*?)class="pagination">', data, re.S)
		Videos = re.findall('class="entry">.*?</span><a href="(.*?)" title=".*?">(.*?)</a></h3>.*?class="preview".*?<img src="(.*?)".*?class="description">(.*?)</div>', parse.group(1), re.S)
		if Videos:
			self.filmliste = []
			for (Url, Title, Image, Descr) in Videos:
				Url = "http://www.fail.to" + Url
				Image = "http://www.fail.to" + Image
				Descr = stripAllTags(Descr).strip()
				self.filmliste.append((Title, Url, Image, Descr))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		PicLink = self['liste'].getCurrent()[0][2]
		Descr = self['liste'].getCurrent()[0][3]
		self['name'].setText(Title)
		self['handlung'].setText(Descr)
		CoverHelper(self['coverArt']).getCover(PicLink)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		Title = self['liste'].getCurrent()[0][0]
		Stream = re.findall("'file': '(.*?)'", data)
		if Stream:
			Stream = "http://www.fail.to" + Stream[0]
			self.session.open(SimplePlayer, [(Title, Stream)], showPlaylist=False, ltype='failto')
		else:
			videoPage = re.findall('www.youtube.com/(v|embed)/(.*?)"', data, re.S)
			if videoPage:
				self.session.open(YoutubePlayer,[(Title, videoPage[0][1], None)],playAll= False,showPlaylist=False,showCover=False)