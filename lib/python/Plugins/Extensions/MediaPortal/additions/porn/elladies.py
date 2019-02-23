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
#############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

BASE_URL = 'http://search.el-ladies.com'

default_cover = "file://%s/elladies.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class elladiesGenreScreen(MPScreen):

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

		self['title'] = Label("EL-Ladies.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		getPage(BASE_URL).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('<select id="selSearchNiche"(.*?)</select>', data, re.S)
		if parse:
			genre = re.findall('<option value="(\d{0,2})">(.*?)<', parse.group(1), re.S)
			if genre:
				for genrenr, genrename in genre:
					if not re.match('(Bizarre|Gay|Men|Piss|Scat)', genrename):
						self.genreliste.append((genrename.replace('&amp;', '&'), genrenr))
		self.genreliste.insert(0, ("--- Search ---", None))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		streamGenreName = self['liste'].getCurrent()[0][0]
		if streamGenreName == "--- Search ---":
			self.suchen()
		else:
			streamSearchString = ""
			streamGenreID = self['liste'].getCurrent()[0][1]
			self.session.open(elladiesFilmScreen, streamSearchString, streamGenreName, streamGenreID)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			streamGenreName = self['liste'].getCurrent()[0][0]
			self.suchString = urllib.quote(callback).replace(' ', '+')
			streamSearchString = self.suchString
			streamGenreID = ""
			self.session.open(elladiesFilmScreen, streamSearchString, streamGenreName, streamGenreID)

class elladiesFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, SearchString, streamGenreName, CatID):
		self.SearchString = SearchString
		self.CatID = CatID
		self.Name = streamGenreName
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
			"yellow" : self.keyHD,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("EL-Ladies.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label("Filter")

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.suchString = ''
		self.HD = 0

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = '%s/?search=%s&fun=0&niche=%s&pnum=%s&hd=%s' % (BASE_URL, self.SearchString, self.CatID, str(self.page), self.HD)
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pageNav">(.*?)</div>')
		Movies = re.findall('<a\shref="http://just.eroprofile.com/play/(.*?)".*?<img\ssrc="(.*?)".*?<div>(.*?)</div>', data, re.S)
		if Movies:
			for (ID, Image, Cat) in Movies:
				if not re.match('(Bizarre|Gay|Men|Piss|Scat)', Cat):
					Title = decodeHtml(Cat) + ' - ' + ID
					Image = Image.replace('&amp;','&')
					self.filmliste.append((Title, ID, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		self.playtitle = None
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)
		url = self['liste'].getCurrent()[0][1]
		url = 'http://just.eroprofile.com/play/' + url
		getPage(url).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		title = re.search('<title>(.*?)</title>', data, re.S)
		self['name'].setText(decodeHtml(title.group(1)))
		handlung = re.search('name="description"\scontent="(.*?)"\s/>', data, re.S)
		if self.HD == 0:
			filter = "All"
		else:
			filter = "HD"
		self.playtitle = handlung.group(1)
		self['handlung'].setText(decodeHtml(handlung.group(1))+"\n\nFilter: "+filter)

	def keyHD(self):
		if self.HD == 1:
			self.HD = 0
		else:
			self.HD = 1
		self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		if Title == "--- Search ---":
			self.suchen()
		else:
			url = self['liste'].getCurrent()[0][1]
			self.keyLocked = True
			url = 'http://just.eroprofile.com/play/' + url
			getPage(url).addCallback(self.getVideoPage).addErrback(self.dataError)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = urllib.quote(callback).replace(' ', '+')
			self.SearchString = self.suchString
			self.loadPage()

	def getVideoPage(self, data):
		videoPage = re.findall(',file:\'(.*?)\'', data, re.S)
		if videoPage:
			for url in videoPage:
				self.keyLocked = False
				self.session.open(SimplePlayer, [(self.playtitle, url)], showPlaylist=False, ltype='elladies')