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
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

default_cover = "file://%s/liveleak.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class LiveLeakScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("LiveLeak.com")
		self['ContentTitle'] = Label("Genre:")
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Featured", "https://www.liveleak.com/rss?featured=1&page="))
		self.genreliste.append(("Upcoming", "https://www.liveleak.com/rss?upcoming=1&page="))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(LiveLeakClips, streamGenreLink, Name)

class LiveLeakClips(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, Name):
		self.streamGenreLink = streamGenreLink
		self.Name = Name
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

		self.keyLocked = True
		self.page = 1
		self.lastpage = 999
		self['title'] = Label("LiveLeak.com")
		self['ContentTitle'] = Label("Auswahl: %s" %self.Name)

 		self['Page'] = Label(_("Page:"))
		self['page'] = Label("1")
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "%s%s&safe_mode=off" % (self.streamGenreLink, str(self.page))
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		rssfeed = re.findall('<item>.*?<title>(.*?)</title>.*?<link>(http[s]?://www.liveleak.com/view.*?)</link>.*?<description>(.*?)</description>.*?<media:thumbnail\surl="(.*?)"', data, re.S)
		if rssfeed:
			self.feedliste = []
			for (title,url,desc,image) in rssfeed:
				if not re.match('LiveLeak.com Rss Feed', title, re.S|re.I):
					if image.startswith('//'):
						image = "https:" + image
					self.feedliste.append((decodeHtml(title).strip(),url,image,decodeHtml(desc.strip())))
			self.ml.setList(map(self._defaultlistleft, self.feedliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.feedliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		desc = self['liste'].getCurrent()[0][3]
		self['name'].setText(Title)
		self['handlung'].setText(desc)
		self['page'].setText(str(self.page))
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		title = self['liste'].getCurrent()[0][0]
		Stream = re.findall('source\ssrc="(.*?)"', data, re.S)
		if Stream:
			self.session.open(SimplePlayer, [(title, Stream[0])], showPlaylist=False, ltype='liveleak')
		else:
			videoPage = re.findall('//www.youtube.com/(v|embed)/(.*?)\?.*?"', data, re.S)
			if videoPage:
				self.session.open(YoutubePlayer,[(title, videoPage[0][1], None)],playAll= False,showPlaylist=False,showCover=False)
			else:
				self.session.open(MessageBoxExt, _("No videos found!"), MessageBoxExt.TYPE_INFO, timeout=3)