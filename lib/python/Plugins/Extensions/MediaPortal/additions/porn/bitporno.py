# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

myagent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'
default_cover = "file://%s/bitporno.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
base_url = "https://bitporno.com"

class bitpornoGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
		}, -1)

		self['title'] = Label("BITPORNO.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		url = base_url + "/?q="
		twAgentGetPage(url, agent=myagent, timeout=60).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('Categories</span><br(.*?)</div', data, re.S)
		if parse:
			Cats = re.findall('href="(.*?)">(.*?)<', parse.group(1), re.S)
			if Cats:
				for (Url, Title) in Cats:
					Url = base_url + Url.replace('&amp;','&') + "&page="
					self.genreliste.append((Title, Url))
		self.genreliste.sort()
		self.genreliste.insert(0, ("Most Viewed", base_url + "/?q=&cat=&sort=mostviewed&time=someday&length=all&user=&page="))
		self.genreliste.insert(0, ("Past", base_url + "/?q=&cat=&sort=oldest&time=past&length=all&user=&page="))
		self.genreliste.insert(0, ("This Year", base_url + "/?q=&cat=&sort=oldest&time=tyear&length=all&user=&page="))
		self.genreliste.insert(0, ("This Month", base_url + "/?q=&cat=&sort=oldest&time=tmonth&length=all&user=&page="))
		self.genreliste.insert(0, ("This Week", base_url + "/?q=&cat=&sort=oldest&time=tweek&length=all&user=&page="))
		self.genreliste.insert(0, ("Today", base_url + "/?q=&cat=&sort=oldest&time=today&length=all&user=&page="))
		self.genreliste.insert(0, ("Newest", base_url + "/?q=&cat=&sort=recent&time=someday&length=all&user=&page="))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", default_cover))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback.replace(' ', '+')
			Name = "--- Search ---"
			Link = '%s' % (self.suchString)
			self.session.open(bitpornoFilmScreen, Link, Name)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		if Name == "--- Search ---":
			self.suchen()
		else:
			Link = self['liste'].getCurrent()[0][1]
			self.session.open(bitpornoFilmScreen, Link, Name)

class bitpornoFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label("BITPORNO.com")
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
			url = base_url + "/?q=%s&or=&cat=&sort=recent&time=someday&length=all&view=0&page=%s&user=" % (self.Link, str(self.page-1))
		else:
			url = self.Link + str(self.page-1)
		twAgentGetPage(url, agent=myagent, timeout=60).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, '', '.*class="pages">\s+(\d+)</a>')
		Movies = re.findall('class="entry.*?href="(.*?)".*?img\ssrc="(.*?)".*?(<div.*?)</div.*?<a href="\/\?c=user\&amp;id=(.*?)"', data, re.S)
		if Movies:
			for (Url, Image, Title, User) in Movies:
				if "bitporno" in Image:
					continue
				stop = False
				filetype = ['.wmv', '.avi', '.mpeg', '.mpg', '.mov']
				for x in filetype:
					if Title.lower().endswith(x):
						stop = True
				if stop:
					continue

				if re.search('(\d{3}-\d{10})', Title):
					stop = True
				if re.search('(\d{3}-\d{1}-\d{10})', Title):
					stop = True
				if re.search('(\d{3}-\d{1,2}-\d{1}-\d{10})', Title):
					stop = True
				if re.search('(\d{3}-\d{1,2}-\d{1}-\d{1}-\d{10})', Title):
					stop = True
				if stop:
					continue

				blacklist = [	'misaanime', 'shiryutetsu', 'shootgamez', 'wsadzxop011', 'peerapat24373', 'inzpistudio', 'zicozico', 'Fuck66666', 'nyc646dude' ]
				for x in blacklist:
					if x.lower() == User.lower():
						stop = True
				if stop:
					continue

				blacklist = [	'dagashi-kashi', 'mahoutsukai-no-yome', 'ryuuou-no-oshigoto', 'b-gata-h-kei', 'misa-anime', 'sword-art-online',
						'super dragon ball heroes', 'ito-junji', 'kakuriyo no yadomeshi', 'fate-apocrypha', 'aldnoah-zero', 'dies-irae',
						'ao-no-exorcist', 'boruto-naruto', 'akiba-rsquo', 'ai-mai-mii-surgical', 'darling-in-the-franxx', 'beelzebub',
						'uma-musume', 'high-school-dxd', 'saiki-kusuo', 'fatestay-night', 'fate-stay-night', 'boku-no-hero', 'fate-extra-last-encore',
						'akkun-to-kanojo', 'alice-or-alice', '3d-kanojo-real-girl', 'toji-no-miko', 'one-piece', 'comic-girls', 'tada-kun-wa',
						'druaga-no-to', 'detective-conan', 'kekkai-sensen', 'jigoku-shoujo', 'kino-no-tabi', 'kujra-no-kora', 'myreadyweb.com',
						'imouto-sae-ireba', 'himouto-umaru', 'hand-shakers', 'little-witch-academia', 'kujira-no-kora', 'touken-ranbu-hanamaru', 'tonagura',
						'saiki kusuo no psi', 'tsurezure-children', 'udon-no-kuni-no', 'true-tears', 'tsukiuta-the-animation', 'trinityseven-', 'triage-x-',
						'tonari-no-kaibutsu', 'animerawrip', 'fall-year-princess', 'sirius the jaeger', 'otatu-anime-senyuu', 'zenzen-suki-jenain',
						'satsuriku-no-tenshi', 'mahouka koukou no rettousei', 'dame-x-prince' ]
				for x in blacklist:
					if x.lower() in Title.lower():
						stop = True
				if stop:
					continue
				Title = stripAllTags(Title).replace('.mp4','').replace('.MP4','').replace('.mkv','').replace('.MKV','').replace('.m4v','').replace('.M4V','').strip('-')
				Url = base_url + Url
				self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No playable movies found, try next page!'), None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		pic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			self.keyLocked = True
			twAgentGetPage(url, agent=myagent, timeout=60).addCallback(self.loadStream).addErrback(self.dataError)

	def loadStream(self, data):
		stream_url = re.findall('source\ssrc="(.*?\.mp4)"\stype="video/mp4"', data, re.S)
		self.keyLocked = False
		if stream_url:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(title, stream_url[-1])], showPlaylist=False, ltype='bitporno')