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
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.additions.mediatheken.youtube import YT_ListScreen
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

default_cover = "file://%s/videogold_de.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class show_VGDE_Genre(MenuHelper):

	def __init__(self, session):
		baseUrl = "https://videogold.de"
		MenuHelper.__init__(self, session, 0, None, baseUrl, "", self._defaultlistcenter, default_cover=default_cover)

		self['title'] = Label("VideoGold.de")
		self['ContentTitle'] = Label("Genres")

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_parseCategorys(self, data):
		themes = ['Nach Format','Nach Thema']
		menu_marker = 'class="menu"'
		excludes = ['/livestreams','/videos-eintragen','/wp-login']
		menu=self.scanMenu(data,menu_marker,themes=themes,base_url=self.mh_baseUrl,url_ex=excludes)
		self.mh_genMenu2(menu)

	def mh_callGenreListScreen(self):
		genreurl = self.mh_genreUrl[self.mh_menuLevel].replace('&#038;','&')
		if not genreurl.startswith('https'):
			genreurl = self.mh_baseUrl+genreurl
		self.session.open(VGDE_FilmListeScreen, genreurl, self.mh_genreTitle)

class VGDE_FilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"0" : self.closeAll
		}, -1)

		self['title'] = Label("VideoGold.de")
		self['ContentTitle'] = Label(genreName)
		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.dokusListe = []
		self.page = 1
		self.lastpage = 1

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)
		if '/?' in self.genreLink:
			self.genreLink = self.genreLink.replace('/?', '/seite/%d/?', 1)
		else:
			self.genreLink += "/seite/%d/"

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		self.dokusListe = []
		self.ml.setList(map(self._defaultlistleft, self.dokusListe))
		url = self.genreLink % max(self.page,1)
		twAgentGetPage(url, timeout=60).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		for m in re.finditer('<article id=(.*?)</article>', data, re.S):
			m2 = re.search('<a href="(.*?)" title="(.*?)">.*?data-lazy-src="(.*?)".*?<p>(.*?)</p>', m.group(1), re.S)
			if m2:
				url, nm, img, desc = m2.groups()
				self.dokusListe.append((decodeHtml(nm), url, img, decodeHtml(desc)))
		if self.dokusListe:
			self.getLastPage(data, "class='wp-pagenavi'(.*?)</div>")

			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			self.th_ThumbsQuery(self.dokusListe,0,1,2,None,None, self.page, self.lastpage, mode=1)
			self.showInfos()
		else:
			self.dokusListe.append((_("No dokus found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		desc = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(desc)
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def parseYTStream(self, data):
		m2 = re.search('//www.youtube.*?com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		url = None
		if m2:
			dhVideoId = m2.group(2)
			if 'p' == m2.group(1):
				url = 'gdata.youtube.com/feeds/api/playlists/PL'+dhVideoId+'?'
		else:
			m2 = re.search('//youtu.be/(.*?)"', data)
			if m2:
				dhVideoId = m2.group(1)
		if m2:
			dhTitle = self['liste'].getCurrent()[0][0]
			if url:
				url = 'gdata.youtube.com/feeds/api/playlists/PL'+dhVideoId+'?'
				self.session.open(YT_ListScreen, url, dhTitle, title="videogold")
			else:
				self.session.open(YoutubePlayer, [(dhTitle, dhVideoId, None)], showPlaylist=False)

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		streamLink = self['liste'].getCurrent()[0][1]
		twAgentGetPage(streamLink, timeout=60).addCallback(self.parseYTStream).addErrback(self.dataError)