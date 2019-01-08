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
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubelink import YoutubeLink
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

default_cover = "file://%s/lachschon_de.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class show_LSDE_Genre(MenuHelper):

	def __init__(self, session):

		baseUrl = "http://www.lachschon.de"
		MenuHelper.__init__(self, session, 0, None, baseUrl, "", self._defaultlistcenter, default_cover=default_cover)

		self['title'] = Label("LACHSCHON.DE")
		self['ContentTitle'] = Label("Genres")
		self.suchString = ''

		self.onLayoutFinish.append(self.parseCats)

	def parseCats(self):
		self.mh_parseCategorys(None)

	def mh_parseCategorys(self, data):
		menu = []
		menu.append((0, '', 'Kategorien'))
		menu.append((1, '/gallery/trend/?', 'Trend'))
		menu.append((1, '/gallery/new/?', 'Neue'))
		menu.append((1, '/gallery/all/?', 'Alles'))
		menu.append((1, '/gallery/toprecent/?', 'Top'))
		menu.append((1, '/gallery/floprecent/?', 'Flop'))
		menu.append((0, '', 'Top & Flop'))
		menu.append((1, '/gallery/premium/?', 'Premium'))
		menu.append((1, '/gallery/trash/?', 'Müllhalde'))
		menu.append((1, '/gallery/top/?', 'Hall of Fame'))
		menu.append((1, '/gallery/flop/?', 'Hall of Shame'))
		menu.append((1, '/gallery/mostvoted/?', 'Stimmen'))
		menu.append((1, '/gallery/mostfavs/?', 'Favs'))
		menu.append((0, '/gallery/search_item/?q=%s&x=0&y=0&', 'Suche'))
		self.mh_genMenu2(menu)

	def mh_callGenreListScreen(self):
		if re.search('Suche', self.mh_genreTitle):
			self.suchen()
		else:
			genreurl = self.mh_baseUrl+self.mh_genreUrl[self.mh_menuLevel]+'set_gallery_type=video'
			self.session.open(LSDE_FilmListeScreen, genreurl, self.mh_genreTitle)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback
			qr = self.suchString.replace(' ','+')
			genreurl = self.mh_baseUrl+(self.mh_genreUrl[self.mh_menuLevel] % qr)+'set_gallery_type=video'
			self.session.open(LSDE_FilmListeScreen, genreurl, self.mh_genreTitle)

class LSDE_FilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName):
		self.genreLink = genreLink
		self.genreName = genreName
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions2", "MP_Actions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
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
			"0"	: self.closeAll
		}, -1)

		self.sortOrder = 0
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label("LACHSCHON.DE")

		self['Page'] = Label(_("Page:"))

		self.filmQ = Queue.Queue(0)
		self.hanQ = Queue.Queue(0)
		self.picQ = Queue.Queue(0)
		self.updateP = 0
		self.eventL = threading.Event()
		self.eventP = threading.Event()
		self.keyLocked = True
		self.dokusListe = []
		self.page = 0
		self.lastpage = 0

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		url = "%s&page=%d" % (self.genreLink, max(self.page,1))

		if self.page:
			self['page'].setText("%d / %d" % (self.page,self.lastpage))

		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()

	def loadPageQueued(self):
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		twAgentGetPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, content):
		m = re.search('="pageselection(.*?)</div>', content, re.S)
		self.dokusListe = []
		content = content[content.find('<ul id="itemlist">'):content.find('<p class="advert-notice">')]
		spl=content.split('<li>')
		for i in range(1,len(spl),1):
			entry=spl[i]
			match=re.compile('<a href="(.+?)"', re.S).findall(entry)
			if match:
				url=match[0]
			else:
				continue
			match=re.compile('class="previewitem".*?src="(.+?)"', re.S).findall(entry)
			if match:
				thumb=match[0]
				if thumb.startswith('//'):
					thumb = 'http:' + thumb
			else:
				thumb = None
			match=re.compile('<span class="rating">(.+?)</span>', re.S).findall(entry)
			rating=-1
			if match:
				rating=match[0]
			match=re.compile('class="title" href="(.+?)"(.+?)title="(.+?)">(.+?)\n', re.S).findall(entry)
			title=match[0][3]
			title=decodeHtml(title).strip()
			if rating!=-1:
				title=title+(" (%.1f / 10)" % float(rating))
			self.dokusListe.append((title, "http://www.lachschon.de"+url, thumb.replace('-medium',''), None))
		if self.dokusListe:
			if not self.lastpage:
				try:
					pgs = re.findall('"\?page=.*?">(\d+)</a', m.group(1), re.S)
					lastpage = int(pgs[-1])
				except:
					lastpage = 1

				if lastpage > self.lastpage:
					self.lastpage = lastpage
			if not self.page:
				self.page = 1
			self['page'].setText("%d / %d" % (self.page,self.lastpage))

			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			self.th_ThumbsQuery(self.dokusListe,0,1,2,None,None, self.page, self.lastpage, mode=1)
			self.loadPicQueued()
		else:
			self.dokusListe.append((_("No videos found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()

	def loadPic(self):
		if self.picQ.empty():
			self.eventP.clear()
			return

		if self.updateP:
			return

		while not self.picQ.empty():
			self.picQ.get_nowait()

		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		self.updateP = 1
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def setHandlung(self, data):
		self['handlung'].setText(data)

	def ShowCoverFileExit(self):
		self.updateP = 0;
		self.keyLocked	= False
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
			self.loadPic()

	def loadPicQueued(self):
		self.picQ.put(None)
		if not self.eventP.is_set():
			self.eventP.set()
		desc = self['liste'].getCurrent()[0][3]
		self.loadPic()

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		self.session.open(
			LSDEPlayer,
			self.dokusListe,
			playIdx = self['liste'].getSelectedIndex()
			)

class LSDEPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx):
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=True, listTitle="LACHSCHON.DE", ltype='lachschon.de')

	def getVideo(self):
		url = self.playList[self.playIdx][1]
		twAgentGetPage(url).addCallback(self.parseStream).addErrback(self.dataError)

	def parseStream(self, data):
		m2 = re.search('//www.youtube.*?com/(embed|v)/(.*?)(\?|" |&amp)', data)
		if m2:
			dhVideoId = m2.group(2)
			dhTitle = self.playList[self.playIdx][0]
			imgurl =  self.playList[self.playIdx][2]
			YoutubeLink(self.session).getLink(self.playStream, self.ytError, dhTitle, dhVideoId, imgurl=imgurl)
		else:
			self.dataError("Kein Videostream gefunden!")

	def ytError(self, error):
		msg = "Title: %s\n%s" % (self.playList[self.playIdx][0], error)
		self.dataError(msg)