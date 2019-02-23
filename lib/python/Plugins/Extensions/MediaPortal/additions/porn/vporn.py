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
from Plugins.Extensions.MediaPortal.resources.configlistext import ConfigListScreenExt
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

config_mp.mediaportal.vporn_username = ConfigText(default="vpornUserName", fixed_size=False)
config_mp.mediaportal.vporn_password = ConfigPassword(default="vpornPassword", fixed_size=False)
config_mp.mediaportal.vporn_hd = ConfigText(default="SD/HD", fixed_size=False)
config_mp.mediaportal.vporn_date = ConfigText(default="all time", fixed_size=False)

vpagent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
vpck = {}
json_headers = {
	'Accept':'application/json',
	'Accept-Language':'en,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/x-www-form-urlencoded',
	}

default_cover = "file://%s/vporn.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class vpornGenreScreen(MPScreen):

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
			"green"	: self.keyHD,
			"yellow": self.keyDate,
			"blue": self.keySetup
		}, -1)

		self.hd = config_mp.mediaportal.vporn_hd.value
		self.date = config_mp.mediaportal.vporn_date.value
		self.username = str(config_mp.mediaportal.vporn_username.value)
		self.password = str(config_mp.mediaportal.vporn_password.value)

		self['title'] = Label("VPORN.com")
		self['ContentTitle'] = Label("Genre:")
		self['F2'] = Label(self.hd)
		self['F3'] = Label(self.date)
		#self['F4'] = Label(_("Setup"))
		self.keyLocked = True
		self.loggedin = False
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		#if self.username != "vpornUserName" and self.password != "vpornPassword":
		#	self.onLayoutFinish.append(self.Login)
		#else:
		self.onLayoutFinish.append(self.layoutFinished)

	def Login(self):
		self['name'].setText(_('Please wait...'))
		loginUrl = "https://www.vporn.com/login"
		loginData = {'backto': "", 'password': self.password, 'sub': 1, 'username': self.username}
		getPage(loginUrl, agent=vpagent, method='POST', postdata=urlencode(loginData), cookies=vpck, timeout=30, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.Login2).addErrback(self.dataError)

	def Login2(self, data):
		if 'href="/logout/"' in data:
			self.loggedin = True
		self.layoutFinished()

	def layoutFinished(self):
		self.keyLocked = True
		url = "https://www.vporn.com"
		getPage(url, agent=vpagent, cookies=vpck, timeout=30).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		#if not self.loggedin:
		#	message = self.session.open(MessageBoxExt, _("Login data is required for HD video playback!"), MessageBoxExt.TYPE_INFO, timeout=5)
		parse = re.search('class="cats-all categories-list">(.*?)</div>', data, re.S)
		Cats = re.findall('<li>\s<a\shref="(?!search)(.*?)".*?>(.*?)</a></li>', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Url = "https://www.vporn.com" + Url
				Title = Title.strip()
				self.genreliste.append((Title, Url, None, False))
			self.genreliste.sort()
			self.genreliste.insert(0, ("Longest", "https://www.vporn.com/longest/", None, True))
			self.genreliste.insert(0, ("Most Votes", "https://www.vporn.com/votes/", None, True))
			self.genreliste.insert(0, ("Most Comments", "https://www.vporn.com/comments/", None, True))
			self.genreliste.insert(0, ("Most Favorited", "https://www.vporn.com/favorites/", None, True))
			self.genreliste.insert(0, ("Most Viewed", "https://www.vporn.com/views/", None, True))
			self.genreliste.insert(0, ("Top Rated", "https://www.vporn.com/rating/", None, True))
			self.genreliste.insert(0, ("Newest", "https://www.vporn.com/newest/", None, True))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", None, True))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self['name'].setText('')
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen(suggest_func=self.getSuggestions)
		else:
			Link = self['liste'].getCurrent()[0][1]
			Main = self['liste'].getCurrent()[0][3]
			self.session.open(vpornFilmScreen, Link, Name, self.hd, self.date, Main)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = urllib.quote(callback).replace(' ', '+')
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			self.session.open(vpornFilmScreen, Link, Name, self.hd, self.date, False)

	def getSuggestions(self, text, max_res):
		url = "https://www.vporn.com/cgi-bin/suggest?q=%s" % urllib.quote_plus(text)
		d = twAgentGetPage(url, agent=vpagent, headers=json_headers, timeout=5)
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

	def keySetup(self):
		pass
		#if mp_globals.isDreamOS:
		#	self.session.openWithCallback(self.setupCallback, vpornSetupScreen, is_dialog=True)
		#else:
		#	self.session.openWithCallback(self.setupCallback, vpornSetupScreen)

	def setupCallback(self):
		pass

	def keyHD(self):
		if self.hd == "SD/HD":
			self.hd = "HD"
			config_mp.mediaportal.vporn_hd.value = "HD"
		elif self.hd == "HD":
			self.hd = "SD/HD"
			config_mp.mediaportal.vporn_hd.value = "SD/HD"

		config_mp.mediaportal.vporn_hd.save()
		configfile_mp.save()
		self['F2'].setText(self.hd)

	def keyDate(self):
		if self.date == "all time":
			self.date = "last 24h"
			config_mp.mediaportal.vporn_date.value = "last 24h"
		elif self.date == "last 24h":
			self.date = "last week"
			config_mp.mediaportal.vporn_date.value = "last week"
		elif self.date == "last week":
			self.date = "last month"
			config_mp.mediaportal.vporn_date.value = "last month"
		elif self.date == "last month":
			self.date = "all time"
			config_mp.mediaportal.vporn_date.value = "all time"

		config_mp.mediaportal.vporn_date.save()
		configfile_mp.save()
		self['F3'].setText(self.date)

class vpornSetupScreen(MPSetupScreen, ConfigListScreenExt):

	def __init__(self, session):
		MPSetupScreen.__init__(self, session, skin='MP_PluginSetup')

		self['title'] = Label("VPORN.com " + _("Setup"))
		self['F4'] = Label('')
		self.setTitle("VPORN.com " + _("Setup"))

		self.list = []
		ConfigListScreenExt.__init__(self, self.list)

		self.list.append(getConfigListEntry(_("Username:"), config_mp.mediaportal.vporn_username))
		self.list.append(getConfigListEntry(_("Password:"), config_mp.mediaportal.vporn_password))

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

class vpornFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name, HD, Date, Main):
		self.Link = Link
		self.Name = Name
		self.Main = Main
		if HD == "HD":
			self.hd = "hd/"
		else:
			self.hd = ""
		if Date == "last 24h":
			self.date = "today/"
		elif Date == "last week":
			self.date = "week/"
		elif Date == "last month":
			self.date = "month/"
		else:
			self.date = ""
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

		self['title'] = Label("VPORN.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		if not self.Main:
			self['F4'] = Label(_("Sort"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.sort = 'newest'
		self.sortname = 'Newest'

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "https://www.vporn.com/search/?q=%s&page=%s&time=%s" % (self.Link, str(self.page), self.date)
		else:
			if self.Main:
				sort = ""
			else:
				sort = self.sort
			if self.page == 1:
				url = "%s%s/%s%s" % (self.Link, sort , self.date, self.hd)
			else:
				url = "%s%s/%s%s%s" % (self.Link, sort , self.date, self.hd, str(self.page))
		getPage(url, agent=vpagent, cookies=vpck, timeout=30).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pages">(.*?)</div>')
		Movies = re.findall('class="video".*?href="(.*?)".*?class="time">(.*?)</span>.*?<img\ssrc="(.*?)"\salt="(.*?)".*?alt="Views">(\d+)', data, re.S)
		if Movies:
			for (Url, Runtime, Image, Title, Views) in Movies:
				Runtime = stripAllTags(Runtime).strip()
				Views = Views.replace(",","")
				if Url.startswith('//'):
					Url = "https:" + Url
				self.filmliste.append((decodeHtml(Title).strip(), Url, Image, Runtime, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"), None, None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		if self['liste'].getCurrent()[0][1] != None:
			title = self['liste'].getCurrent()[0][0]
			pic = self['liste'].getCurrent()[0][2]
			runtime = self['liste'].getCurrent()[0][3]
			views = self['liste'].getCurrent()[0][4]
			self['name'].setText(title)
			if not self.Main:
				sort = "\nSort order: %s" % self.sortname
			else:
				sort = ''
			self['handlung'].setText("Runtime: %s\nViews: %s%s" % (runtime, views, sort))
			CoverHelper(self['coverArt']).getCover(pic)
		else:
			self['name'].setText('')

	def keySort(self):
		if self.keyLocked or self.Main:
			return
		rangelist = [['Newest', 'newest'], ['Views','views'], ['Rating','rating'], ['Favorites','favorites'], ['Comments','comments'], ['Votes','votes'], ['Duration','longest']]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sortname = result[0]
			self.sort = result[1]
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			self.keyLocked = True
			getPage(url, agent=vpagent, cookies=vpck, timeout=30).addCallback(self.getVideoPage).addErrback(self.dataError)

	def getVideoPage(self, data):
		url = None
		videoPage = re.findall('initDownload\(\'(.*?)\'\)', data, re.S)
		if videoPage:
			url = videoPage[-1].replace('https://','http://')
		else:
			videoPage = re.findall('source\ssrc="(http.*?)"', data, re.S)
			if videoPage:
				url = videoPage[0].replace('https://','http://')
		if url:
			self.keyLocked = False
			Title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='vporn')