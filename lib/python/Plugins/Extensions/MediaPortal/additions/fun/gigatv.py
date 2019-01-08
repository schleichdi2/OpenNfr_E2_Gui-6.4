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
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

default_cover = "file://%s/gigatv.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class gigatvGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
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
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("GIGA.de")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("G-Log","http://www.giga.de/games/videos/g-log/", "http://static.giga.de/wp-content/uploads/2012/12/g-log2-rcm239x151.jpg"))
		self.genreliste.append(("GIGA Games", "https://www.giga.de/games/videos/", default_cover))
		self.genreliste.append(("GIGA Tech","http://www.giga.de/tech/videos/", default_cover))
		self.genreliste.append(("GIGA Windows","http://www.giga.de/windows/videos/", default_cover))
		self.genreliste.append(("GIGA Android/Apple","http://www.giga.de/android/videos-podcasts/", default_cover))
		self.genreliste.append(("GIGA Failplays","http://www.giga.de/games/channel/giga-failplays/", "http://static.giga.de/wp-content/uploads/2013/04/failplay-teaser-rcm239x151.jpg"))
		self.genreliste.append(("GIGA Gameplay","http://www.giga.de/games/videos/giga-gameplay/", "http://static.giga.de/wp-content/uploads/2012/12/gameplay2-rcm239x151.jpg"))
		self.genreliste.append(("GIGA Live","http://www.giga.de/games/videos/giga-live/", "http://static.giga.de/wp-content/uploads/2012/12/gigatvlive-teaser-rcm239x151.jpg"))
		self.genreliste.append(("GIGA Top Montag","http://www.giga.de/mac/channel/giga-top-montag/", "http://static.giga.de/wp-content/uploads/2013/04/topmontag-teaser-rcm239x151.jpg"))
		self.genreliste.append(("Jonas liest","http://www.giga.de/games/videos/jonas-liest/", "http://static.giga.de/wp-content/uploads/2012/12/jonasliest-teaser-rcm239x151.jpg"))
		self.genreliste.append(("NostalGIGA","http://www.giga.de/games/videos/nostalgiga/", "http://static.giga.de/wp-content/uploads/2012/12/nostalgiga-rcm239x151.jpg"))
		self.genreliste.append(("Radio GIGA","http://www.giga.de/games/videos/radio-giga/", "http://static.giga.de/wp-content/uploads/2012/12/radiogiga-rcm239x151.jpg"))
		self.genreliste.append(("Specials","http://www.giga.de/games/videos/specials/", default_cover))
		self.genreliste.append(("Top 100 Filme","http://www.giga.de/games/channel/top-100-filme/", "http://static.giga.de/wp-content/uploads/2012/12/top100filme-teaser-rcm239x151.jpg"))
		self.genreliste.append(("Top 100 Games","http://www.giga.de/games/channel/top-100-games/", "http://static.giga.de/wp-content/uploads/2012/12/top100spiele-teaser-rcm239x151.jpg"))
		self.genreliste.append(("Top 100 Momente","http://www.giga.de/android/channel/top-100-spielemomente/", "http://static.giga.de/wp-content/uploads/2013/04/top100spielemomente-teaser-rcm239x151.jpg"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.genreliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		Image = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(gigatvFilmScreen, streamGenreLink, Name)

class gigatvFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, CatLink, Name):
		self.CatLink = CatLink
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

		self['title'] = Label("GIGA.de")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.page = 1
		self.lastpage = 1
		self['title'].setText('GIGA.de')

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if self.page > 1:
			url = "%spage/%s/" % (self.CatLink, str(self.page))
		else:
			url = "%s" % (self.CatLink)
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		self.getLastPage(data, 'class="pagination">(.*?)</ul>', '.*(?:>|\s+)(\d+)(?:<|)')
		Movies = re.findall('<article\sclass=.*?<img title="(.*?)".*?src="(https://static.giga.de/.*?)".*?<a\shref="(.*?)"', data, re.S|re.I)
		if Movies:
			for (Title, Image, Url) in Movies:
				self.filmliste.append((decodeHtml(Title).strip(), Url, Image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.getID).addErrback(self.dataError)

	def getID(self, data):
		ID = re.findall('\/embed\/(\d+)', data, re.S)
		if ID:
			url = "http://videos.giga.de/embed/%s" % ID[0]
			self.keyLocked = True
			getPage(url).addCallback(self.getVideoPage).addErrback(self.dataError)
		else:
			yt = re.findall('www.youtube.com/(v|embed)/(.*?)\?.*?"', data, re.S)
			if yt:
				title = self['liste'].getCurrent()[0][0]
				self.session.open(YoutubePlayer,[(title, yt[0][1], None)],playAll= False,showPlaylist=False,showCover=False)
			else:
				message = self.session.open(MessageBoxExt, _("This video is not available."), MessageBoxExt.TYPE_INFO, timeout=5)

	def getVideoPage(self, data):
		data = data.replace('\/','/')
		videoPage = re.findall('src":"(http[s]?:\/\/(?:lx\d+.spieletips.de|vid-cdn\d+.stroeermb.de)/\d+(?:_v\d+|)/(?:1080|720|480|360)+p.mp4)"', data, re.S)
		if videoPage:
			url = videoPage[0]
			self.play(url)
		else:
			message = self.session.open(MessageBoxExt, _("This video is not available."), MessageBoxExt.TYPE_INFO, timeout=5)
		self.keyLocked = False

	def play(self,file):
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Title, file)], showPlaylist=False, ltype='giga')