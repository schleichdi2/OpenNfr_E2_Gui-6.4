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

agent='Mozilla/5.0 (Windows NT 6.1; rv:44.0) Gecko/20100101 Firefox/44.0'
headers = {
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	}
default_cover = "file://%s/eporner.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
	
class epornerGenreScreen(MPScreen):

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

		self['title'] = Label("Eporner.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.eporner.com/categories/"
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = re.findall('class="categoriesbox.*?"\sid=".*?">.*?<a\shref="(.*?)".*?title=".*?">.{0,1}<img\ssrc="(.*?)"\salt="(.*?)"', data, re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				Url = "http://www.eporner.com" + Url
				Title = Title.replace(' porn videos', '')
				self.genreliste.append((Title, Url, Image))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Longest", "https://www.eporner.com/%page/longest/", default_cover))
			self.genreliste.insert(0, ("Top Rated", "https://www.eporner.com/top-rated/", default_cover))
			self.genreliste.insert(0, ("Most Viewed", "https://www.eporner.com/%page/most_viewed/", default_cover))
			self.genreliste.insert(0, ("Most Recent", "http://www.eporner.com/", default_cover))
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
			streamGenreLink = self['liste'].getCurrent()[0][1]
			self.session.open(epornerFilmScreen, streamGenreLink, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = self['liste'].getCurrent()[0][0]
			self.suchString = callback
			streamGenreLink = 'http://www.eporner.com/search/%s/' % urllib.quote(self.suchString).replace(' ', '-')
			self.session.open(epornerFilmScreen, streamGenreLink, Name)

	def getSuggestions(self, text, max_res):
		url = "https://www.eporner.com/suggest/%s" % urllib.quote_plus(text)
		d = twAgentGetPage(url, agent=agent, headers=headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, err=True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = re.findall('title="(.*?)"', suggestions)
			for item in suggestions:
				li = item
				list.append(str(li))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class epornerFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, Name):
		self.CatLink = CatLink
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

		self['title'] = Label("Eporner.com")
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
		if re.match(".*%page", self.CatLink):
			url = self.CatLink.replace('%page',str(self.page))
		else:
			url = "%s%s/" % (self.CatLink, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="numlist2">(.*?)title=\'Next page\'')
		if "<h2>Recent HD Porn Videos</h2>" in data:
			data = re.search('<h2>Recent HD Porn Videos</h2>(.*?)</html>', data, re.S).group(1)
		Movies = re.findall('class="mb".*?>\s+<a\shref="(.*?)"\stitle="(.*?)".*?src="(.*?)".*?"mbtim">(.*?)</div>.*?"mbvie">(.*?)</div>', data, re.S)
		if Movies:
			for (Url, Title, Image, Runtime, Views) in Movies:
				Views = Views.replace(',','')
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste,0,1,2,3,None,self.page,self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nViews: %s" % (runtime, views))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		url = 'http://www.eporner.com%s' % (self['liste'].getCurrent()[0][1])
		self.keyLocked = True
		id = re.findall('//[^/]+/[^/]+/([^/]+)', url)
		if id:
			getPage(url).addCallback(self.getXMLPage,id[0]).addErrback(self.dataError)

	def int_to_str(self, n, b, symbols='0123456789abcdefghijklmnopqrstuvwxyz'):
		return (self.int_to_str(n/b, b, symbols) if n >= b else "") + symbols[n%b]

	def make_hash(self, s):
		return ''.join((self.int_to_str(int(s[lb:lb + 8], 16), 36) for lb in range(0, 32, 8)))

	def getXMLPage(self, data, id):
		videoPage = re.findall('hash:\s*["\']([^\'"]+)', data, re.S)
		xml = 'http://www.eporner.com/xhr/video/%s?device=generic&domain=www.eporner.com&hash=%s&fallback=false' % (id, self.make_hash(videoPage[0]))
		getPage(xml).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoRes = re.findall('"(\d+p).*?src["\']:\s+["\'](.*?)["\']', data, re.S)
		if videoRes:
			for item in videoRes:
				if "1080p" in item:
					url = item[1]
					break
				if "720p" in item:
					url = item[1]
					break
				if "360p" in item:
					url = item[1]
					break
		if url:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='eporner')