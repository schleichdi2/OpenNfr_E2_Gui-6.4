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
from Plugins.Extensions.MediaPortal.resources.decrypt import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
json_headers = {
	'Accept':'application/json',
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/x-www-form-urlencoded',
	}
default_cover = "file://%s/porncom.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class porncomGenreScreen(MPScreen):

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

		self['title'] = Label("Porn.com")
		self['ContentTitle'] = Label("Genre:")
		self.keyLocked = True
		self.suchString = ''

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self.url = "https://www.porn.com/categories"
		getPage(self.url, agent=agent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		dupelist = []
		Cats = re.findall('class="thumb"><a href="(.*?)"\stitle=".*?<img src="(.*?)".*?></a></div><h3><a href=".*?>(.*?)</a>', data, re.S)
		if Cats:
			for (Url, Image, Title) in Cats:
				Url = "https://www.porn.com" + Url + "?p="
				dupelist.append(Title)
				self.filmliste.append((Title, Url, Image, True))
		Cats2 = re.findall('class="flex"><a href="(.*?)">(.*?)</a>', data, re.S)
		if Cats2:
			for (Url, Title) in Cats2:
				if Title not in dupelist:
					Url = "https://www.porn.com" + Url + "?p="
					self.filmliste.append((Title, Url, default_cover, True))
		self.filmliste.sort()
		self.filmliste.insert(0, ("HD", "https://www.porn.com/videos/hd?p=", default_cover, True))
		self.filmliste.insert(0, ("Playlists", "https://www.porn.com/playlists?p=", default_cover, True))
		self.filmliste.insert(0, ("Channels", "https://www.porn.com/channels?p=", default_cover, True))
		self.filmliste.insert(0, ("Pornstars", "https://www.porn.com/pornstars?p=", default_cover, True))
		self.filmliste.insert(0, ("Longest", "https://www.porn.com/videos?o=l$$AGE$$&p=", default_cover, False))
		self.filmliste.insert(0, ("Most Discussed", "https://www.porn.com/videos?o=m$$AGE$$&p=", default_cover, False))
		self.filmliste.insert(0, ("Top Rated", "https://www.porn.com/videos?o=r$$AGE$$&p=", default_cover, False))
		self.filmliste.insert(0, ("Most Viewed", "https://www.porn.com/videos?o=v$$AGE$$&p=", default_cover, False))
		self.filmliste.insert(0, ("Most Popular", "https://www.porn.com/videos?o=f$$AGE$$&p=", default_cover, False))
		self.filmliste.insert(0, ("Featured", "https://www.porn.com/videos?p=", default_cover, False))
		self.filmliste.insert(0, ("Newest", "https://www.porn.com/videos?o=d&p=", default_cover, False))
		self.filmliste.insert(0, ("--- Search ---", "callSuchen", default_cover, True))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		cover = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(cover)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		Sort = self['liste'].getCurrent()[0][3]
		if Name == "--- Search ---":
			self.suchen(suggest_func=self.getSuggestions)
		elif Name == "Channels":
			self.session.open(porncomChannelsScreen, Link, Name, Sort)
		elif Name == "Playlists":
			self.session.open(porncomPlaylistsScreen, Link, Name, Sort)
		elif Name == "Pornstars":
			self.session.open(porncomPornstarsScreen, Link, Name, Sort)
		else:
			self.session.open(porncomFilmScreen, Link, Name, Sort)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "--- Search ---"
			self.suchString = callback
			Link = self.suchString.replace(' ', '+')
			self.session.open(porncomFilmScreen, Link, Name, True)

	def getSuggestions(self, text, max_res):
		url = "https://www.porn.com/search/suggest.json"
		postdata = {'type': "v", 'q': text}
		d = twAgentGetPage(url, method='POST', postdata=urlencode(postdata), agent=agent, headers=json_headers, timeout=5)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, err=True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		list = []
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions:
				if not item.has_key('separator'):
					li = item['label']
					list.append(str(li))
					max_res -= 1
					if not max_res: break
		elif err:
			printl(str(suggestions),self,'E')
		return list

class porncomPornstarsScreen(MPScreen, ThumbsHelper):

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
			"yellow" : self.keySort,
			"blue" : self.keyAge
		}, -1)

		self['title'] = Label("Porn.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Sort"))
		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.sort = 't'
		self.sortname = 'Top Trending'
		self.age = ''
		self.agename = 'All Time'

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s%s&o=%s$$AGE$$" % (self.Link, str(self.page), self.sort)
		if self.sortname != 'Top Trending' and self.sortname != 'Alphabetical' and self.sortname != 'Number of videos':
			age = '$$AGE$$'
		else:
			age = ''
		url = url.replace('$$AGE$$', self.age)
		getPage(url, agent=agent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		lastp = re.search('<span>\((?:<span>|)(\d+.*?)(?:</span>|) pornstars\)', data, re.S)
		if lastp:
			lastp = lastp.group(1).replace(',','')
			lastp = round((float(lastp) / 24) + 0.5)
			self.lastpage = int(lastp)
			if self.lastpage > 50 and self.sortname != 'Alphabetical':
				self.lastpage = 50
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self.lastpage = 999
			self['page'].setText(str(self.page))
		Movies = re.findall('class="thumb"><a href="(.*?)">.*?<img src="(.*?)" alt=".*?</a></div><h3><a href=".*?>(.*?)</a>.*?<div class="meta">(.*?)</div>', data, re.S)
		if Movies:
			for (Url, Image, Title, Meta) in Movies:
				Videos = re.findall('<p>(\d.*?)\s<span>Videos</span></p>', Meta, re.S)
				if Videos:
					Videos = Videos[0].replace('.','')
				else:
					Videos = "-"
				Url = "https://www.porn.com" + Url + "?p="
				self.filmliste.append((decodeHtml(Title), Url, Image, Videos))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No pornstars found!'), "", None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def keySort(self):
		if self.keyLocked:
			return
		if not self.Sort:
			return
		rangelist = [ ['Top Trending', 't'], ['Most Popular', 'f'], ['Most Viewed', 'v'], ['Alphabetical', 'n'], ['Number of videos', 'c'] ]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sortname = result[0]
			self.loadPage()
		if self.sortname != 'Top Trending' and self.sortname != 'Alphabetical' and self.sortname != 'Number of videos':
			self['F4'].setText(_("Filter"))
		else:
			self['F4'].setText('')
			self.age = ''
			self.agename = 'All Time'

	def keyAge(self):
		if self.keyLocked:
			return
		if self.Sort and (self.sortname == 'Top Trending' or self.sortname == 'Alphabetical' or self.sortname == 'Number of videos'):
			return
		rangelist = [ ['Today', '1'], ['This Week', '7'], ['This Month', '30'], ['All Time', ''] ]
		self.session.openWithCallback(self.keyAgeAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keyAgeAction(self, result):
		if result:
			self.age = result[1]
			self.agename = result[0]
			self.loadPage()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		videos = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		if self.Sort:
			sort = self.sortname
		else:
			sort = self.Name
		self['handlung'].setText("Videos: %s\n%s: %s\n%s: %s" % (videos, _("Sort order"), sort, _("Filter"), self.agename))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(porncomFilmScreen, Link, Name, True)

class porncomChannelsScreen(MPScreen, ThumbsHelper):

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
			"yellow" : self.keySort,
			"blue" : self.keyAge
		}, -1)

		self['title'] = Label("Porn.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Sort"))
		self['F4'].setText(_("Filter"))
		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.sort = 'f'
		self.sortname = 'Most Popular'
		self.age = '7'
		self.agename = 'This Week'

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s%s&o=%s$$AGE$$" % (self.Link, str(self.page), self.sort)
		if self.sortname != 'Newest':
			age = '$$AGE$$'
		else:
			age = ''
		url = url.replace('$$AGE$$', self.age)
		getPage(url, agent=agent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		lastp = re.search('<span>\((?:<span>|)(\d+.*?)(?:</span>|) channels\)', data, re.S)
		if lastp:
			lastp = lastp.group(1).replace(',','')
			lastp = round((float(lastp) / 32) + 0.5)
			self.lastpage = int(lastp)
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self.lastpage = 999
			self['page'].setText(str(self.page))
		Movies = re.findall('class="thumb"><a href="(.*?)">.*?<img src=".*?<img src="(.*?)" alt=".*?</a></div><h3><a href=".*?>(.*?)</a>.*?<div class="meta">(.*?)</div>', data, re.S)
		if Movies:
			for (Url, Image, Title, Meta) in Movies:
				Videos = re.findall('<p>(\d.*?)\s<span>Videos</span></p>', Meta, re.S)
				if Videos:
					Videos = Videos[0].replace('.','')
				else:
					Videos = "-"
				Url = "https://www.porn.com" + Url + "?p="
				self.filmliste.append((decodeHtml(Title), Url, Image, Videos))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No channels found!'), "", None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=0)
		self.showInfos()

	def keySort(self):
		if self.keyLocked:
			return
		if not self.Sort:
			return
		rangelist = [ ['Newest', 'd'], ['Most Popular', 'f'], ['Most Viewed', 'v'] ]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sortname = result[0]
			self.loadPage()
		if self.sortname != 'Newest':
			self['F4'].setText(_("Filter"))
		else:
			self['F4'].setText('')
			self.age = ''
			self.agename = 'All Time'

	def keyAge(self):
		if self.keyLocked:
			return
		if self.Sort and self.sortname == 'Newest':
			return
		rangelist = [ ['Today', '1'], ['This Week', '7'], ['This Month', '30'], ['All Time', ''] ]
		self.session.openWithCallback(self.keyAgeAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keyAgeAction(self, result):
		if result:
			self.age = result[1]
			self.agename = result[0]
			self.loadPage()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		videos = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		if self.Sort:
			sort = self.sortname
		else:
			sort = self.Name
		self['handlung'].setText("Videos: %s\n%s: %s\n%s: %s" % (videos, _("Sort order"), sort, _("Filter"), self.agename))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(porncomFilmScreen, Link, Name, True)

class porncomPlaylistsScreen(MPScreen, ThumbsHelper):

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
			"yellow" : self.keySort,
			"blue" : self.keyAge
		}, -1)

		self['title'] = Label("Porn.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		self['F3'] = Label(_("Sort"))
		self['F4'].setText(_("Filter"))
		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self.sort = 'f'
		self.sortname = 'Most Popular'
		self.age = '7'
		self.agename = 'This Week'

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s%s&o=%s$$AGE$$" % (self.Link, str(self.page), self.sort)
		if self.sortname != 'Newest' and self.sortname != 'Number of videos':
			age = '$$AGE$$'
		else:
			age = ''
		url = url.replace('$$AGE$$', self.age)
		getPage(url, agent=agent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		lastp = re.search('<span>\((?:<span>|)(\d+.*?)(?:</span>|) user playlists\)', data, re.S)
		if lastp:
			lastp = lastp.group(1).replace(',','')
			lastp = round((float(lastp) / 25) + 0.5)
			self.lastpage = int(lastp)
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			self.lastpage = 999
			self['page'].setText(str(self.page))
		Movies = re.findall('class="thumb">.*?<img src="(.*?)"\salt="(.*?)".*?Play all</a><a href="(.*?)">.*?<div class="meta">(.*?)</div>', data, re.S)
		if Movies:
			for (Image, Title, Url, Meta) in Movies:
				Videos = re.findall('<p><span>(\d.*?)\sVideos</span></p>', Meta, re.S)
				if Videos:
					Videos = Videos[0].replace('.','')
				else:
					Videos = "-"
				Url = "https://www.porn.com" + Url + "?p="
				self.filmliste.append((decodeHtml(Title), Url, Image, Videos))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No playlists found!'), "", None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def keySort(self):
		if self.keyLocked:
			return
		if not self.Sort:
			return
		rangelist = [ ['Newest', 'd'], ['Top Rated', 'r'], ['Most Popular', 'f'], ['Most Viewed', 'v'], ['Number of videos', 'c'] ]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sortname = result[0]
			self.loadPage()
		if self.sortname != 'Newest' and self.sortname != 'Number of videos':
			self['F4'].setText(_("Filter"))
		else:
			self['F4'].setText('')
			self.age = ''
			self.agename = 'All Time'

	def keyAge(self):
		if self.keyLocked:
			return
		if self.Sort and (self.sortname == 'Newest' or self.sortname == 'Number of videos'):
			return
		rangelist = [ ['Today', '1'], ['This Week', '7'], ['This Month', '30'], ['All Time', ''] ]
		self.session.openWithCallback(self.keyAgeAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keyAgeAction(self, result):
		if result:
			self.age = result[1]
			self.agename = result[0]
			self.loadPage()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		videos = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		if self.Sort:
			sort = self.sortname
		else:
			sort = self.Name
		self['handlung'].setText("Videos: %s\n%s: %s\n%s: %s" % (videos, _("Sort order"), sort, _("Filter"), self.agename))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(porncomFilmScreen, Link, Name, True)

class porncomFilmScreen(MPScreen, ThumbsHelper):

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
			"yellow" : self.keySort,
			"blue" : self.keyAge
		}, -1)

		self['title'] = Label("Porn.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))
		if self.Sort:
			self['F3'] = Label(_("Sort"))
		if not self.Sort and self.Name != 'Newest':
			self['F4'].setText(_("Filter"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		if re.match(".*Search", self.Name):
			self.sortname = 'Most Relevant'
			self.sort = ''
		else:
			self.sortname = 'Newest'
			self.sort = 'd'
		self.age = ''
		self.agename = 'All Time'

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*Search", self.Name):
			if self.sortname != 'Most Relevant' and self.sortname != 'Newest':
				age = '$$AGE$$'
			else:
				age = ''
			url = "https://www.porn.com/videos/search?q=%s&p=%s&o=%s%s" % (self.Link, str(self.page), self.sort, age)
		else:
			url = "%s%s" % (self.Link, str(self.page))
			if self.Sort:
				url = "%s&o=%s$$AGE$$" % (url, self.sort)
			if self.sortname != 'Newest':
				age = '$$AGE$$'
			else:
				age = ''
		url = url.replace('$$AGE$$', self.age)
		getPage(url, agent=agent).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		lastp = re.search('<span>\((?:<span>|)(\d+.*?)(?:</span>|) (?:results|videos)\)', data, re.S)
		if lastp:
			lastp = lastp.group(1).replace(',','')
			lastp = round((float(lastp) / 41) + 0.5)
			self.lastpage = int(lastp)
			if self.lastpage > 244 and re.match(".*Search", self.Name):
				self.lastpage = 244
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		else:
			lastp = re.search('Videos:</span><span>(.*?)</span>', data, re.S)
			if lastp:
				lastp = lastp.group(1).replace(',','')
				lastp = round((float(lastp) / 201) + 0.5)
				self.lastpage = int(lastp)
				self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
			else:
				self.lastpage = 999
				self['page'].setText(str(self.page))
		Movies = re.findall('class="thumb"><a href="(.*?)"\stitle=".*?<img src="(.*?)".*?></a></div><h3><a href=".*?>(.*?)</a>.*?<div class="meta">(.*?)</div>', data, re.S)
		if Movies:
			for (Url, Image, Title, Meta) in Movies:
				Views = re.findall('<p>(\d.*?)\sviews</p>', Meta, re.S)
				if Views:
					Views = Views[0]
				else:
					Views = "0"
				Runtime = re.findall('<p><span>(\d+\smin)</span></p>', Meta, re.S)
				if Runtime:
					Runtime = Runtime[0]
				else:
					Runtime = "-"
				Url = "https://www.porn.com" + Url
				Image = Image.replace('/tags/', '/promo/crop/')
				Image = re.sub(r'/\d+.jpg', "/promo_15.jpg", Image)
				self.filmliste.append((decodeHtml(Title), Url, Image, Runtime, Views))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No movies found!'), "", None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def keySort(self):
		if self.keyLocked:
			return
		if not self.Sort:
			return
		if re.match(".*Search", self.Name):
			rangelist = [ ['Most Relevant', None], ['Newest', 'd'], ['Most Popular', 'f'], ['Most Viewed', 'v'], ['Top Rated', 'r'], ['Longest', 'l'] ]
		else:
			rangelist = [ ['Newest', 'd'], ['Most Popular', 'f'], ['Most Viewed', 'v'], ['Top Rated', 'r'], ['Most Discussed', 'm'], ['Longest', 'l'] ]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.sortname = result[0]
			self.loadPage()
		if self.sortname != 'Newest' and self.sortname != 'Most Relevant':
			self['F4'].setText(_("Filter"))
		else:
			self['F4'].setText('')
			self.age = ''
			self.agename = 'All Time'

	def keyAge(self):
		if self.keyLocked:
			return
		if self.Sort and (self.sortname == 'Newest' or self.sortname == 'Most Relevant'):
			return
		if not self.Sort and self.Name == 'Newest':
			return
		rangelist = [ ['Today', '1'], ['This Week', '7'], ['This Month', '30'], ['All Time', ''] ]
		self.session.openWithCallback(self.keyAgeAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keyAgeAction(self, result):
		if result:
			self.age = result[1]
			self.agename = result[0]
			self.loadPage()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		runtime = self['liste'].getCurrent()[0][3]
		views = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		if self.Sort:
			sort = self.sortname
		else:
			sort = self.Name
		self['handlung'].setText("Runtime: %s\nViews: %s\n%s: %s\n%s: %s" % (runtime, views, _("Sort order"), sort, _("Filter"), self.agename))
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		getPage(Link, agent=agent).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		Title = self['liste'].getCurrent()[0][0]
		match = re.findall('"\d+p",url:"(http.*?)"', data)
		if match:
			url = match[-1].replace('\/','/').replace('%2F','%252F').replace('%3D','%253D').replace('%2B','%252B')
			self.session.open(SimplePlayer, [(Title, url)], showPlaylist=False, ltype='porncom')
		else:
			message = self.session.open(MessageBoxExt, _("Stream not found"), MessageBoxExt.TYPE_INFO, timeout=5)