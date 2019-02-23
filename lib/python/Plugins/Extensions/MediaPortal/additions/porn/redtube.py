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
json_headers = {
	'Accept':'text/plain, */*; q=0.01',
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/x-www-form-urlencoded',
	'Referer':'https://www.redtube.com/',
	'Origin':'https://www.redtube.com/'
	}
default_cover = "file://%s/redtube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

token = ''

class redtubeGenreScreen(MPScreen):

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

		self['title'] = Label("RedTube.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "https://www.redtube.com/categories"
		twAgentGetPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		global token
		token = re.findall('page_params.token\s=\s"(.*?)";', data, re.S)[0]
		parse = re.search('id="categories_list_section"(.*?)$', data, re.S)
		Cats = re.findall('class="category_item_wrapper">.*?<a href="(.*?)".*?data-src="(.*?\.jpg).*?".*?alt="(.*?)"', parse.group(1), re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				Url = "https://www.redtube.com" + Url
				Title = Title.replace('&amp;','&')
				if Image.startswith('//'):
					Image = 'http:' + Image
				self.genreliste.append((Title, Url, Image, True))
			self.genreliste.sort()
		self.genreliste.insert(0, ("Recommended", "https://www.redtube.com/recommended", default_cover, True))
		self.genreliste.insert(0, ("Longest", "https://www.redtube.com/longest?period=alltime", default_cover, False))
		self.genreliste.insert(0, ("Most Favorited", "https://www.redtube.com/mostfavored?period=alltime", default_cover, False))
		self.genreliste.insert(0, ("Most Viewed", "https://www.redtube.com/mostviewed?period=alltime", default_cover, False))
		self.genreliste.insert(0, ("Top Rated", "https://www.redtube.com/top?period=alltime", default_cover, False))
		self.genreliste.insert(0, ("Trending", "https://www.redtube.com/hot", default_cover, False))
		self.genreliste.insert(0, ("Newest", "https://www.redtube.com/newest", default_cover, False))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover, True))
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
			Sort = self['liste'].getCurrent()[0][3]
			self.session.open(redtubeFilmScreen, Link, Name, Sort)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = urllib.quote(self.suchString).replace(' ', '+')
			self.session.open(redtubeFilmScreen, Link, Name, True)

	def getSuggestions(self, text, max_res):
		url = "https://www.redtube.com/video/search_autocomplete?pornstars=true&token=%s&orientation=straight&q=%s&alt=0" % (token, text.replace(' ', '+'))
		d = twAgentGetPage(url, agent=agent, headers=json_headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, err=True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions['queries']:
				li = item
				list.append(str(li))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class redtubeFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("RedTube.com")
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
		elif (re.match(".*?Search", self.Name) or self.Name == "Recommended"):
			self.sort = ''
			self.sorttext = 'Most Relevant'
		else:
			self.sort = ''
			self.sorttext = 'Newest'

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = 'https://www.redtube.com/%s?search=%s&page=%s' % (self.sort, self.Link, str(self.page))
		elif self.Name == "Recommended":
			url = "%s/%s?page=%s" % (self.Link, self.sort, str(self.page))
		else:
			if '?' in self.Link or '?' in self.sort:
				delim = '&'
			else:
				delim = '?'
			url = "%s%s%spage=%s" % (self.Link, self.sort, delim, str(self.page))
		twAgentGetPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		lastp = re.search('<h1>.*?\s\((.*?)\)</h1>', data, re.S)
		if lastp:
			lastp = lastp.group(1).replace(',','')
			cat = self.Link
			lastp = round((float(lastp) / 24) + 0.5)
			self.lastpage = int(lastp)
		else:
			self.lastpage = 1230
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		Movies = re.findall('class="video_block_wrapper">.*?<a\sclass="video_link.*?href="(\/\d+)".*?data-src\s{0,1}=\s{0,1}"(.*?)".*?duration">.*?(\d.*?)</a.*?a\stitle="(.*?)".*?video_count">(.*?)views', data, re.S)
		if Movies:
			for (Url, Image, Runtime, Title, Views) in Movies:
				if Image.startswith('//'):
					Image = 'http:' + Image
				Views = Views.replace(',','').strip()
				Runtime = stripAllTags(Runtime).strip()
				Title = Title.strip()
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
		CoverHelper(self['coverArt']).getCover(pic)

	def keySort(self):
		if self.keyLocked:
			return
		if not self.Sort:
			return
		if (re.match(".*?Search", self.Name) or self.Name == "Recommended"):
			rangelist = [['Newest', 'new'], ['Most Relevant',''], ['Most Viewed','mostviewed'], ['Top Rated','top'], ['Longest','longest']]
		else:
			rangelist = [['Newest', ''], ['Most Viewed','?sorting=mostviewed&period=alltime'], ['Most Favored','?sorting=mostfavored&period=alltime'], ['Top Rated','?sorting=rating&period=alltime'], ['Longest','?sorting=longest&period=alltime']]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sorttext = result[0]
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		Link = 'http://www.redtube.com' + self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		twAgentGetPage(Link).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		videoPage = re.findall('"quality":"(\d+)","videoUrl":"(http.*?)"', data, re.S)
		if videoPage:
			url = videoPage[0][1]
			url = url.replace('\/','/').replace('&amp;','&')
			if url.startswith('//'):
				url = 'http:' + url
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, url.replace('%2F','%252F').replace('%3D','%253D').replace('%2B','%252B'))], showPlaylist=False, ltype='redtube')