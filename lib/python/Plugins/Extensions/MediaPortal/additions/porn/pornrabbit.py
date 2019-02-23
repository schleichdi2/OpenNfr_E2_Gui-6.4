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
from Plugins.Extensions.MediaPortal.resources.aes_crypt import aes_decrypt_text

default_cover = "file://%s/pornrabbit.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class pornrabbitGenreScreen(MPScreen):

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

		self['title'] = Label("PornRabbit.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.pornrabbit.com/page/categories/"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('class="cat">.*?<a\shref="(.*?)".*?<h2>(.*?)<small>.*?(\d+,?\d+).*?<img\ssrc="(.*?)"', data, re.S)
		if Cats:
			for (Url, Title, Count, Image) in Cats:
				Image = "http://www.pornrabbit.com" + Image
				self.genreliste.append((Title, Url, Image, Count.replace(',','')))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Most Recent", "/videos/", default_cover, None))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover, None))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
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
			count = self['liste'].getCurrent()[0][3]
			self.session.open(pornrabbitFilmScreen, Link, Name, count)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = urllib.quote(callback).replace(' ', '%20')
			Name = "--- Search ---"
			Link = '/search/%s/' % (self.suchString)
			count = None
			self.session.open(pornrabbitFilmScreen, Link, Name, count)

class pornrabbitFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Count=None):
		self.Link = Link
		self.Name = Name
		self.Count = Count
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

		self['title'] = Label("PornRabbit.com")
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
		url = "http://www.pornrabbit.com%s%s/" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if self.Count:
			self.lastpage = int(round((float(self.Count) / 33) + 0.5))
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self.lastpage = 999
			self['page'].setText(str(self.page))
		Movies = re.findall('class="video">.*?<a href="(.*?)" title="(.*?)".*?<img.*?src="(.*?)".*?views: <b>(.*?)</b>.*?runtime: <b>(.*?)</b>', data, re.S)
		if Movies:
			for (Url, Title, Image, Views, Runtime) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
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
		if not Link == None:
			url = 'http://www.pornrabbit.com%s' % Link
			self.keyLocked = True
			getPage(url).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		self.keyLocked = False
		videoPage = re.findall('jwplayer.*?file: \'(.*?)\'', data, re.S)
		if videoPage:
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, videoPage[0])], showPlaylist=False, ltype='pornrabbit')
			return
		else:
			videoPage = re.findall('videoplay.*?src=["|\'](.*?)["|\']', data, re.S)
			if videoPage:
				if re.search('//xhamster.com/', videoPage[0]):
					self.keyLocked = True
					getPage(videoPage[0]).addCallback(self.getxhamsterLink).addErrback(self.errWorker).addErrback(self.dataError)
					return
				elif re.search('//www.youporn.com/', videoPage[0]):
					self.keyLocked = True
					getPage(videoPage[0], headers={'Cookie': 'age_verified=1', 'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.getyoupornLink).addErrback(self.errWorker).addErrback(self.dataError)
					return
		message = self.session.open(MessageBoxExt, _("No supported streams found!"), MessageBoxExt.TYPE_INFO, timeout=3)

	def errWorker(self, error):
		self.keyLocked = False
		message = self.session.open(MessageBoxExt, _("No link found!"), MessageBoxExt.TYPE_INFO, timeout=3)
		myerror = error.getErrorMessage()
		if myerror:
			raise error

	def getxhamsterLink(self, data):
		self.keyLocked = False
		videoPage = re.findall('videoUrls.*?(http.*?)%22', data)
		if videoPage:
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, urllib.unquote(videoPage[0]).replace('\/', '/'))], showPlaylist=False, ltype='pornrabbit')
		else:
			message = self.session.open(MessageBoxExt, _("No link found!"), MessageBoxExt.TYPE_INFO, timeout=3)

	def getyoupornLink(self, data):
		self.keyLocked = False
		videoPage = re.findall('video_url\':\s\'(.*?)\'', data)
		if videoPage:
			Title = self['liste'].getCurrent()[0][0]
			videoLink = aes_decrypt_text(videoPage[0], Title, 32)
			self.session.open(SimplePlayer, [(Title, videoLink)], showPlaylist=False, ltype='pornrabbit')
		else:
			message = self.session.open(MessageBoxExt, _("No link found!"), MessageBoxExt.TYPE_INFO, timeout=3)