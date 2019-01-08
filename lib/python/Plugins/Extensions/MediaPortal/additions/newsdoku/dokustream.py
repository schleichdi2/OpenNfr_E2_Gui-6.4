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
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

default_cover = "file://%s/dokustream.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class show_DS_Genre(MenuHelper):

	def __init__(self, session):

		baseUrl = "https://www.doku-stream.org"
		MenuHelper.__init__(self, session, 0, None, baseUrl, "", self._defaultlistcenter, default_cover=default_cover)

		self['title'] = Label("DokuStream")
		self['ContentTitle'] = Label("Genres")

		self.menu = []
		self.menu.append((0, '/', 'Neue Dokus'))
		self.menu.append((0, '/category/hd/', 'HD Dokus'))
		self.menu.append((0, '/tag/top/', 'Empfehlungen'))
		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_initMenu(self):
		self.mh_buildMenu(self.mh_baseUrl+'/kategorien/')

	def mh_parseCategorys(self, data, category='Kategorien'):
		if category == 'Kategorien':
			self.menu.append((0, '', 'Themen'))
			a = data.find('="entry"')
			if a > 0:
				b = data.find('</ul>', a)
				if b > 0:
					entrys = re.findall('href="(.*?)">(.*?)</a>', data[a:b])
					if entrys:
						for (u, n) in entrys:
							self.menu.append((1, u.replace(self.mh_baseUrl,''), n))

			self.getSerienPage()

		if category == 'Serien':
			self.menu.append((0, '', 'Serien'))
			a = data.find('="entry"')
			if a > 0:
				b = data.find('</ul>', a)
				if b > 0:
					entrys = re.findall('href="(.*?)">(.*?)</a>', data[a:b])
					if entrys:
						for (u, n) in entrys:
							self.menu.append((1, u.replace(self.mh_baseUrl,''), n))

			self.mh_genMenu2(self.menu)

	def mh_callGenreListScreen(self):
		genreurl = self.mh_baseUrl+self.mh_genreUrl[0]+self.mh_genreUrl[1]
		self.session.open(DS_FilmListeScreen, genreurl, self.mh_genreTitle)

	def getSerienPage(self):
		self.mh_lastPageUrl = self.mh_baseUrl+'/serien/'
		twAgentGetPage(self.mh_lastPageUrl, agent=None, headers=std_headers).addCallback(self.mh_parseCategorys, category='Serien').addErrback(self.mh_dataError)

class DS_FilmListeScreen(MPScreen, ThumbsHelper):

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
		self.baseUrl = "http://www.doku-stream.org"
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label("DokuStream")

		self['Page'] = Label(_("Page:"))

		self.filmQ = Queue.Queue(0)
		self.hanQ = Queue.Queue(0)
		self.picQ = Queue.Queue(0)
		self.updateP = 0
		self.eventL = threading.Event()
		self.eventP = threading.Event()
		self.keyLocked = True
		self.dokusListe = []
		self.keckse = CookieJar()
		self.page = 0
		self.lastpage = 0;

		self.setGenreStrTitle()

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		url = "%s/page/%d/" % (self.genreLink, self.page)
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
		twAgentGetPage(url, cookieJar=self.keckse, agent=None, headers=std_headers).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		printl(error,self,"E")
		self.dokusListe.append((_("No dokus found!"),"","",""))
		self.ml.setList(map(self._defaultlistleft, self.dokusListe))

	def loadPageData(self, data):
		self.dokusListe = []
		data = data.replace('\n', '')
		data = re.search('id="infinite-articles"(.*?)$', data, re.S).group(1)
		dokus = re.findall('<img.*?src="(.*?)".*?class="content-grid".*?href="(.*?)">.*?="entry-title">(.*?)</', data)
		if dokus:
			m = re.findall('class=\Dpage larger.*?>(\d+)<', data)
			try:
				lastpage = int(m[-1])
			except:
				lastpage = 1
			if lastpage > self.lastpage:
					self.lastpage = lastpage
			if not self.page:
				self.page = 1
			self['page'].setText("%d / %d" % (self.page,self.lastpage))
			for	(img,url,name) in dokus:
				self.dokusListe.append((decodeHtml(name), url, img))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self.ml.moveToIndex(0)
			self.th_ThumbsQuery(self.dokusListe, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.loadPicQueued()
		else:
			self.dokusListe.append((_("No dokus found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
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
		desc = None
		self.getHandlung(desc)
		self.updateP = 1
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def getHandlung(self, desc):
		if desc == None:
			self['handlung'].setText(_("No further information available!"))
			return
		self.setHandlung(desc)

	def setHandlung(self, data):
		self['handlung'].setText(decodeHtml(data))

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
		self.loadPic()

	def parseStream(self, data):
		m2 = re.search('//www.youtube.*?com/(embed|v)/(.*?)(\?|" |&amp)', data, re.S)
		if m2:
			dhVideoId = m2.group(2)
			dhTitle = self['liste'].getCurrent()[0][0]
			self.session.open(
				YoutubePlayer,
				[(dhTitle, dhVideoId, None)],
				showPlaylist=False
				)

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		streamLink = self['liste'].getCurrent()[0][1]
		twAgentGetPage(streamLink).addCallback(self.parseStream).addErrback(self.dataError)