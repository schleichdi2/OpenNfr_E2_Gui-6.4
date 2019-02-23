# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

myagent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
json_headers = {
	'Accept':'application/json',
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/x-www-form-urlencoded',
	}

uid = ''

yps_cookies = CookieJar()

default_cover = "file://%s/yourpornsexy.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class YourPornSexyGenreScreen(MPScreen):

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

		self['title'] = Label("YourPornSexy")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://yourporn.sexy"
		twAgentGetPage(url, agent=myagent, cookieJar=yps_cookies).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		usss = re.findall('usss\[\'id\'\] = "(.*?)";', data, re.S)
		if usss:
			global uid
			uid = usss[0]
		parse = re.search('<span>Popular HashTags</span>(.*?)<div class=\'fbd\'', data, re.S)
		Cats = re.findall('<a(?:\sclass=\'tdn\'|)\shref=[\'|"](/blog/.*?)[\'|"].*?<span(?:\sclass=\'htag_el_tag\'|)>#(.*?)</span>', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://yourporn.sexy" + Url.replace('/0.html','/%s.html')
				Title = Title.lower().title()
				self.genreliste.append((Title, Url))
			self.genreliste.sort()
		self.genreliste.insert(0, ("Trends", "http://yourporn.sexy/searches/%s.html"))
		self.genreliste.insert(0, ("Orgasmic", "http://yourporn.sexy/orgasm/%s"))
		self.genreliste.insert(0, ("Pornstars", "http://yourporn.sexy/pornstars/%s.html"))
		self.genreliste.insert(0, ("Top Viewed (All Time)", "http://yourporn.sexy/popular/top-viewed.html/%s?p=all"))
		self.genreliste.insert(0, ("Top Viewed (Monthly)", "http://yourporn.sexy/popular/top-viewed.html/%s?p=month"))
		self.genreliste.insert(0, ("Top Viewed (Weekly)", "http://yourporn.sexy/popular/top-viewed.html/%s?p=week"))
		self.genreliste.insert(0, ("Top Viewed (Daily)", "http://yourporn.sexy/popular/top-viewed.html/%s?p=day"))
		self.genreliste.insert(0, ("Top Rated (All Time)", "http://yourporn.sexy/popular/top-rated.html/%s?p=all"))
		self.genreliste.insert(0, ("Top Rated (Monthly)", "http://yourporn.sexy/popular/top-rated.html/%s?p=month"))
		self.genreliste.insert(0, ("Top Rated (Weekly)", "http://yourporn.sexy/popular/top-rated.html/%s?p=week"))
		self.genreliste.insert(0, ("Top Rated (Daily)", "http://yourporn.sexy/popular/top-rated.html/%s?p=day"))
		self.genreliste.insert(0, ("Newest", "http://yourporn.sexy/blog/all/%s.html?fl=all&sm=latest"))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen(suggest_func=self.getSuggestions)
		elif Name == "Trends":
			self.session.open(YourPornSexyTrendsScreen, Link, Name)
		elif Name == "Pornstars":
			self.session.open(YourPornSexyPornstarsScreen, Link, Name)
		else:
			self.session.open(YourPornSexyFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = urllib.quote(self.suchString).replace(' ', '-')
			self.session.open(YourPornSexyFilmScreen, Link, Name)

	def getSuggestions(self, text, max_res):
		url = "https://yourporn.sexy/php/livesearch.php"
		postdata = {'key': text.replace(' ','-'), 'c':'livesearch4', 'uid': uid}
		d = twAgentGetPage(url, method='POST', postdata=urlencode(postdata), agent=myagent, headers=json_headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, err=True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions['searches']:
				li = item['title']
				list.append(str(li))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class YourPornSexyPornstarsScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("YourPornSexy")
		self['ContentTitle'] = Label("Pornstars:")
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 26

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		alfa = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.genreliste = []
		url = self.Link.replace('%s', alfa[self.page-1])
		twAgentGetPage(url, agent=myagent, cookieJar=yps_cookies).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self['page'].setText(str(self.page) + '/' +str(self.lastpage))
		preparse = re.search('.*?pstars_container(.*?)d="center_control"', data, re.S)
		Cats = re.findall("<a href='/(.*?).html' title='.*?PornStar Page'><div class='ps_el'>(.*?)</div></a>", preparse.group(1) , re.S)
		if Cats:
			for (Url, Title) in Cats:
				self.genreliste.append((Title, Url))
			self.genreliste.sort
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(YourPornSexyFilmScreen, Link, self.Name)

class YourPornSexyTrendsScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("YourPornSexy")
		self['ContentTitle'] = Label("Trends:")
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.genreliste = []
		url = self.Link.replace('%s', str((self.page-1)*150))
		twAgentGetPage(url, agent=myagent, cookieJar=yps_cookies).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', 'ctrl_el.*>(\d+)</div')
		Cats = re.findall('title=\'.*?\'>(.*?)</a></td><td>(\d+)</td><td\sstyle=\'color:#.{6}\'>.{0,1}\d+</td><td>(\d+)</td>', data , re.S)
		if Cats:
			for (Title, Frequency, Results) in Cats:
				self.genreliste.append((Title, Title, Frequency, Results))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		freq = self['liste'].getCurrent()[0][2]
		results = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText("Frequency: %s\nResults: %s" % (freq, results))

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(YourPornSexyFilmScreen, Link, self.Name)

class YourPornSexyFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"5" : self.keyShowThumb,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("YourPornSexy")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.tw_agent_hlp = TwAgentHelper()

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if self.Name == "Newest":
			count = 20
		elif self.Name == "Orgasmic":
			count = 30
		elif (re.match(".*?Top Rated", self.Name) or re.match(".*?Top Viewed", self.Name)):
			count = 30
		else:
			count = 20
		if re.match(".*?Search", self.Name) or self.Name == "Trends" or self.Name == "Pornstars":
			url = "https://yourporn.sexy/%s.html?page=%s" % (self.Link, str((self.page-1)*30))
			twAgentGetPage(url, agent=myagent, cookieJar=yps_cookies).addCallback(self.loadData).addErrback(self.dataError)
		else:
			url = self.Link.replace('%s', str((self.page-1)*count))
			twAgentGetPage(url, agent=myagent, cookieJar=yps_cookies).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', 'ctrl_el.*>(\d+)</div')
		prep = data
		if re.search("</head>(.*?)<span>Other Results</span>", data, re.S):
			preparse = re.search('</head>(.*?)<span>Other Results</span>', data, re.S)
			if preparse:
				prep = preparse.group(1)
		if re.search("class='main_content'(.*?)id='center_control'", data, re.S):
			preparse = re.search("class='main_content'(.*?)id='center_control'", data, re.S)
			if preparse:
				prep = preparse.group(1)
		Videos = re.findall('class=\'pes_author_div(.*?)(?:tm_playlist_hl|small_post_control)', prep, re.S)
		if Videos:
			for Video in Videos:
				Movie = re.findall("src='(.*?.jpg)'.*?class='duration_small'.*?'>(.*?)</span></div></div><div class='post_control'><a class='tdn post_time' href='(.*?\.html.*?)'\stitle='(?!bitrate:\d+)(.*?)'>(.*?\sviews)", Video, re.S)
				if Movie:
					for (Image, Runtime, Url, Title, AddedViews) in Movie:
						if "post_control_time" in AddedViews:
							av = re.findall("class='post_control_time'><span>([\d|Hour].*?ago|Yesterday|Last month|Last year)\s{0,1}</span><strong>.{0,3}</strong>\s{0,1}(\d+)\sviews", AddedViews, re.S)
							if av:
								Added = av[0][0]
								Views = av[0][1]
							else:
								Added = "-"
								Views = "-"
							Url = "http://yourporn.sexy" + Url
							if Image.startswith('//'):
								Image = "http:" + Image
							self.filmliste.append((decodeHtml(Title), Url, Image, Views, Runtime, Added))


				else:
					Movie = re.findall("href='(/post.*?\.html.*?)'.*?src='(.*?)'.*?class='duration_small'.*?'>(.*?)<.*?title='(?!bitrate:\d+)(.*?)'(.*?\sviews)", Video, re.S)
					if Movie:
						for (Url, Image, Runtime, Title, AddedViews) in Movie:
							if "post_control_time" in AddedViews:
								av = re.findall("class='post_control_time'><span>([\d|Hour].*?ago|Yesterday|Last month|Last year)\s{0,1}</span><strong>.{0,3}</strong>\s{0,1}(\d+)\sviews", AddedViews, re.S)
								if av:
									Added = av[0][0]
									Views = av[0][1]
								else:
									Added = "-"
									Views = "-"
								Url = "http://yourporn.sexy" + Url
								if Image.startswith('//'):
									Image = "http:" + Image
								self.filmliste.append((decodeHtml(Title), Url, Image, Views, Runtime, Added))

		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, '', '', ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()
		self.keyLocked = False

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		views = self['liste'].getCurrent()[0][3]
		runtime = self['liste'].getCurrent()[0][4]
		added = self['liste'].getCurrent()[0][5]
		self['name'].setText(title)
		self['handlung'].setText("Views: %s\nRuntime: %s\nAdded: %s" % (views, runtime, added))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		twAgentGetPage(Link, agent=myagent, cookieJar=yps_cookies).addCallback(self.getVideoUrl).addErrback(self.dataError)

	def getVideoUrl(self, data):
		videoUrl = re.findall('data-vnfo=\'\{"[0-9a-f]+":"(.*?)"\}\'', data, re.S)
		if videoUrl:
			url = videoUrl[-1].replace('\/','/')
			url = 'https://yourporn.sexy' + url.replace('/cdn/','/cdn4/')
			self.tw_agent_hlp.getRedirectedUrl(url).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, url):
		Title = self['liste'].getCurrent()[0][0]
		if url.startswith('//'):
			url = "http:" + url
		self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='yourpornsexy')
		self.keyLocked = False