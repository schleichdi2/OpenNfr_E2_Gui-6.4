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

default_cover = "file://%s/eroprofile.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class eroprofileGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("EroProfile.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("--- Search ---", ""))
		self.genreliste.append(("Newest", "home"))
		self.genreliste.append(("Most Popular", "popular"))
		self.genreliste.append(("Amateur Moms/Mature", "13"))
		self.genreliste.append(("Amateur Teens", "14"))
		self.genreliste.append(("Amateurs", "12"))
		self.genreliste.append(("Asian", "19"))
		self.genreliste.append(("Ass", "27"))
		self.genreliste.append(("BDSM", "25"))
		self.genreliste.append(("Big Ladies", "5"))
		self.genreliste.append(("Big Tits", "11"))
		self.genreliste.append(("Bisexual", "18"))
		self.genreliste.append(("Black / Ebony", "20"))
		self.genreliste.append(("Celeb", "23"))
		self.genreliste.append(("Dogging", "33"))
		self.genreliste.append(("Facial / Cum", "24"))
		self.genreliste.append(("Fetish / Kinky", "10"))
		self.genreliste.append(("Fucking / Sucking", "26"))
		self.genreliste.append(("Fun", "17"))
		self.genreliste.append(("Hairy", "7"))
		self.genreliste.append(("Interracial", "15"))
		self.genreliste.append(("Lesbian", "6"))
		self.genreliste.append(("Lingerie / Panties", "30"))
		self.genreliste.append(("Nudist / Voyeur / Public", "16"))
		self.genreliste.append(("Other / Cartoon", "28"))
		self.genreliste.append(("Pregnant", "32"))
		self.genreliste.append(("Shemale / TS", "9"))
		self.genreliste.append(("Squirting", "34"))
		self.genreliste.append(("Swingers / Gangbang", "8"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			ID = self['liste'].getCurrent()[0][1]
			self.session.open(eroprofileFilmScreen, '', Name, ID)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = self['liste'].getCurrent()[0][0]
			self.suchString = urllib.quote(callback).replace(' ', '+')
			self.session.open(eroprofileFilmScreen, self.suchString, Name, '')

class eroprofileFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, SearchString, Name, ID):
		self.SearchString = SearchString
		self.ID = ID
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

		self['title'] = Label("EroProfile.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if self.ID == "popular":
			url = 'http://www.eroprofile.com/m/videos/popular?niche=13.14.12.19.27.25.5.11.18.20.23.24.10.26.17.7.15.6.30.16.28.9.8.32.33.34&pnum=%s' % str(self.page)
		elif self.ID == "home":
			url = 'http://www.eroprofile.com/m/videos/search?niche=13.14.12.19.27.25.5.11.18.20.23.24.10.26.17.7.15.6.30.16.28.9.8.32.33.34&pnum=%s' % str(self.page)
		elif self.ID == "":
			url = 'http://www.eroprofile.com/m/videos/search?niche=13.14.12.19.27.25.5.11.18.20.23.24.10.26.17.7.15.6.30.16.28.9.8.32.33.34&text=%s&pnum=%s' % (self.SearchString, str(self.page))
		else:
			url = 'http://www.eroprofile.com/m/videos/search?niche=%s&pnum=%s' % (self.ID, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'id="divVideoListPageNav">(.*?)</div>','.*pnum=(\d+)')
		Movies = re.findall('class="video">.*?<a\shref="(.*?)"(?:\sclass="videoLnk exopu"|)><img\ssrc="(.*?)".*?class="videoDur">(.*?)</div>.*?(?:class="videoTtl">|class="videoTtl"\stitle=")(.*?)(?:</div|")', data, re.S)
		if Movies:
			for (Url, Image, Runtime, Title) in Movies:
				if Image.startswith('//'):
					Image = "http:" + Image
				Url = "http://www.eroprofile.com" + Url
				self.filmliste.append((decodeHtml(Title), Url, Image.replace('amp;',''), Runtime))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), None, '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s" % (runtime))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if url:
			self.keyLocked = True
			getPage(url).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('source src="(.*?)"', data, re.S)
		if videoPage:
			url = videoPage[0].replace('&amp;','&')
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='eroprofile')