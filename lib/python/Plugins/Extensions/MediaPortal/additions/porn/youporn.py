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
from Plugins.Extensions.MediaPortal.resources.configlistext import ConfigListScreenExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

config_mp.mediaportal.youporn_username = ConfigText(default="youpornUserName", fixed_size=False)
config_mp.mediaportal.youporn_password = ConfigPassword(default="youpornPassword", fixed_size=False)

ck = CookieJar()
ypLoggedIn = False
ypAgent = getUserAgent()

headers = {
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	}
default_cover = "file://%s/youporn.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class youpornGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"blue": self.keySetup
		}, -1)

		self.username = str(config_mp.mediaportal.youporn_username.value)
		self.password = str(config_mp.mediaportal.youporn_password.value)

		self['title'] = Label("YouPorn.com")
		self['ContentTitle'] = Label("Genre:")
		self['F4'] = Label(_("Setup"))
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		if self.username != "youpornUserName" and self.password != "youpornPassword":
			if ypLoggedIn:
				self.onLayoutFinish.append(self.layoutFinished)
			else:
				self.onLayoutFinish.append(self.Login)
		else:
			self.onLayoutFinish.append(self.layoutFinished)

	def Login(self):
		loginUrl = "https://www.youporn.com/login/"
		loginData = {
			'login[username]' : self.username,
			'login[password]' : self.password
			}
		twAgentGetPage(loginUrl, agent=ypAgent, method='POST', postdata=urlencode(loginData), cookieJar=ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.Login2).addErrback(self.dataError)

	def Login2(self, data):
		url = "https://www.youporn.com/login/"
		twAgentGetPage(url, agent=ypAgent, cookieJar=ck).addCallback(self.Login3).addErrback(self.dataError)

	def Login3(self, data):
		global ypLoggedIn
		if re.findall('loginForm', data):
			ypLoggedIn = False
		else:
			ypLoggedIn = True
		self.layoutFinished()

	def layoutFinished(self):
		self.keyLocked = True
		url = "http://www.youporn.com/categories/alphabetical/"
		twAgentGetPage(url, agent=ypAgent, cookieJar=ck).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		Cats = None
		self.genreliste = []
		preparse = re.search('categoryListWrapper"(.*?)id="countryFlags"', data, re.S)
		if preparse:
			Cats = re.findall('<a\shref="((?:/category|https://www.youporn.com).*?)".*?img\ssrc.*?alt="(.*?)".*?data-original="(.*?)"', preparse.group(1), re.S)
		if Cats:
			for (Url, Title, Image) in Cats:
				Url = "http://www.youporn.com" + Url + '?page='
				self.genreliste.append((Title, Url, Image))
			# remove duplicates
			self.genreliste = list(set(self.genreliste))
			self.genreliste.sort()
		if ypLoggedIn:
			self.genreliste.insert(0, (400 * "—", None, default_cover))
			self.genreliste.insert(0, ("Recommended", "http://www.youporn.com/recommended/?page=", default_cover))
			self.genreliste.insert(0, ("Favourite Videos", "http://www.youporn.com/favorites/?page=", default_cover))
		self.genreliste.insert(0, (400 * "—", None, default_cover))
		self.genreliste.insert(0, ("Channels", "http://www.youporn.com/channels/most_subscribed/?page=", default_cover))
		self.genreliste.insert(0, ("Popular by Country", "http://www.youporn.com/categories/", default_cover))
		self.genreliste.insert(0, ("Most Discussed", "http://www.youporn.com/most_discussed/?page=", default_cover))
		self.genreliste.insert(0, ("Most Favorited", "http://www.youporn.com/most_favorited/?page=", default_cover))
		self.genreliste.insert(0, ("Most Viewed", "http://www.youporn.com/most_viewed/?page=", default_cover))
		self.genreliste.insert(0, ("Top Rated", "http://www.youporn.com/top_rated/?page=", default_cover))
		if not ypLoggedIn:
			self.genreliste.insert(0, ("Recommended", "http://www.youporn.com/recommended/?page=", default_cover))
		self.genreliste.insert(0, ("Newest", "http://www.youporn.com/browse/time/?page=", default_cover))
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
		elif Name == "Channels":
			Link = self['liste'].getCurrent()[0][1]
			if Link:
				self.session.open(youpornChannelScreen, Link, Name)
		elif Name == "Popular by Country":
			Link = self['liste'].getCurrent()[0][1]
			if Link:
				self.session.open(youpornCountryScreen, Link, Name)
		else:
			Link = self['liste'].getCurrent()[0][1]
			if Link:
				self.session.open(youpornFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = 'http://www.youporn.com/search/?query=%s&page=' % self.suchString.replace(' ', '+')
			self.session.open(youpornFilmScreen, Link, Name)

	def keySetup(self):
		if mp_globals.isDreamOS:
			self.session.openWithCallback(self.setupCallback, youpornSetupScreen, is_dialog=True)
		else:
			self.session.openWithCallback(self.setupCallback, youpornSetupScreen)

	def setupCallback(self, answer=False):
		if answer:
			ck.clear()
			global ypLoggedIn
			ypLoggedIn = False
			self.username = str(config_mp.mediaportal.youporn_username.value)
			self.password = str(config_mp.mediaportal.youporn_password.value)
			self.Login()

	def getSuggestions(self, text, max_res):
		url = "http://www.youporn.com/search/autocomplete/%s/" % urllib.quote_plus(text)
		d = twAgentGetPage(url, agent=ypAgent, headers=headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, err=True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions['queries']:
				li = item.replace('+',' ')
				list.append(str(li))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class youpornSetupScreen(MPSetupScreen, ConfigListScreenExt):

	def __init__(self, session):
		MPSetupScreen.__init__(self, session, skin='MP_PluginSetup')

		self['title'] = Label("YouPorn.com " + _("Setup"))
		self['F4'] = Label('')
		self.setTitle("YouPorn.com " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		self.list.append(getConfigListEntry(_("Username:"), config_mp.mediaportal.youporn_username))
		self.list.append(getConfigListEntry(_("Password:"), config_mp.mediaportal.youporn_password))

		self["config"].setList(self.list)

		self["setupActions"] = ActionMap(["MP_Actions"],
		{
			"ok"    : self.keySave,
			"cancel": self.keyCancel
		}, -1)

	def keySave(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		self.close(True)

class youpornCountryScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("YouPorn.com")
		self['ContentTitle'] = Label("Country Auswahl")
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.genreliste = []
		url = self.Link
		getPage(url, agent=ypAgent, headers={'Cookie': 'age_verified=1'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('id="countryFlags">(.*?)heading4">Network\sSites</h2>', data, re.S)
		Cats = re.findall('<a\sclass="countryBox\sflag\sflag-.*?"\shref="(.*?)">.*?<span\sclass=\'countryTag\'>(.*?)</span', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "http://www.youporn.com" + Url + "?page="
				self.genreliste.append((Title.strip(), Url))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(youpornFilmScreen, Link, Name)

class youpornChannelScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("YouPorn.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
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
		self.genreliste = []
		url = "%s%s" % (self.Link, str(self.page))
		twAgentGetPage(url, agent=ypAgent, cookieJar=ck).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		self.getLastPage(data, 'objectPagination =.*?total: (\d+),', '(\d+)')
		Cats = re.findall('channel-box-image.*?<img\ssrc=.*?data-original="(.*?)".*?channel-box-title">.*?href="(.*?)">(.*?)</', data, re.S)
		if Cats:
			for (Image, Url, Title) in Cats:
				Url = "http://www.youporn.com" + Url + 'time/?page='
				self.genreliste.append((Title.strip(), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.genreliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(youpornFilmScreen, Link, Name)

class youpornFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("YouPorn.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1

		self.tw_agent_hlp = TwAgentHelper(followRedirect=True)
		self.tw_agent_hlp.headers['Cookie'] = 'age_verified=1'
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s%s" % (self.Link, str(self.page))
		twAgentGetPage(url, agent=ypAgent, cookieJar=ck).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'objectPagination =.*?total: (\d+),', '(\d+)')
		parse = re.search('My Favorited Videos(.*?)class=\'ad-bottom-text', data, re.S)
		if not parse:
			parse = re.search('eight-column\sheading4\'>Videos from(.*?)class=\'ad-bottom-text', data, re.S)
			if not parse:
				parse = re.search('class=\'container\'>(.*?)search-suggestions', data, re.S)
				if not parse:
					parse = re.search('heading4\'>Most Recent Videos</h2(.*?)class=\'ad-bottom-text', data, re.S)
					if not parse:
						parse = re.search('class=\'ad-bottom-text\'>(.*?)class=\'footer', data, re.S)
		if parse:
			Movies = re.findall('class=\'video-box.*?<a\shref="(.*?)".*?<img\ssrc=".*?"\salt=\'(.*?)\'.*?data-(?:thumbnail|echo)="(.*?)".*?class=\'video-box-percentage\sup\'>(.*?)</.*?class="video-duration">(.*?)</', parse.group(1), re.S)
			if Movies:
				for (Url, Title, Image, Rating, Runtime) in Movies:
					Url = Url.replace("&amp;","&")
					self.filmliste.append((decodeHtml(Title), Url, Image, Runtime.strip(), Rating.strip()))
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
		rating = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		self['handlung'].setText("Runtime: %s\nRating: %s" % (runtime, rating))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = 'http://www.youporn.com' + self['liste'].getCurrent()[0][1]
		self.keyLocked = True
		getPage(Link, agent=ypAgent, headers={'Cookie': 'age_verified=1'}).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		Title = self['liste'].getCurrent()[0][0]
		parse = re.findall('video.mediaDefinition =.{0,2}\[(.*?)\];', data, re.S)
		if parse:
			videoPage = re.findall('\d+","videoUrl":[\"|\'](http[s]?.*?)[\"|\']', parse[-1], re.S)
			if videoPage:
				self.keyLocked = False
				url = videoPage[0].replace('\/','/').replace('%2F','%252F').replace('%3D','%253D').replace('%2B','%252B')
				self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='youporn')