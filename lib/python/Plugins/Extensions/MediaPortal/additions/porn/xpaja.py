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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import TwAgentHelper

agent='Mozilla/5.0 (Windows NT 6.1; rv:44.0) Gecko/20100101 Firefox/44.0'
default_cover = "file://%s/xpaja.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class xpajaGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("xpaja.net")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "https://www.xpaja.net/categories"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('.*?Categorías de  Vídeos</h1>(.*?)separador', data, re.S)
		if parse:
			Cats = re.findall('class="col-md-3.*?<a href="(/category/(.*?))">.*?<img src="(.*?)">', parse.group(1), re.S)
			if Cats:
				for (Url, Title, Image) in Cats:
					Url = "https://www.xpaja.net" + Url
					Image = "https://www.xpaja.net" + Image
					Title = Title.replace('-',' ').title().replace('Videos Hd','HD')
					self.genreliste.append((Title, Url, Image))
		self.genreliste.insert(0, ("Columbian", "https://www.xpaja.net/tag/colombianas", default_cover))
		self.genreliste.insert(0, ("Mexican", "https://www.xpaja.net/tag/mexicana", default_cover))
		self.genreliste.insert(0, ("Blowjob", "https://www.xpaja.net/tag/mamadas", default_cover))
		self.genreliste.insert(0, ("Riding", "https://www.xpaja.net/tag/ride", default_cover))
		self.genreliste.sort()
		self.genreliste.insert(0, ("Recommended", "https://www.xpaja.net/recommended", default_cover))
		self.genreliste.insert(0, ("Most Viewed", "https://www.xpaja.net/most-viewed", default_cover))
		self.genreliste.insert(0, ("Top Rated", "https://www.xpaja.net/top-rated", default_cover))
		self.genreliste.insert(0, ("Most Recent", "https://www.xpaja.net/videos", default_cover))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(xpajaFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = callback.replace(' ', '-')
			self.session.open(xpajaFilmScreen, Link, Name)

class xpajaFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("xpaja.net")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.tw_agent_hlp = TwAgentHelper()

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "https://www.xpaja.net/search/videos/%s/page/%s" % (self.Link, str(self.page))
		else:
			url = "%s/page/%s" % (self.Link, str(self.page))
		self.tw_agent_hlp.getWebPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</ul>', '.*[\/|>](\d+)[\"|<]')
		Movies = re.findall('class="preload".*?thumb-post"\ssrc="(.*?)"\salt="(.*?)".*?amount">(.*?)</div.*?href="(.*?)".*?post-inf">(.*?)\sVisi', data, re.S)
		if Movies:
			for (Image, Title, Runtime, Url, Views) in Movies:
				Url = "https://www.xpaja.net/" + Url
				Image = "https://www.xpaja.net" + Image
				Views = Views.replace(',','')
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Url = self['liste'].getCurrent()[0][1]
		if Url == None:
			return
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nViews: %s" % (runtime, views))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link == None:
			return
		self.keyLocked = True
		getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall("<source src=\"(.*?)\" type='video/mp4'", data, re.S)
		if videoPage:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			url = "https://www.xpaja.net/" + videoPage[0]
			self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='xpaja')