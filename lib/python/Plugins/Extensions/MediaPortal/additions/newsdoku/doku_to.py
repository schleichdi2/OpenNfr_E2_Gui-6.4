# -*- coding: utf-8 -*-
#
#    Copyright (c) 2016 Billy2011, MediaPortal Team
#
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.additions.mediatheken.youtube import YT_ListScreen
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

default_cover = "file://%s/doku_to.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class show_DUTO_Genre(MenuHelper):

	def __init__(self, session):

		baseUrl = "http://doku.to"
		MenuHelper.__init__(self, session, 0, None, baseUrl, "", self._defaultlistcenter, default_cover=default_cover)

		self['title'] = Label("DOKU.to")
		self['ContentTitle'] = Label("Genres")

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_parseCategorys(self, data):
		menu = [
			(0, "/", "Letzte Beiträge"),
			(0, "/", "Kategorien"),
			]
		menu_marker = '">Kategorien</h3'
		menu += self.scanMenu(data,menu_marker, base_url=self.mh_baseUrl, init_level=0)
		m = re.search('="widget-title">Schlagwörter<(.*?)</div>', data, re.S)
		if m:
			menu.append((0, "", "Schlagwörter"))
			for m2 in re.finditer('<a\shref="(.*?)\/"\sclass="tag-cloud-link.*?">(.*?)</a>', m.group(1)):
				url, nm = m2.groups()
				menu.append((1, url, decodeHtml(nm)))
		self.mh_genMenu2(menu)
		del menu[:]

	def mh_callGenreListScreen(self):
		genreurl = self.mh_genreUrl[self.mh_menuLevel].replace('&#038;','&')
		if not genreurl.startswith('http'):
			genreurl = self.mh_baseUrl+genreurl
		self.session.open(DUTO_FilmListeScreen, genreurl, self.mh_genreTitle)

class DUTO_FilmListeScreen(MPScreen, ThumbsHelper):

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
			"1" : self.key_1,
			"3" : self.key_3,
			"4" : self.key_4,
			"6" : self.key_6,
			"7" : self.key_7,
			"9" : self.key_9,
			"0" : self.closeAll
		}, -1)

		self.sortOrder = 0
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label("DOKU.to")

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
		self.pages = 0
		self.pageplus = ''

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		if self.page > 1:
			if '/?' in self.genreLink:
				url = self.genreLink.replace('/?', '/page/%d/?', 1)
			else:
				url = self.genreLink + "/page/%d/"
			url = url % self.page
		else:
			url = self.genreLink

		if self.page:
			self['page'].setText("%d / %d%s" % (self.page,self.pages,self.pageplus))

		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()

	def loadPageQueued(self):
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		twAgentGetPage(url, timeout=30).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		printl(error,self,"E")
		if not 'TimeoutError' in str(error):
			message = self.session.open(MessageBoxExt, _("No dokus / streams found!"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			message = self.session.open(MessageBoxExt, str(error), MessageBoxExt.TYPE_INFO)

	def loadPageData(self, data):
		self.dokusListe = []
		for m in re.finditer('<article id=(.*?)</article>', data, re.S):
			if re.search('Status:.*?alt="Offline"', m.group(1)): continue
			m2 = re.search('="entry-thumb">.*?href="(.*?)"\stitle="(.*?)".*?<img.*?src="(.*?)".*?<p>\s*(.*?)\s*</p>', m.group(1), re.S)
			if m2:
				url, nm, img, desc = m2.groups()
				self.dokusListe.append((decodeHtml(nm), url, img, decodeHtml(desc)))

		self.pageplus = '+' if re.search('class="fa fa-long-arrow-left"></i>&nbsp;<a href="', data) != None and self.page >= self.pages else ''
		if self.dokusListe:
			if not self.page:
				self.page = 1
			if self.page > self.pages: self.pages = self.page
			self['page'].setText("%d / %d%s" % (self.page,self.pages,self.pageplus))

			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self['liste'].moveToIndex(0)
			self.th_ThumbsQuery(self.dokusListe,0,1,2,None,None, self.page, self.pages)
			self.loadPicQueued()
		else:
			if self.page:
				self['page'].setText("%d / %d%s" % (self.page,self.pages,self.pageplus))
			self.dokusListe.append((_("No playable dokus found!"),"","",""))
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

	def getHandlung(self, desc):
		if desc == None:
			self['handlung'].setText(_("No further information available!"))
			return
		self.setHandlung(desc)

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
		self.getHandlung(desc)
		self.loadPic()

	def parseYTStream(self, data):
		m2 = re.search('//www.youtube.*?com/(embed|v|p)/(.*?)(\?|" |&amp)', data)
		url = None
		if m2:
			dhVideoId = m2.group(2)
			if 'p' == m2.group(1):
				url = 'gdata.youtube.com/feeds/api/playlists/PL'+dhVideoId+'?'
		else:
			m2 = re.search('youtu.*?/(.*?)</p>', data)
			if not m2:
				m2 = re.search('//youtu.be/(.*?)"', data)
			if m2:
				dhVideoId = m2.group(1)
		if m2:
			dhTitle = self['liste'].getCurrent()[0][0]
			if url:
				url = 'gdata.youtube.com/feeds/api/playlists/PL'+dhVideoId+'?'
				self.session.open(YT_ListScreen, url, dhTitle, title="DOKU.to")
			else:
				self.session.open(
					YoutubePlayer,
					[(dhTitle, dhVideoId, None)],
					showPlaylist=False
					)
		else:
			self.dataError(_('No streamlink found.'))

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		streamLink = self['liste'].getCurrent()[0][1]
		twAgentGetPage(streamLink, timeout=30).addCallback(self.parseYTStream).addErrback(self.dataError)

	def keyUpRepeated(self):
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		if self.keyLocked:
			return
		self.loadPicQueued()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyPageDown(self):
		self.keyPageDownFast(1)

	def keyPageUp(self):
		self.keyPageUpFast(1)

	def keyPageUpFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page + step) <= self.pages:
			self.page += step
		elif self.pageplus:
			self.page += 1
			self.pages += 1
			self.pageplus = ''
		else:
			self.page = 1
		if oldpage != self.page:
			self.loadPage()

	def keyPageDownFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page - step) >= 1:
			self.page -= step
		else:
			self.page = self.pages
		if oldpage != self.page:
			self.loadPage()

	def key_1(self):
		self.keyPageDownFast(2)

	def key_4(self):
		self.keyPageDownFast(5)

	def key_7(self):
		self.keyPageDownFast(10)

	def key_3(self):
		self.keyPageUpFast(2)

	def key_6(self):
		self.keyPageUpFast(5)

	def key_9(self):
		self.keyPageUpFast(10)