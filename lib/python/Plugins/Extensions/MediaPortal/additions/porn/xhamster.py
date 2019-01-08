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
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

ck = {}
favourites = []
subscriptions = []
pornstars = []
xhAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
base_url = "https://xhamster.com"

default_cover = "file://%s/xhamster.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

def writeFavSub():
	try:
		wl_path = config_mp.mediaportal.watchlistpath.value+"mp_xhamster_favsub"
		writefavsub = open(wl_path, 'w')
		for m in favourites:
			writefavsub.write('"fav";"%s";"%s"\n' % (m[0], m[1]))
		for m in subscriptions:
			writefavsub.write('"sub";"%s";"%s"\n' % (m[0], m[1]))
		for m in pornstars:
			writefavsub.write('"star";"%s";"%s"\n' % (m[0], m[1]))
		writefavsub.close()
	except:
		pass

class xhamsterGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("xHamster.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadFavSub)
		self.onLayoutFinish.append(self.layoutFinished)

	def loadFavSub(self):
		global favourites
		favourites = []
		global subscriptions
		subscriptions = []
		global pornstars
		pornstars = []
		self.wl_path = config_mp.mediaportal.watchlistpath.value+"mp_xhamster_favsub"
		try:
			readfavsub = open(self.wl_path,"r")
			rawData = readfavsub.read()
			readfavsub.close()
			for m in re.finditer('"(.*?)";"(.*?)";"(.*?)"\n', rawData):
				(type, link, name) = m.groups()
				if type == "fav":
					favourites.append(((link, name)))
				elif type == "sub":
					subscriptions.append((link, name))
				elif type == "star":
					pornstars.append((link, name))
		except:
			pass

	def layoutFinished(self):
		url = base_url + "/categories"
		getPage(url, agent=xhAgent, cookies=ck).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('class="letter-blocks(.*?)class="footer-buffer">', data, re.S)
		Cats = re.findall('<a\shref="(https://xhamster.com\/(?:channels\/|categories\/|tags\/).*?)(?:-1.html|)"\s{0,2}>(.*?)</a', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				Title = Title.strip(' ')
				self.genreliste.append((decodeHtml(Title), Url))
		self.genreliste.sort()
		self.genreliste.insert(0, (400 * "—", None))
		self.genreliste.insert(0, ("Subscriptions", 'subs'))
		self.genreliste.insert(0, ("Favourite Pornstars", 'stars'))
		self.genreliste.insert(0, ("Favourite Videos", 'favs'))
		self.genreliste.insert(0, (400 * "—", None))
		self.genreliste.insert(0, ("Pornstars", '%s/pornstars' % base_url))
		self.genreliste.insert(0, ("Most Commented (All Time)", '%s/most-commented' % base_url))
		self.genreliste.insert(0, ("Most Commented (Monthly)", '%s/most-commented/monthly' % base_url))
		self.genreliste.insert(0, ("Most Commented (Weekly)", '%s/most-commented/weekly' % base_url))
		self.genreliste.insert(0, ("Most Commented (Daily)", '%s/most-commented/daily' % base_url))
		self.genreliste.insert(0, ("Most Viewed (All Time)", '%s/most-viewed' % base_url))
		self.genreliste.insert(0, ("Most Viewed (Monthly)", '%s/most-viewed/monthly' % base_url))
		self.genreliste.insert(0, ("Most Viewed (Weekly)", '%s/most-viewed/weekly' % base_url))
		self.genreliste.insert(0, ("Most Viewed (Daily)", '%s/most-viewed/daily' % base_url))
		self.genreliste.insert(0, ("Top Rated (All Time)", '%s/best' % base_url))
		self.genreliste.insert(0, ("Top Rated (Monthly)", '%s/best/monthly' % base_url))
		self.genreliste.insert(0, ("Top Rated (Weekly)", '%s/best/weekly' % base_url))
		self.genreliste.insert(0, ("Top Rated (Daily)", '%s/best/daily' % base_url))
		self.genreliste.insert(0, ("Newest", '%s' % base_url))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen(suggest_func=self.getSuggestions)
		elif Name == "Subscriptions":
			self.session.open(xhamsterSubscriptionsScreen, Name)
		elif Name == "Pornstars":
			self.session.open(xhamsterPornstarsScreen, Link, Name)
		elif Name == "Favourite Pornstars":
			self.session.open(xhamsterPornstarsScreen, Link, Name)
		else:
			if Link:
				self.session.open(xhamsterFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = '%s' % self.suchString.replace(' ', '+')
			self.session.open(xhamsterFilmScreen, Link, Name)

	def getSuggestions(self, text, max_res):
		url = "http://m.xhamster.com/ajax.php?act=search&q=%s" % urllib.quote_plus(text)
		d = twAgentGetPage(url, agent=xhAgent, headers={'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest'}, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, err=True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions:
				li = item["plainText"]
				list.append(str(li))
				max_res -= 1
				if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class xhamsterSubscriptionsScreen(MPScreen):

	def __init__(self, session, name):
		self.Name = name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keySubscribe,
		}, -1)

		self['title'] = Label("xHamster.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self.keyLocked = True
		self.subscribed = False

		self.streamList = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.pageData)

	def pageData(self):
		self.streamList = []
		self.keyLocked = True
		global subscriptions
		for m in subscriptions:
			url = "https://xhamster.com/users/%s/videos" % m[0]
			self.streamList.append((m[1], None, url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No subscriptions found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Link = self['liste'].getCurrent()[0][2]
		if Link:
			getPage(Link, agent=xhAgent, cookies=ck).addCallback(self.showInfos2).addErrback(self.dataError)

	def dataError(self, error):
		self.showInfos2("error")

	def showInfos2(self, data):
		if data == "error":
			CoverHelper(self['coverArt']).getCover(default_cover)
			self['handlung'].setText("User not found")
			url = self['liste'].getCurrent()[0][2]
			self.username = ((url.split('/')[-2], ""),)
			global subscriptions
			found = False
			for t in subscriptions:
				if t[0] == self.username[0][0]:
					submsg = "\nUser: " + self.username[0][1]
					self['F1'].setText(_("Unsubscribe"))
					self.subscribed = True
					found = True
		else:
			self.username = re.findall('class="user-name.*?href="https://xhamster.com/users/(.*?)".*? class="value">(.*?)</a', data, re.S)
			title = self['liste'].getCurrent()[0][0]
			pic = re.findall('class="xh-avatar largest" src="(.*?)"', data, re.S)
			if pic:
				import requests
				try:
					r = requests.head(pic[0], timeout=15)
					size = int(r.headers['content-length'])
				except:
					size = 100000
				if size < 100000:
					pic = pic[0]
				else:
					pic = "https://static-ec.xhcdn.com/xh-tpl3/images/favicon/apple-touch-icon.png"
			else:
				pic = "https://static-ec.xhcdn.com/xh-tpl3/images/favicon/apple-touch-icon.png"
			self['name'].setText(title)
			global subscriptions
			found = False
			for t in subscriptions:
				if t[0] == self.username[0][0]:
					submsg = "\nUser: " + self.username[0][1]
					self['F1'].setText(_("Unsubscribe"))
					self.subscribed = True
					found = True
			if not found:
				submsg = "\nUser: " + self.username[0][1]
				self['F1'].setText(_("Subscribe"))
				self.subscribed = False
			self['handlung'].setText(submsg.strip('\n'))
			CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][2]
		if Link:
			self.session.open(xhamsterFilmScreen, Link, Name)

	def keySubscribe(self):
		Link = self['liste'].getCurrent()[0][2]
		if self.keyLocked:
			return
		if not Link:
			return
		self.keyLocked = True
		global subscriptions
		if self.subscribed:
			sub_tmp = []
			for t in subscriptions:
				if t[0] == self.username[0][0]:
					continue
				else:
					sub_tmp.append(((t[0], t[1])))
			subscriptions = sub_tmp
		else:
			subscriptions.insert(0, ((self.username[0][0], self.username[0][1])))
		self.pageData()
		writeFavSub()
		self.keyLocked = False

class xhamsterPornstarsScreen(MPScreen):

	def __init__(self, session, link, name):
		self.Link = link
		self.Name = name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"red" : self.keySubscribe,
		}, -1)

		self['title'] = Label("xHamster.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self.keyLocked = True
		self.subscribed = False

		self.streamList = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.streamList = []
		self.keyLocked = True
		if self.Link == "stars":
			self['Page'].setText('')
			self.pageData('')
		else:
			url = self.Link
			getPage(url, agent=xhAgent, cookies=ck).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		if self.Link == "stars":
			for m in pornstars:
				self.streamList.append((m[1], m[0]))
		else:
			stars = re.findall('class="item">.*?href=".*?/pornstars/(?!all/)(.*?)"\s{0,2}>(.*?)</a', data, re.S)
			for (url, name) in stars:
				self.streamList.append((name.strip(), url))
		if len(self.streamList) == 0:
			self.streamList.append((_('No pornstars found!'), None))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Link = self['liste'].getCurrent()[0][1]
		if Link:
			url = "https://xhamster.com/pornstars/" + Link
			getPage(url, agent=xhAgent, cookies=ck).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		self.username = [(self['liste'].getCurrent()[0][1], self['liste'].getCurrent()[0][0])]
		pic = re.findall('class="thumb-image-container__image" src="(.*?)"', data, re.S)
		if pic:
			get_random = random.randint(0, len(pic)-1)
			pic = pic[get_random]
		else:
			pic = None
		self['name'].setText(self.username[0][1])
		global pornstars
		found = False
		for t in pornstars:
			if t[0] == self.username[0][0]:
				if self.Link == "stars":
					starmsg = ""
				else:
					starmsg = "Favourite"
				self['F1'].setText(_("Unsubscribe"))
				self.subscribed = True
				found = True
		if not found:
			starmsg = ""
			Link = self['liste'].getCurrent()[0][1]
			if Link:
				self['F1'].setText(_("Subscribe"))
			else:
				self['F1'].setText('')
			self.subscribed = False
		self['handlung'].setText(starmsg.strip('\n'))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Link:
			url = "https://xhamster.com/pornstars/" + Link
			self.session.open(xhamsterFilmScreen, url, Name)

	def keySubscribe(self):
		Link = self['liste'].getCurrent()[0][1]
		if self.keyLocked:
			return
		if not Link:
			return
		self.keyLocked = True
		global pornstars
		if self.subscribed:
			star_tmp = []
			for t in pornstars:
				if t[0] == self.username[0][0]:
					continue
				else:
					star_tmp.append(((t[0], t[1])))
			pornstars = star_tmp
		else:
			pornstars.insert(0, ((self.username[0][0], self.username[0][1])))
		self.layoutFinished()
		writeFavSub()
		self.keyLocked = False

class xhamsterFilmScreen(MPScreen, ThumbsHelper):

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
			"menu" : self.keyMenu,
			"red" : self.keySubscribe,
			"green" : self.keyPageNumber,
			"yellow" : self.keyRelated,
			"blue" : self.keyFavourite
		}, -1)

		self['title'] = Label("xHamster.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Show Related"))
		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.hd = False
		self.favourited = False
		self.subscribed = False
		self.username = ""
		self.videoId = ""
		self.reload = False
		self.streamList = []

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self.keyLocked = True
		if self.Link == "favs":
			self['Page'].setText('')
			self.pageData('')
		else:
			self['name'].setText(_('Please wait...'))
			if re.match(".*?Search", self.Name):
				if self.hd:
					hd = "hd"
				else:
					hd = "all"
				url = "https://xhamster.com/search?date=any&duration=any&sort=relevance&quality=%s&categories=MjM6ODoRrDU=&q=%s&p=%s" % (hd, self.Link, str(self.page))
			else:
				if re.match('.*?\/channels\/', self.Link):
					url = "%s-%s.html" % (self.Link, str(self.page))
					if self.hd:
						url = url.replace('/new-', '/hd-')
				elif re.match('.*?\/rankings\/', self.Link):
					url = "%s-%s.html" % (self.Link, str(self.page))
				elif re.match('.*?\/new\/', self.Link):
					if self.page == 1:
						url = base_url
					else:
						url = "%s%s.html" % (self.Link, str(self.page))
				elif self.Name == "Related":
					url = self.Link + str(self.page)
				else:
					if self.hd:
						hd = '/hd'
					else:
						hd = ''
					if self.page == 1:
						url = "%s%s" % (self.Link, hd)
					else:
						url = "%s%s/%s" % (self.Link, hd, str(self.page))
			getPage(url, agent=xhAgent, cookies=ck).addCallback(self.pageData).addErrback(self.dataError)

	def pageData(self, data):
		if self.Link == "favs":
			for m in favourites:
				url = "https://xhamster.com/movies/" + m[0]
				self.streamList.append((m[1], None, url, "", "", ""))
		else:
			self.getLastPage(data, 'class="pager-section"(.*?)</div>')
			if 'video-thumb__date-added' in data:
				parse = re.search('video-thumb__date-added(.*?)</html>', data, re.S)
			else:
				parse = re.search('class="iframe-container(.*?)</html>', data, re.S)
				if not parse:
					parse = re.search('class="category-title"(.*?)</html>', data, re.S)
					if not parse:
						parse = re.search('Video Search Results</h1>(.*?)</html>', data, re.S)
			if parse:
				Liste = re.findall('class="thumb-container"\sdata-href="(.*?)"\sdata-thumb="(.*?)".*?class="duration">(.*?)</div>.*?class="name">(.*?)</div>.*?class="views">(.*?)</div>.*?class="rating">(.*?)</div>', parse.group(1), re.S)
				if not Liste:
					Liste = re.findall('class="video-thumb__image-container.*?href="(.*?)".*?image-container__image"\ssrc="(.*?)".*?container__duration">(.*?)</div>.*?video-thumb-info__name.*?>(.*?)</a>.*?thumb-info__views.*?>(.*?)</i>.*?thumb-info__rating.*?>(.*?)</i>', parse.group(1), re.S)
				if Liste:
					for (Link, Image, Runtime, Name, Views, Rating) in Liste:
						Name = stripAllTags(Name).strip()
						Views = stripAllTags(Views).strip().replace(',','')
						Rating = stripAllTags(Rating).strip()
						self.streamList.append((decodeHtml(Name), Image, Link, Runtime, Views, Rating))
			else:
				Liste = re.findall('"duration":(\d+),"title":"(.*?)","pageURL":"(.*?)".*?ratingModel","value":(\d+).*?videoModel","thumbURL":"(.*?)".*?views":(\d+),', data, re.S)
				if Liste:
					for (Runtime, Name, Link, Rating, Image, Views) in Liste:
						Link = Link.replace('\/','/')
						Image = Image.replace('\/','/')
						Rating = Rating + "%"
						m, s = divmod(int(Runtime), 60)
						Runtime = "%02d:%02d" % (m, s)
						self.streamList.append((decodeHtml(Name), Image, Link, Runtime, Views, Rating))
		if len(self.streamList) == 0:
			self.streamList.append((_('No videos found!'), None, None, '', '', ''))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		if not self.reload:
			self.ml.moveToIndex(0)
		self.reload = False
		self.keyLocked = False
		if self.Link == "favs":
			self.th_ThumbsQuery(self.streamList, 0, 2, None, None, 'itemprop="thumbnailUrl" href="(.*?)">', 1, 1, mode=1)
		else:
			self.th_ThumbsQuery(self.streamList, 0, 2, 1, 3, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		Link = self['liste'].getCurrent()[0][2]
		if Link:
			getPage(Link, agent=xhAgent, cookies=ck).addCallback(self.showInfos2).addErrback(self.dataError)

	def dataError(self, error):
		self.showInfos2("error")

	def showInfos2(self, data):
		if data == "error":
			CoverHelper(self['coverArt']).getCover(default_cover)
			self['handlung'].setText("Video not found")
			self['F1'].setText("")
			self['F2'].setText("")
			self['F3'].setText("")
			url = self['liste'].getCurrent()[0][2]
			self.videoId = url.split('/')[-1]
			global favourites
			for t in favourites:
				if t[0] == self.videoId:
					favmsg = "\nFavourited"
					self.favourited = True
					self['F4'].setText(_("Remove Favourite"))
					found = True
		else:
			if self.Link == "favs":
				self['F2'].setText("")
			else:
				self['F2'].setText(_("Page"))
			self['F3'].setText(_("Show Related"))
			self.videoId = re.findall('"videoId":(\d+),', data, re.S)[0]
			self.username = re.findall('"entity-author-container__name(?: link|)" (?:href="https://xhamster.com/users/(.*?)"\s|data-tooltip="User is retired").*?itemprop="name">(.*?)</span', data, re.S)
			title = self['liste'].getCurrent()[0][0]
			if self.Link == "favs":
				pic = re.findall('itemprop="thumbnailUrl" href="(.*?)">', data, re.S)[0]
			else:
				pic = self['liste'].getCurrent()[0][1]
			runtime = self['liste'].getCurrent()[0][3]
			views = self['liste'].getCurrent()[0][4]
			rating = self['liste'].getCurrent()[0][5]
			self['name'].setText(title)
			found = False
			global subscriptions
			for t in subscriptions:
				if self.username[0][0]:
					if t[0] == self.username[0][0]:
						submsg = "\nUser: " + self.username[0][1] + " - Subscribed"
						self['F1'].setText(_("Unsubscribe"))
						self.subscribed = True
						found = True
			if not found:
				if self.username[0][0]:
					submsg = "\nUser: " + self.username[0][1]
					self['F1'].setText(_("Subscribe"))
				else:
					submsg = "\nUser: " + self.username[0][1] + " (retired)"
					self['F1'].setText('')
				self.subscribed = False
			found = False
			global favourites
			for t in favourites:
				if t[0] == self.videoId:
					favmsg = "\nFavourited"
					self.favourited = True
					self['F4'].setText(_("Remove Favourite"))
					found = True
			if not found:
				favmsg = ""
				self['F4'].setText(_("Add Favourite"))
				self.favourited = False
			if self.Link == "favs":
				self['handlung'].setText(submsg.strip('\n'))
			else:
				self['handlung'].setText("Runtime: %s\nViews: %s\nRating: %s%s%s" % (runtime, views, rating, submsg, favmsg))
			CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][2]
		self.keyLocked = True
		if Link:
			getPage(Link, agent=xhAgent, cookies=ck).addCallback(self.playerData).addErrback(self.dataError)

	def keyMenu(self):
		if self.keyLocked:
			return
		if re.match('.*?\/rankings\/', self.Link):
			return
		elif re.match('.*?\/new\/', self.Link):
			return
		elif self.Name == "Related":
			return
		elif self.Link == "favs":
			return
		rangelist = [['All Videos', False], ['Only HD', True]]
		self.session.openWithCallback(self.keyMenuAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keyMenuAction(self, result):
		if result:
			self.hd = result[1]
			self.loadPage()

	def keySubscribe(self):
		Link = self['liste'].getCurrent()[0][2]
		if self.keyLocked:
			return
		if not Link:
			return
		self.keyLocked = True
		global subscriptions
		if self.subscribed:
			sub_tmp = []
			for t in subscriptions:
				if self.username[0][0]:
					if t[0] == self.username[0][0]:
						continue
					else:
						sub_tmp.append(((t[0], t[1])))
			subscriptions = sub_tmp
		else:
			if self.username[0][0]:
				subscriptions.insert(0, ((self.username[0][0], self.username[0][1])))
		self.showInfos()
		writeFavSub()
		self.keyLocked = False

	def keyRelated(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][2]
		self.keyLocked = True
		if Link:
			getPage(Link, agent=xhAgent, cookies=ck).addCallback(self.getRelated).addErrback(self.dataError)

	def keyFavourite(self):
		Link = self['liste'].getCurrent()[0][2]
		if self.keyLocked:
			return
		if not Link:
			return
		self.keyLocked = True
		global favourites
		if self.favourited:
			fav_tmp = []
			for t in favourites:
				if t[0] == self.videoId:
					continue
				else:
					fav_tmp.append(((t[0], t[1])))
			favourites = fav_tmp
		else:
			if self.videoId != "":
				title = self['liste'].getCurrent()[0][0]
				favourites.insert(0, (self.videoId, title))
		if self.Link == "favs":
			self.reload = True
			self.loadPage()
		else:
			self.showInfos()
		writeFavSub()
		self.keyLocked = False

	def getRelated(self, data):
		self.keyLocked = False
		parse = re.findall('&amp;q=(.*?)">\s+Show all', data, re.S)
		RelatedUrl = 'https://xhamster.com/search?q=%s&p=' % parse[0]
		self.session.open(xhamsterFilmScreen, RelatedUrl, "Related")

	def playerData(self, data):
		playerData = re.findall('itemprop="embedUrl" href="(.*?)">', data, re.S)
		if playerData:
			getPage(playerData[0], agent=xhAgent, cookies=ck).addCallback(self.playUrl).addErrback(self.dataError)

	def playUrl(self, data):
		Title = self['liste'].getCurrent()[0][0]
		playUrl = re.findall('"\d+p":"(.*?)"', data, re.S)
		if playUrl:
			self.keyLocked = False
			self.session.open(SimplePlayer, [(Title, playUrl[-1].replace('&amp;','&').replace('\/','/'))], showPlaylist=False, ltype='xhamster')