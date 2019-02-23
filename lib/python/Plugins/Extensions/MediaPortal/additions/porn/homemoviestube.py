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

hmtAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
json_headers = {
	'Accept':'application/json',
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/x-www-form-urlencoded',
	}
	
default_cover = "file://%s/homemoviestube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class homemoviestubeGenreScreen(MPScreen):

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

		self['title'] = Label("HomeMoviesTube.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.homemoviestube.com/"
		getPage(url, agent=hmtAgent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('<h4>Channels</h4>(.*?)<h4>Top Categories', data, re.S)
		if parse:
			Cats = re.findall('<a\shref=[\'|"](http://www.homemoviestube.com/channels/.*?)[\'|"]>(.*?)<', parse.group(1), re.S)
			if Cats:
				for (Url, Title) in Cats:
					Title = Title.strip(' ')
					self.genreliste.append((Title, Url))
				self.genreliste.sort()
		self.genreliste.insert(0, ("Longest", 'http://www.homemoviestube.com/longest/'))
		self.genreliste.insert(0, ("Most Viewed", 'http://www.homemoviestube.com/most-viewed/'))
		self.genreliste.insert(0, ("Most Favorited", 'http://www.homemoviestube.com/most-favored/'))
		self.genreliste.insert(0, ("Top Rated", 'http://www.homemoviestube.com/top-rated/'))
		self.genreliste.insert(0, ("Most Recent", 'http://www.homemoviestube.com/most-recent/'))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen(suggest_func=self.getSuggestions)
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(homemoviestubeFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = '%s' % urllib.quote(self.suchString).replace(' ', '-')
			self.session.open(homemoviestubeFilmScreen, Link, Name)

	def getSuggestions(self, text, max_res):
		url = "http://www.homemoviestube.com/autocomplete.php?term=%s" % urllib.quote_plus(text)
		d = twAgentGetPage(url, agent=hmtAgent, headers=json_headers, timeout=5)
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

class homemoviestubeFilmScreen(MPScreen, ThumbsHelper):

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
			"green" : self.keyPageNumber,
			"blue" : self.keySort
		}, -1)

		self['title'] = Label("HomeMoviesTube.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		if re.match('.*?\/channels\/', self.Link):
			self['F4'] = Label(_("Sort"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.sortfilter = 'newest/'
		self.sort = 'Latest'
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.streamList = []
		if re.match(".*?Search", self.Name):
			url = "http://www.homemoviestube.com/search/%s/page%s.html" % (self.Link, str(self.page))
		elif re.match('.*?\/channels\/', self.Link):
			url = self.Link + self.sortfilter + "page%s.html" % str(self.page)
		else:
			url = self.Link + "page%s.html" % str(self.page)
		getPage(url, agent=hmtAgent).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		self.getLastPage(data, 'pagination-items">(.*?)</div>')
		if re.search('id="featured-videos"', data, re.S):
			parse = re.search('<!-- featured-end --(.*?</html>', data, re.S)
		else:
			parse = re.search('<head>(.*)</html>', data, re.S)
		Liste = re.findall('class="film-item.*?-wrapper">(.*?)<a\shref="(.*?)"\stitle="(.*?)".*?class="film-thumb.*?img\ssrc="(.*?)".*?class="film-time">(.*?)</span.*?stat-added">(.*?)</span>.*?stat-views">(.*?)</span.*?stat-rated">(.*?)</span', parse.group(1), re.S)
		if Liste:
			for (Premium, Link, Name, Image, Runtime, Added, Views, Rated) in Liste:
				if not "premium_star.png" in Premium:
					self.streamList.append((decodeHtml(Name), Image, Link, Runtime, Added, Views, Rated))
		if len(self.streamList) == 0:
			self.streamList.append((_('No videos found!'), None, '', ''))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.streamList, 0, 2, 1, 3, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][1].replace(' ','%20')
		runtime = self['liste'].getCurrent()[0][3]
		added = self['liste'].getCurrent()[0][4]
		views = self['liste'].getCurrent()[0][5]
		rated = self['liste'].getCurrent()[0][6]
		self['name'].setText(title)
		if re.match(".*?Search", self.Name):
			self['handlung'].setText("Runtime: %s\nViews: %s\nAdded: %s\nRating: %s" % (runtime, views, added, rated))
		else:
			self['handlung'].setText("Runtime: %s\nViews: %s\nAdded: %s\nRating: %s\nSort: %s" % (runtime, views, added, rated, self.sort))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][2]
		self.keyLocked = True
		getPage(Link, agent=hmtAgent).addCallback(self.getVideo).addErrback(self.dataError)

	def keySort(self):
		if self.keyLocked or not re.match('.*?\/channels\/', self.Link):
			return
		rangelist = [['Latest', 'newest/'], ['Rating', 'rating/'], ['Views','views/'], ['Length','longest/'], ['Favored','most-favored/']]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sortfilter = result[1]
			self.sort = result[0]
			self.loadPage()

	def getVideo(self, data):
		Title = self['liste'].getCurrent()[0][0]
		File = re.findall('<source src="(.*?)" type=\'video/mp4\'>', data)
		if File:
			self.keyLocked = False
			self.session.open(SimplePlayer, [(Title, File[0])], showPlaylist=False, ltype='homemoviestube')