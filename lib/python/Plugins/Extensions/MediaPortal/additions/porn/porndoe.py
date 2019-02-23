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
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
default_cover = "file://%s/porndoe.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

ck = {}

class porndoeGenreScreen(MPScreen):

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

		self['title'] = Label("Porndoe.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		ck.update({'__language':'en'})
		url = "https://www.porndoe.com/categories"
		getPage(url, agent=agent, cookies=ck).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('class="item">.*?href="(.*?)".*?data-src="(.*?)".*?class="txt">(.*?)(?:</span|<span)', data, re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				Url = "https://www.porndoe.com" + Url
				if Image.startswith('//'):
					Image = 'https:' + Image
				self.genreliste.append((Title.replace('&amp;','&').strip(), Url, Image, True))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Longest", "https://www.porndoe.com/videos?sort=duration-down", default_cover, False))
			self.genreliste.insert(0, ("Most Viewed", "https://www.porndoe.com/videos?sort=views-down", default_cover, False))
			self.genreliste.insert(0, ("Top Rated", "https://www.porndoe.com/videos?sort=likes-down", default_cover, False))
			self.genreliste.insert(0, ("Newest", "https://www.porndoe.com/videos", default_cover, False))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover, False))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image, agent=agent, headers={'Referer':'https://www.porndoe.com'})

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			Sort = self['liste'].getCurrent()[0][3]
			self.session.open(porndoeFilmScreen, Link, Name, Sort)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = urllib.quote(self.suchString).replace(' ', '+')
			self.session.open(porndoeFilmScreen, Link, Name, False)

class porndoeFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, Sort):
		self.Link = Link
		self.Name = Name
		self.Sort = Sort
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
			"green" : self.keyPageNumber,
			"yellow" : self.keySort
		}, -1)

		self['title'] = Label("Porndoe.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		if self.Sort:
			self['F3'] = Label(_("Sort"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		if not self.Sort:
			self.sort = ''
			self.sorttext = ''
		else:
			self.sort = ''
			self.sorttext = 'Date'

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = 'https://www.porndoe.com/search?keywords=%s&page=%s' % (self.Link, str(self.page))
		else:
			if '?' in self.Link or '?' in self.sort:
				delim = '&'
			else:
				delim = '?'
			url = "%s%s%spage=%s" % (self.Link, self.sort, delim, str(self.page))
		getPage(url, agent=agent, cookies=ck).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="paginator"(.*?)</ul>', '.*(?:page=|<span>)(\d+)(?:"|</span>)')
		Movies = re.findall('data-title="(.*?)".*?href="(.*?)".*?data-src="(.*?)".*?class="item-stat right duration".*?txt">(.*?)</span.*?class="item-stat views".*?txt">(.*?)</span', data, re.S)
		if Movies:
			for (Title, Url, Image, Runtime, Views) in Movies:
				Url = "https://www.porndoe.com" + Url
				if Image.startswith('//'):
					Image = 'http:' + Image
				Runtime = Runtime.strip()
				Views = Views.strip()
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		self['handlung'].setText("%s: %s\nRuntime: %s\nViews: %s" % (_("Sort order"),self.sorttext,runtime, views))
		CoverHelper(self['coverArt']).getCover(pic, agent=agent, headers={'Referer':'https://www.porndoe.com'})

	def keySort(self):
		if self.keyLocked:
			return
		if not self.Sort:
			return
		rangelist = [['Date', ''], ['Views','?sort=views-down'], ['Likes','?sort=likes-down'], ['Duration','?sort=duration-down']]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sorttext = result[0]
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link, agent=agent, cookies=ck).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('<source.*?src="(.*?)".*?type="video/mp4".*?label="(\d+)', data, re.S)
		if videoPage:
			url = videoPage[0][0]
			if url.startswith('//'):
				url = 'http:' + url
			url = url.replace('%2F','%252F').replace('%3D','%253D').replace('%2B','%252B')
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			headers = '&Referer=' + self['liste'].getCurrent()[0][1]
			url = url + '#User-Agent='+agent+headers
			mp_globals.player_agent = agent
			self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='porndoe')