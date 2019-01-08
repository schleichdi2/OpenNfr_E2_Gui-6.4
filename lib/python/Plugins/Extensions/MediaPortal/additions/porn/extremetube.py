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

agent='Mozilla/5.0 (Windows NT 6.1; rv:44.0) Gecko/20100101 Firefox/44.0'
headers = {
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	}
default_cover = "file://%s/extremetube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class extremetubeGenreScreen(MPScreen):

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

		self['title'] = Label("ExtremeTube.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.extremetube.com/video-categories"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="title-general">\s{0,1}Categories</h1>(.*?)footer', data, re.S)
		Cats = re.findall('href="(.*?)".*?img"\ssrc="(.*?)".*?title="(.*?)"', parse.group(1), re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				if Title != "High Definition Videos":
					Url = "http://www.extremetube.com" + Url.replace('?fromPage=categories', '') + '?page='
					if Image.startswith('//'):
						Image = 'http:' + Image
					self.genreliste.append((Title, Url, Image))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Longest", "http://www.extremetube.com/videos?o=lg", default_cover))
			self.genreliste.insert(0, ("Highest Rated", "http://www.extremetube.com/videos?o=tr", default_cover))
			self.genreliste.insert(0, ("Most Popular", "http://www.extremetube.com/videos?o=mv", default_cover))
			self.genreliste.insert(0, ("Being Watched", "http://www.extremetube.com/videos?o=bw", default_cover))
			self.genreliste.insert(0, ("Recently Added", "http://www.extremetube.com/videos?o=mr", default_cover))
			self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover))
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
			self.suchen(suggest_func=self.getSuggestions)
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(extremetubeFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = self['liste'].getCurrent()[0][0]
			self.suchString = callback
			Link = 'http://www.extremetube.com/videos?search=%s' % self.suchString.replace(' ', '+')
			self.session.open(extremetubeFilmScreen, Link, Name)

	def getSuggestions(self, text, max_res):
		url = "http://www.pornmd.com/autosuggest?key=%s" % urllib.quote_plus(text)
		d = twAgentGetPage(url, agent=agent, headers=headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, err=True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions:
				li = item
				list.append(str(li))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class extremetubeFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("ExtremeTube.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

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
		if re.match('.*?\?', self.Link):
			delimiter = '&'
		else:
			delimiter = '?'
		url = "%s%sformat=json&page=%s" % (self.Link, delimiter, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		json_data = json.loads(data)
		if json_data["1"]["navigation"].has_key('lastPage'):
			self.lastpage = json_data["1"]["navigation"]["lastPage"]
		if self.lastpage > 1:
			self['Page'].setText(_("Page:"))
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		for node in json_data["1"]["items"]:
			Views = str(node["real_times_viewed"]).replace(',','')
			Title = str(node["specialchars_title"])
			Runtime = str(node["duration"])
			Url = str(node["video_link"])
			Image = str(node["thumb_url"])
			if Url.startswith('//'):
				Url = 'http:' + Url
			if Image.startswith('//'):
				Image = 'http:' + Image
			self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), None, None, '', ''))
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
		self['handlung'].setText("Runtime: %s\nViews: %s" % (runtime, views))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link:
			self.keyLocked = True
			getPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('"quality_\d+p":"(.*?)","', data, re.S)
		if videoPage:
			url = videoPage[-1]
			url = url.replace('\/','/')
			if url.startswith('//'):
				url = "https:" + url
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, url.replace('%2F','%252F').replace('%3D','%253D').replace('%2B','%252B'))], showPlaylist=False, ltype='extremetube')