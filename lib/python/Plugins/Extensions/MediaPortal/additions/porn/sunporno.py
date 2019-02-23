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

spAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
json_headers = {
	'Accept':'application/json',
	'Accept-Language':'en,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/x-www-form-urlencoded',
	}
default_cover = "file://%s/sunporno.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class sunpornoGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("SunPorno.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		url = "https://www.sunporno.com/channels/"
		getPage(url, agent=spAgent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="cat-container(.*?)class="clearfix">', data, re.S)
		Cats = re.findall('<a\shref="https://www.sunporno.com/channels/(\d+).*?">(.*?)<', parse.group(1), re.S)
		if Cats:
			for (Id, Title) in Cats:
				Url = "https://www.sunporno.com/?area=ajaxMovieListViewer&nicheId=%s&dateAddedType=5&lengthType=0-50&orderBy=id&pageId=" % Id
				Title = Title.strip()
				self.genreliste.append((Title, Url))
			self.genreliste.sort()
		self.genreliste.insert(0, ("High Definition", "https://www.sunporno.com/?area=ajaxMovieListViewer&dateAddedType=5&lengthType=0-50&orderBy=hd&pageId="))
		self.genreliste.insert(0, ("Longest", "https://www.sunporno.com/?area=ajaxMovieListViewer&dateAddedType=5&lengthType=0-50&orderBy=longest&pageId="))
		self.genreliste.insert(0, ("Most Favorited", "https://www.sunporno.com/?area=ajaxMovieListViewer&dateAddedType=5&lengthType=0-50&orderBy=favorited&pageId="))
		self.genreliste.insert(0, ("Most Viewed", "https://www.sunporno.com/?area=ajaxMovieListViewer&dateAddedType=5&lengthType=0-50&orderBy=viewCount&pageId="))
		self.genreliste.insert(0, ("Top Rated", "https://www.sunporno.com/?area=ajaxMovieListViewer&dateAddedType=5&lengthType=0-50&orderBy=rating&pageId="))
		self.genreliste.insert(0, ("Newest", "https://www.sunporno.com/?area=ajaxMovieListViewer&dateAddedType=5&lengthType=0-50&orderBy=id&pageId="))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self['name'].setText('')

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen(suggest_func=self.getSuggestions)
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(sunpornoFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = '%s' % (urllib.quote(self.suchString).replace(' ', '+'))
			self.session.open(sunpornoFilmScreen, Link, Name)

	def getSuggestions(self, text, max_res):
		url = "https://www.sunporno.com/?area=autocomplete&o=straight&q=%s" % urllib.quote_plus(text)
		d = twAgentGetPage(url, agent=spAgent, headers=json_headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, err=True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions['suggestions']:
				li = re.sub('\s+', ' ', item).strip()
				list.append(str(li))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class sunpornoFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("SunPorno.com")
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
			url = "https://www.sunporno.com/?area=ajaxMovieListViewer&q=%s&dateAddedType=5&lengthType=0-50&orderBy=relevance&pageId=%s" % (self.Link, str(self.page))
		else:
			url = "%s%s" % (self.Link, str(self.page))
		getPage(url, agent=spAgent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', '"maxPage":(\d+),"')
		res = json.loads(data)
		for node in res["list"]:
			Title = str(node["name"])
			Url = "https://www.sunporno.com/videos/%s/" % str(node["id"])
			Image = str(node["thumb"])
			Rating = str(node["rating"]) + "%"
			Runtime = str(node["duration"])
			Added = str(node["ago"])
			self.filmliste.append((Title, Url, Image, Runtime, Rating, Added))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, '', '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		rating = self['liste'].getCurrent()[0][4]
		added = self['liste'].getCurrent()[0][5]
		self['handlung'].setText("Runtime: %s\nAdded: %s\nRating: %s" % (runtime, added, rating))
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link, agent=spAgent).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		parse = re.findall('itemprop="name">(.*?)</span>', data, re.S|re.I)
		title = decodeHtml(parse[0])
		if parse:
			title = decodeHtml(parse[0])
		else:
			title = self['liste'].getCurrent()[0][0]
		video = re.findall('video\ssrc="(.*?)"', data, re.S)
		if video:
			url = video[0].replace('https','http')
			self.keyLocked = False
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='sunporno')