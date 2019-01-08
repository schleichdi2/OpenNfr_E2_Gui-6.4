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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

myagent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0'

default_cover = "file://%s/moviefap.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class moviefapGenreScreen(MPScreen):

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

		self['title'] = Label("MovieFap.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		url = "http://www.moviefap.com/browse/"
		twAgentGetPage(url, agent=myagent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('Categories</h1></div>(.*?)</div', data, re.S)
		Cats = re.findall('<li>\s*<a\shref="(?:.*?empflix.com|.*?moviefap.com|)(.*?)(?:1.html|)".*?>(.*?)(?:<i>|</a></li>)', parse.group(1), re.S)
		if Cats:

			for (Url, Title) in Cats:
				if not Title == "All":
					Url = "http://www.moviefap.com" + Url + "mr/"
					self.genreliste.append((decodeHtml(Title), Url))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Being Watched", 'http://www.moviefap.com/browse/?category=bw&page='))
			self.genreliste.insert(0, ("Top Rated", 'http://www.moviefap.com/browse/?category=tr&page='))
			self.genreliste.insert(0, ("Most Recent", 'http://www.moviefap.com/browse/?category=mr&page='))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
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
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(moviefapFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Link = '%s' % (self.suchString)
			Name = "--- Search ---"
			self.session.open(moviefapFilmScreen, Link, Name)

class moviefapFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("MovieFap.com")
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
			url = "http://www.moviefap.com/search/%s/relevance/%s" % (self.Link, str(self.page))
		else:
			url = "%s%s" % (self.Link, str(self.page))
		twAgentGetPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</div>')
		Movies = re.findall('class="video.*?<a\s{1,2}href="(.*?)"\stitle="(.*?)".*?img\ssrc="(.*?)".*?videoleft">(.*?)<', data, re.S)
		if Movies:
			for (Url, Title, Image, Runtime) in Movies:
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, int(self.lastpage), mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		self['handlung'].setText("Runtime: %s" % (runtime))
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		twAgentGetPage(Link).addCallback(self.getXMLPage).addErrback(self.dataError)

	def getXMLPage(self, data):
		xml = re.findall('flashvars.config.*?//(.*?)"', data, re.S)
		if not xml:
			xml = re.findall('name="config".*?//(.*?)"', data, re.S)
		url = "http://" + xml[0]
		twAgentGetPage(url, timeout=30).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		url = re.findall('<videoLink>.*?//(.*?)(?:]]>|</videoLink>)', data, re.S)
		if url:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			url = "http://" + url[-1].replace('&amp;','&')
			self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='moviefap')