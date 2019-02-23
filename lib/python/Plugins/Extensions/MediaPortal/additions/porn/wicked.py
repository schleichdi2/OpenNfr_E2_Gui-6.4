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
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

myagent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0'
BASE_NAME = "WickedPictures.com"
default_cover = "file://%s/wickedpictures.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class wickedGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.suchString = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.insert(0, ("Exclusive Girls", 'http://www.wicked.com/tour/pornstars/exclusive/', None))
		self.genreliste.insert(0, ("Most Active Girls", 'http://www.wicked.com/tour/pornstars/mostactive/', None))
		self.genreliste.insert(0, ("Most Liked Girls", 'http://www.wicked.com/tour/pornstars/mostliked/', None))
		self.genreliste.insert(0, ("Most Recent Girls", 'http://www.wicked.com/tour/pornstars/mostrecent/', None))
		self.genreliste.insert(0, ("Most Viewed Movies", 'http://www.wicked.com/tour/movies/mostviewed/', None))
		self.genreliste.insert(0, ("Top Rated Movies", 'http://www.wicked.com/tour/movies/toprated/', None))
		self.genreliste.insert(0, ("Latest Movies", 'http://www.wicked.com/tour/movies/latest/', None))
		self.genreliste.insert(0, ("Most Viewed Scenes", 'http://www.wicked.com/tour/videos/mostviewed/', None))
		self.genreliste.insert(0, ("Top Rated Scenes", 'http://www.wicked.com/tour/videos/toprated/', None))
		self.genreliste.insert(0, ("Latest Scenes", 'http://www.wicked.com/tour/videos/latest/', None))
		self.genreliste.insert(0, ("--- Search ---", "callSuchen", None))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.showInfos()

	def keyOK(self):
		if not config_mp.mediaportal.premiumize_use.value:
			message = self.session.open(MessageBoxExt, _("%s only works with enabled MP premiumize.me option (MP Setup)!" % BASE_NAME), MessageBoxExt.TYPE_INFO, timeout=10)
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "--- Search ---":
			self.suchen()
		elif re.match(".*?Girls", Name):
			self.session.open(wickedGirlsScreen, Link, Name)
		else:
			self.session.open(wickedFilmScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			self.suchString = callback
			Name = "--- Search ---"
			Link = urllib.quote(self.suchString).replace(' ', '-')
			self.session.open(wickedFilmScreen, Link, Name)

class wickedGirlsScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label(BASE_NAME)
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
		url = "%s%s/" % (self.Link, str(self.page))
		getPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="paginationui-container(.*?)</ul>', '.*(?:\/|>)(\d+)')
		parse = re.search('class="showcase-models(.*?)</section>', data, re.S)
		Movies = re.findall('<a\shref="(.*?)"\sclass="showcase-models.*?img\ssrc="(.*?)"\stitle="(.*?)".*?scenes">(\d+)\sScenes', parse.group(1), re.S)
		if Movies:
			for (Url, Image, Title, Scenes) in Movies:
				Url = "http://www.wicked.com" + Url
				Title = Title + " - %s Scenes" % Scenes
				self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No pornstars found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, int(self.lastpage), mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		if Link:
			rangelist = [['Scenes', 'videos/'], ['Movies', 'movies/']]
			self.session.openWithCallback(self.keyOK2, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keyOK2(self, result):
		if result:
			Name = self['liste'].getCurrent()[0][0]
			Link = self['liste'].getCurrent()[0][1]
			Link = Link + result[1]
			self.session.open(wickedFilmScreen, Link, Name)

class wickedFilmScreen(MPScreen, ThumbsHelper):

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

		self['title'] = Label(BASE_NAME)
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 9

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if re.match(".*?Search", self.Name):
			url = "http://www.wicked.com/tour/search/videos/%s/%s/" % (self.Link, str(self.page))
		else:
			url = "%s%s/" % (self.Link, str(self.page))
		getPage(url, agent=myagent).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		if re.match(".*?Search", self.Name):
			self.getLastPage(data, 'class="paginationui-container(.*?)</ul>', '.*(?:\/|>)(\d+)')
		elif re.match(".*?/tour/pornstar", self.Link):
			self.getLastPage(data, 'class="paginationui-container(.*?)</ul>', '.*(?:\/|>)(\d+)')
		else:
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		parse = re.search('lass="showcase-movies">(.*?)</section>', data, re.S)
		if parse:
			Movies = re.findall('<a\shref="(.*?)"\sclass="showcase-movies.*?img\ssrc="(.*?)"\salt=".*?"\stitle="(.*?)"', parse.group(1), re.S)
		else:
			parse = re.search('class="showcase-scenes">(.*?)</section>', data, re.S)
			if parse:
				Movies = re.findall('<a\shref="(.*?)"\sclass="showcase-scenes.*?img\ssrc="(.*?)"\stitle=".*?"\salt="(.*?)"', parse.group(1), re.S)
		if Movies:
			for (Url, Image, Title) in Movies:
				Image = Image.replace('_2.jpg','_1.jpg')
				Url = "http://www.wicked.com" + Url
				self.filmliste.append((decodeHtml(Title), Url, Image))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), '', None, ''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, int(self.lastpage), mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][1]
		get_stream_link(self.session).check_link(Link, self.play)

	def play(self, url):
		title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(title, url.replace('%2F','%252F').replace('%3D','%253D').replace('%2B','%252B'))], showPlaylist=False, ltype='wicked')