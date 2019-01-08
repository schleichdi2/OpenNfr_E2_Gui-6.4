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

agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'

default_cover = "file://%s/sexu.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class sexuGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("Sexu.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://sexu.com/"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="listTags">(.*?)</body>', data, re.S)
		Cats = re.findall('href="(.*?)".*?</i>(.*?)</a>', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://sexu.com" + Url + '/'
				self.genreliste.append((Title.title(), Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Trending", "http://sexu.com/trending/"))
			self.genreliste.insert(0, ("Hall of Fame", "http://sexu.com/all/"))
			self.genreliste.insert(0, ("Newest", "http://sexu.com/"))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(sexuFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			self.session.open(sexuFilmScreen, Link, Name)

class sexuFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("Sexu.com")
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
		if re.match(".*?Search", self.Name):
			url = "http://sexu.com/search?q=%s&page=%s" % (self.Link, str(self.page))
		else:
			url = "%s%s" % (self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</ul>', '.*[>|=|\/](\d+)[<|"]')
		parse = re.search('class="list-thumbs">(.*?)</html>', data, re.S)
		Movies = re.findall('class="thumb".*?href="(.*?)"\stitle="(.*?)".*?img\sclass.*?data-original="(.*?)".*?timeVideo">(.*?)</span', parse.group(1), re.S)
		if Movies:
			for (Url, Title, Image, Runtime) in Movies:
				Url = "http://sexu.com" + Url
				Title = Title.strip('.').replace("\\'","'")
				if Image.startswith('//'):
					Image = "http:" + Image
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), None, None))
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
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s" % runtime)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link == None:
			return
		getPage(Link).addCallback(self.getVideoData).addErrback(self.dataError)

	def getVideoData(self, data):
		stream_urls = re.findall('"src":"(.*?)","quality":"(\d+)p",', data)
		if stream_urls:
			res = 0
			for stream in stream_urls:
				if int(stream[1]) > res:
					link = stream[0]
					res = int(stream[1])
			title = self['liste'].getCurrent()[0][0]
			headers = '&Referer=http://sexu.com/'
			if link.startswith('//'):
				link = "http:" + link
			link = link + '#User-Agent='+agent+headers
			self.session.open(SimplePlayer, [(title, link)], showPlaylist=False, ltype='sexu')