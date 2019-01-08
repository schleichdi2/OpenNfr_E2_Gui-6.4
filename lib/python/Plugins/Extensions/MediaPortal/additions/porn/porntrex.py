# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.configlistext import ConfigListScreenExt

myagent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'

config_mp.mediaportal.porntrex_username = ConfigText(default="porntrexUserName", fixed_size=False)
config_mp.mediaportal.porntrex_password = ConfigPassword(default="porntrexPassword", fixed_size=False)
config_mp.mediaportal.javwhores_username = ConfigText(default="javwhoresUserName", fixed_size=False)
config_mp.mediaportal.javwhores_password = ConfigPassword(default="javwhoresPassword", fixed_size=False)

ck = {}
LoggedIn = False
username = ""
password = ""

class porntrexGenreScreen(MPScreen):

	def __init__(self, session, mode):
		self.mode = mode

		global default_cover
		if self.mode == "porntrex":
			self.portal = "Porntrex.com"
			self.baseurl = "https://www.porntrex.com"
			default_cover = "file://%s/porntrex.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
			global username
			global password
			username = str(config_mp.mediaportal.porntrex_username.value)
			password = str(config_mp.mediaportal.porntrex_password.value)
		elif self.mode == "javwhores":
			self.portal = "JavWhores.com"
			self.baseurl = "https://www.javwhores.com"
			default_cover = "file://%s/javwhores.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
			global username
			global password
			username = str(config_mp.mediaportal.javwhores_username.value)
			password = str(config_mp.mediaportal.javwhores_password.value)
		elif self.mode == "camwhoresbay":
			self.portal = "Camwhoresbay.com"
			self.baseurl = "https://www.camwhoresbay.com"
			default_cover = "file://%s/camwhoresbay.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

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

		self['title'] = Label(self.portal)
		self['ContentTitle'] = Label("Genre:")
		if self.mode == "porntrex" or self.mode == "javwhores":
			self['F4'] = Label(_("Setup"))
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		ck.clear()
		global LoggedIn
		LoggedIn = False
		url = self.baseurl + "/categories/"
		getPage(url, agent=myagent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('.*?class="list-categories">(.*?)</html>', data, re.S)
		if parse:
			Cats = re.findall('class="item"\shref="(.*?)"\stitle="(.*?)".*?thumb"\ssrc="(.*?)"', parse.group(1), re.S)
			if Cats:
				for (Url, Title, Image) in Cats:
					if Image.startswith('//'):
						Image = 'https:' + Image
					self.genreliste.append((decodeHtml(Title), Url, Image))
				self.genreliste.sort()
				self.genreliste.insert(0, ("Top Rated", '%s/top-rated/' % self.baseurl, default_cover))
				self.genreliste.insert(0, ("Most Popular", '%s/most-popular/' % self.baseurl, default_cover))
				self.genreliste.insert(0, ("Most Recent", '%s/latest-updates/' % self.baseurl, default_cover))
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
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(porntrexFilmScreen, Link, Name, self.portal, self.baseurl)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = callback.replace(' ', '-')
			self.session.open(porntrexFilmScreen, Link, Name, self.portal, self.baseurl)

	def keySetup(self):
		if self.mode == "porntrex" or self.mode == "javwhores":
			if mp_globals.isDreamOS:
				self.session.openWithCallback(self.setupCallback, porntrexSetupScreen, self.mode, self.portal, is_dialog=True)
			else:
				self.session.openWithCallback(self.setupCallback, porntrexSetupScreen, self.mode, self.portal)

	def setupCallback(self, answer=False):
		if answer:
			global LoggedIn
			global username
			global password
			ck.clear()
			LoggedIn = False
			if self.mode == "porntrex":
				username = str(config_mp.mediaportal.porntrex_username.value)
				password = str(config_mp.mediaportal.porntrex_password.value)
			elif self.mode == "javwhores":
				username = str(config_mp.mediaportal.javwhores_username.value)
				password = str(config_mp.mediaportal.javwhores_password.value)

class porntrexSetupScreen(MPSetupScreen, ConfigListScreenExt):

	def __init__(self, session, mode, portal):
		self.mode = mode
		self.portal = portal
		MPSetupScreen.__init__(self, session, skin='MP_PluginSetup')

		self['title'] = Label(self.portal + " " + _("Setup"))
		self['F4'] = Label('')
		self.setTitle(self.portal + " " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		if self.mode == "porntrex":
			self.list.append(getConfigListEntry(_("Username:"), config_mp.mediaportal.porntrex_username))
			self.list.append(getConfigListEntry(_("Password:"), config_mp.mediaportal.porntrex_password))
		elif self.mode == "javwhores":
			self.list.append(getConfigListEntry(_("Username:"), config_mp.mediaportal.javwhores_username))
			self.list.append(getConfigListEntry(_("Password:"), config_mp.mediaportal.javwhores_password))

		self["config"].setList(self.list)

		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"ok":		self.saveConfig,
			"cancel":	self.exit
		}, -1)

	def saveConfig(self):
		for x in self["config"].list:
			x[1].save()
		configfile_mp.save()
		self.close()

	def exit(self):
		self.close()

class porntrexFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, portal, baseurl):
		self.portal = portal
		self.baseurl = baseurl
		self.Link = Link
		self.Name = Name

		global default_cover
		if self.portal == "Porntrex.com":
			default_cover = "file://%s/porntrex.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		elif self.portal == "JavWhores.com":
			default_cover = "file://%s/javwhores.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
		elif self.portal == "Camwhoresbay.com":
			default_cover = "file://%s/camwhoresbay.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

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

		self['title'] = Label(self.portal)
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
			if self.portal == "Porntrex.com":
				url = "%s/search/%s/?mode=async&function=get_block&block_id=list_videos_videos&q=%s&category_ids=&sort_by=relevance&from_videos=%s" % (self.baseurl, self.Link, self.Link.replace('-','+'), str(self.page))
			else:
				url = "%s/search/%s/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&from_videos=%s" % (self.baseurl, self.Link, str(self.page))
		else:
			url = "%s%s/" % (self.Link, str(self.page))
		getPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination"(.*?)</ul>')
		Movies = re.findall('class="video-item.*?href="(.*?)"\stitle="(.*?)".*?data-(?:original|src)="(.*?)".*?</a>(.*?)class="ico.*?class="viewsthumb">(.*?)\sviews.*?clock-o"></i>(.*?)</div.*?list-unstyled">.*?<li>(.*?)</li', data, re.S)
		if Movies:
			for (url, title, image, private, views, runtime, added) in Movies:
				if image.startswith('//'):
					image = 'https:' + image
				runtime = runtime.strip()
				views = views.replace(' ','')
				if "private" in private:
					private = True
				else:
					private = False
				self.filmliste.append((decodeHtml(title), url, image, runtime, views, added, private))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), None, None, '', '', '', False))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, int(self.lastpage), mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		added = self['liste'].getCurrent()[0][5]
		self['handlung'].setText("Runtime: %s\nAdded: %s\nViews: %s" % (runtime, added, views))
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		private = self['liste'].getCurrent()[0][6]
		if not private:
			self.keyLocked = True
			getPage(url, agent=myagent).addCallback(self.getVideoPage).addErrback(self.dataError)
		elif LoggedIn:
			self.keyLocked = True
			getPage(url, agent=myagent, cookies=ck).addCallback(self.getVideoPage).addErrback(self.dataError)
		else:
			self.Login(url)

	def Login(self, url):
		self['name'].setText(_('Please wait...'))
		loginUrl = "%s/login/" % self.baseurl
		loginData = {'action': "login", 'pass': password, 'remember_me': 1, 'username': username, 'format': "json", 'mode': "async", 'email_link': "%s/email/" % self.baseurl}
		getPage(loginUrl, agent=myagent, method='POST', postdata=urlencode(loginData), cookies=ck, timeout=30, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.Login2, url).addErrback(self.dataError)

	def Login2(self, data, url):
		if '"status":"success",' in data:
			global LoggedIn
			LoggedIn = True
			self.keyLocked = True
			getPage(url, agent=myagent, cookies=ck).addCallback(self.getVideoPage).addErrback(self.dataError)
		else:
			message = self.session.open(MessageBoxExt, _("Login data is required video playback!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def getVideoPage(self, data):
		vidurl = None
		url = re.findall("video_(?:alt_|)url(?:\d+|):\s.{0,1}'(.*?)'", data, re.S)
		if url:
			vidurl = url[-1]
			if "2160p" in vidurl or "1440p" in vidurl:
				vidurl = url[-2]
			if "2160p" in vidurl or "1440p" in vidurl:
				vidurl = url[-3]
		else:
			url = re.findall('Download:.*?href="(.*?)\/\?download', data, re.S)
			if url:
				vidurl = url[-1]
		if vidurl:
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, vidurl)], showPlaylist=False, ltype='porntrex')
		self.keyLocked = False