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

default_cover = "file://%s/tubewolf.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class tubewolfGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		global default_cover
		if self.mode == "tubewolf":
			self.portal = "TubeWolf.com"
			self.baseurl = "https://www.tubewolf.com"
			default_cover = "file://%s/tubewolf.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		elif self.mode == "alphaporno":
			self.portal = "AlphaPorno.com"
			self.baseurl = "https://www.alphaporno.com"
			default_cover = "file://%s/alphaporno.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		elif self.mode == "zedporn":
			self.portal = "ZedPorn.com"
			self.baseurl = "https://zedporn.com"
			default_cover = "file://%s/zedporn.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		elif self.mode == "crocotube":
			self.portal = "CrocoTube.com"
			self.baseurl = "https://crocotube.com"
			default_cover = "file://%s/crocotube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self['name'].setText(_('Please wait...'))
		url = self.baseurl
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('Categories<(.*?)class="(?:wrap|all|link_all_cat)"', data, re.S)
		cat = re.findall('a\shref="(.*?)"\stitle="(.*?)"', parse.group(1), re.S)
		if cat:
			for (Url, Title) in cat:
				self.filmliste.append((decodeHtml(Title), Url))
			self.filmliste.sort()
			self.filmliste.insert(0, ("Top Rated", "%s/top-rated" % self.baseurl, default_cover))
			self.filmliste.insert(0, ("Most Popular", "%s/most-popular" % self.baseurl, default_cover))
			self.filmliste.insert(0, ("Newest", "%s/latest-updates" % self.baseurl, default_cover))
			self.filmliste.insert(0, ("--- Search ---", "callSuchen", default_cover))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.keyLocked = False
		self['name'].setText('')

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = callback.replace(' ', '+')
			self.session.open(tubewolfListScreen, Link, Name, self.portal, self.baseurl)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(tubewolfListScreen, Link, Name, self.portal, self.baseurl)

class tubewolfListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal, baseurl):
		self.Link = Link
		self.Name = Name
		self.portal = portal
		self.baseurl = baseurl

		global default_cover
		if self.portal == "TubeWolf.com":
			default_cover = "file://%s/tubewolf.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		elif self.portal == "AlphaPorno.com":
			default_cover = "file://%s/alphaporno.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		elif self.portal == "ZedPorn.com":
			default_cover = "file://%s/zedporn.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		elif self.portal == "CrocoTube.com":
			default_cover = "file://%s/crocotube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.page = 1
		self.lastpage = 1
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "%s/search/%s/?q=%s" % (self.baseurl, self.page, self.Link)
		else:
			url = self.Link + "/" + str(self.page) + "/"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		self.getLastPage(data, '"pagination(?:-list|)"(.*?)</ul>')
		movies = re.findall('class="(?:video-|)thumb".*?href="(%s.*?)".*?class="(?:th|img-shadow|pic)".*?src="(.*?)"\salt="(.*?)".*?duration">(.*?)</span>(.*?(?:</li>|</em></p>|content="[0-9\-]+">))' % self.baseurl, data, re.S)
		if movies:
			for (Url, Image, Title, Duration, Added) in movies:
				Date = re.search('"datePublished" content="(.*?)"', Added)
				if Date:
					Added = Date.group(1)
				else:
					Date = re.search('<p><span>(.*?)</span>', Added)
					if Date:
						Added = Date.group(1)
					else:
						Added = ''
				if Image.startswith('//'):
					Image = "https:" + Image
				self.filmliste.append((decodeHtml(Title), Url, Image, Duration, Added))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), None, None, '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		runtime = self['liste'].getCurrent()[0][3]
		added = self['liste'].getCurrent()[0][4]
		if added != "":
			added = "\nAdded: %s" % added
		else:
			added = ""
		self['handlung'].setText("Runtime: %s%s" % (runtime, added))
		self['name'].setText(Title)
		coverUrl = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link).addCallback(self.getStreamData).addErrback(self.dataError)

	def getStreamData(self, data):
		title = self['liste'].getCurrent()[0][0]
		raw = re.findall('source src="(.*?)"', data, re.S)
		if raw:
			self.session.open(SimplePlayer, [(title, raw[-1])], showPlaylist=False, ltype='tubewolf')