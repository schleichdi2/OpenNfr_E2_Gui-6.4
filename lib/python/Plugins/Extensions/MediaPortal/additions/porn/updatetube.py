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

class updatetubeGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		global default_cover
		if self.mode == "updatetube":
			self.portal = "UpdateTube.com"
			self.baseurl = "www.updatetube.com"
			default_cover = "file://%s/updatetube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		if self.mode == "pinkrod":
			self.portal = "Pinkrod.com"
			self.baseurl = "www.pinkrod.com"
			default_cover = "file://%s/pinkrod.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		if self.mode == "hotshame":
			self.portal = "hotshame.com"
			self.baseurl = "www.hotshame.com"
			default_cover = "file://%s/hotshame.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		if self.mode == "thenewporn":
			self.portal = "TheNewPorn.com"
			self.baseurl = "www.thenewporn.com"
			default_cover = "file://%s/thenewporn.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		if self.mode == "pornsharing":
			self.portal = "PornSharing.com"
			self.baseurl = "www.pornsharing.com"
			default_cover = "file://%s/pornsharing.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

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

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		url = "http://%s/categories/" % self.baseurl
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="cat(?:egories|)">(.*?)class="(?:clr|clearfix)"', data, re.S)
		Cats = re.findall('class="(?:ic|item)">.*?<a\shref="(.*?)"(?:\sclass="img3"|)\stitle="(.*?)".*?<img.*?src="(.*?)">', parse.group(1), re.S)
		if Cats:
			for (Url, Title, Image) in Cats:
				Title = Title.replace('HD ','').replace(' Sex','')
				self.genreliste.append((Title, Url, Image))
			self.genreliste.sort()
		if self.mode == "pornsharing":
			most = "videos/viewed"
			rated = "videos/rated"
		else:
			most = "most-popular"
			rated = "top-rated"
		self.genreliste.insert(0, ("Most Popular", "http://%s/%s" % (self.baseurl, most), default_cover))
		self.genreliste.insert(0, ("Top Rated", "http://%s/%s" % (self.baseurl, rated), default_cover))
		self.genreliste.insert(0, ("Newest", "http://%s" % self.baseurl, default_cover))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
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
			self.session.open(updatetubeFilmScreen, Link, Name, self.portal, self.baseurl)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = 'http://%s/search/?q=%s' % (self.baseurl, self.suchString)
			self.session.open(updatetubeFilmScreen, Link, Name, self.portal, self.baseurl)

class updatetubeFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal, baseurl):
		self.Link = Link
		self.portal = portal
		self.baseurl = baseurl
		self.Name = Name

		global default_cover
		if self.portal == "UpdateTube.com":
			default_cover = "file://%s/updatetube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		if self.portal == "Pinkrod.com":
			default_cover = "file://%s/pinkrod.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		if self.portal == "hotshame.com":
			default_cover = "file://%s/hotshame.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		if self.portal == "TheNewPorn.com":
			default_cover = "file://%s/thenewporn.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		if self.portal == "PornSharing.com":
			default_cover = "file://%s/pornsharing.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

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

		self['title'] = Label(self.portal)
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
		cat = self.Link
		search = re.search('/search/(.*)', cat, re.S)
		if search:
			url = 'http://%s/search/%s/%s' % (self.baseurl, str(self.page), str(search.group(1)))
		elif self.page == 1:
			url = "%s" % (self.Link)
		else:
			if self.Name == "Newest" and self.portal == "PornSharing.com":
				url = "%s/videos/%s" % (self.Link, str(self.page))
			else:
				url = "%s/%s" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '(?:id="pgn">|class="pagination">)(.*?)</nav>', '.*\/(\d+)')
		Movies = re.findall('class="(?:ic|item)".*?href="(.*?)"(?:\sclass="img"|).*?title="(.*?)"(?:\starget="_blank"|)(?:\sclass="lnk"|)>.*?data-src="(.*?)"', data, re.S)
		if Movies:
			for (Url, Title, Image) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('<source src="(.*?)"', data, re.S)
		if videoPage:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, videoPage[-1].replace('&amp;','&'))], showPlaylist=False, ltype='updatetube')