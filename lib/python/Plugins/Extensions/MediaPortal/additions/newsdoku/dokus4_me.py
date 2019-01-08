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
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

default_cover = "file://%s/dokus4_me.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class show_D4ME_Genre(MenuHelper):

	def __init__(self, session):
		MenuHelper.__init__(self, session, 1, [[("Suche", "/?s=%s&x=0&y=0"),("Neueste Dokus", "")],[None,None]], "http://www.dokus4.me", "/index.php", self._defaultlistcenter, default_cover=default_cover)

		self['title'] = Label("dokus4.me")
		self['ContentTitle'] = Label("Genres")

		self.param_qr = ''

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_parseData(self, data):
		entrys = re.findall('<li class="cat-item.*?href="http://www.dokus4.me/index.php(.*?)/".*?>(.*?)</a>', data)
		return entrys

	def mh_callGenreListScreen(self):
		if re.search('Suche', self.mh_genreTitle):
			self.paraQuery()
		else:
			genreurl = self.mh_baseUrl+self.mh_genreBase+self.mh_genreUrl[0]+self.mh_genreUrl[1]
			self.session.open(D4ME_FilmListeScreen, genreurl, self.mh_genreTitle)

	def paraQuery(self):
		self.param_qr = ''
		self.session.openWithCallback(self.cb_paraQuery, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_qr, is_dialog=True)

	def cb_paraQuery(self, callback = None, entry = None):
		if callback != None:
			self.param_qr = callback.strip()
			if len(self.param_qr) > 0:
				qr = self.param_qr.replace(' ','+')
				genreurl = self.mh_baseUrl + self.mh_genreUrl[0] % qr
				self.session.open(D4ME_FilmListeScreen, genreurl, self.mh_genreTitle)

class D4ME_FilmListeScreen(MPScreen, ThumbsHelper):

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
		self.baseUrl = "http://www.dokus4.me"
		self.genreTitle = ""
		self.sortParIMDB = ""
		self.sortParAZ = ""
		self.sortOrderStrAZ = ""
		self.sortOrderStrIMDB = ""
		self.sortOrderStrGenre = ""
		self['title'] = Label("dokus4.me")

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
		self.pages = 0;

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
			self['page'].setText("%d / %d" % (self.page,self.pages))
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
		dokus = re.findall('<div class="tbl_titel"><a href="(.*?)" title="(.*?)".*?<img src="(.*?)".*?class="vid_desc">(.*?)</td>', data, re.S)
		if dokus:
			if not self.pages:
				m = re.search("class='pages'>Seite 1 von (\d+)<", data)
				try:
					pages = int(m.group(1))
				except:
					pages = 1
				if pages > self.pages:
					self.pages = pages
			if not self.page:
				self.page = 1
			self['page'].setText("%d / %d" % (self.page,self.pages))
			for	(url,name,img,desc) in dokus:
				self.dokusListe.append((decodeHtml(name), url, img, decodeHtml(desc.strip())))
			self.ml.setList(map(self._defaultlistleft, self.dokusListe))
			self.th_ThumbsQuery(self.dokusListe, 0, 1, 2, None, None, self.page, self.pages, mode=1)
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

	def parseStream(self, data):
		m2 = re.search('//www.youtube.com/(embed|v)/(.*?)(\?|" |&amp)', data)
		if m2:
			dhVideoId = m2.group(2)
			dhTitle = self['liste'].getCurrent()[0][0]
			self.session.open(
				YoutubePlayer,
				[(dhTitle, dhVideoId, None)],
				showPlaylist=False
				)
		else:
			self.session.open(MessageBoxExt,"Kein Stream gefunden!", MessageBoxExt.TYPE_INFO, timeout=10)

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		streamLink = self['liste'].getCurrent()[0][1]
		twAgentGetPage(streamLink).addCallback(self.parseStream).addErrback(self.dataError)

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