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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
default_cover = "file://%s/watchbox.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
wbAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
base_url = 'https://www.watchbox.de'

class watchboxGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Watchbox")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(('Neue Filme', '/filme/neu'))
		self.genreliste.append(('Anime', '/anime/filme/neu'))
		self.genreliste.append(('British', '/british/filme/neu'))
		self.genreliste.append(('Science-Fiction', '/science-fiction/filme/neu'))
		self.genreliste.append(('Horror', '/horror/filme/neu'))
		self.genreliste.append(('Independent', '/independent/filme/neu'))
		self.genreliste.append(('Komödie', '/komoedie/filme/neu'))
		self.genreliste.append(('Thriller', '/thriller/filme/neu'))
		self.genreliste.append(('Show', '/show/filme/neu'))
		self.genreliste.append(('Erotik', '/erotik/filme/neu'))
		self.genreliste.append(('Animation', '/animation/filme/neu'))
		self.genreliste.append(('Action', '/action/filme/neu'))
		self.genreliste.append(('Drama', '/drama/filme/neu'))
		self.genreliste.append(('Romantik', '/romantik/filme/neu'))
		self.genreliste.append(('Trash', '/trash/filme/neu'))
		self.genreliste.append(('Asian', '/asian/filme/neu'))
		self.genreliste.append(('Klassiker', '/klassiker/filme/neu'))
		self.genreliste.append(('Queer/LGBT', '/queer-lgbt/filme/neu'))
		self.genreliste.append(('Fantasy', '/fantasy/filme/neu'))
		self.genreliste.append(('Kinder', '/kinder/filme/neu'))
		self.genreliste.append(('Reportage & Doku', '/reportage-und-dokumentationen/filme/neu'))
		self.genreliste.append(('Abenteuer', '/abenteuer/filme/neu'))
		self.genreliste.append(('Western', '/western/filme/neu'))
		self.genreliste.append(('Skandinavien', '/scandinavian/filme/neu'))
		self.genreliste.append(('Krimi', '/crime/filme/neu'))
		self.genreliste.append(('Arthouse', '/arthouse/filme/neu'))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		Url = self['liste'].getCurrent()[0][1]
		self.session.open(watchboxFolgenListeScreen, Name, Url)

class watchboxFolgenListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Name, Url):
		self.Name = Name
		self.Url = Url
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Watchbox")
		self['ContentTitle'] = Label("Filme:")
		self['Page'] = Label(_("Page:"))

		self.page = 1
		self.lastpage = 999

		self.folgenliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.folgenliste = []
		url = base_url + "%s/?page=%s" % (self.Url, str(self.page))
		twAgentGetPage(url, agent=wbAgent).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self['page'].setText(str(self.page))
		if not "js-pagination-more-button" in data:
			self.lastpage = self.page
		folgen = re.findall('class="grid__item".*?format-type="(.*?)".*?href="(.*?)".*?img\s+src="(.*?)".*?alt="(.*?)"', data, re.S)
		if folgen:
			for (type, url, image, title) in folgen:
				if image.startswith('//'):
					image = 'http:' + image
				url = base_url + url
				self.folgenliste.append((decodeHtml(title), url, image, type))
			self.ml.setList(map(self._defaultlistleft, self.folgenliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()
			self.th_ThumbsQuery(self.folgenliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		twAgentGetPage(url, agent=wbAgent).addCallback(self.get_link).addErrback(self.dataError)

	def get_link(self, data):
		data = data.replace('&quot;', '"')
		if '"drm":{"userToken"' in data:
			message = self.session.open(MessageBoxExt, _("This movie can't be played it's protected with DRM."), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			stream_url = re.search('hls":"(.*?\.m3u8)",', data, re.S)
			if stream_url:
				url = stream_url.group(1).replace('\/','/')
				getPage(url, agent=wbAgent).addCallback(self.loadplaylist, url).addErrback(self.dataError)

	def loadplaylist(self, data, baseurl):
		self.bandwith_list = []
		match_sec_m3u8=re.findall('BANDWIDTH=(\d+).*?\n(.*?m3u8)', data, re.S)
		max = 0
		for x in match_sec_m3u8:
			if int(x[0]) > max:
				max = int(x[0])
		videoPrio = int(config_mp.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			bw = max
		elif videoPrio == 1:
			bw = max/2
		else:
			bw = max/3
		for each in match_sec_m3u8:
			bandwith,url = each
			self.bandwith_list.append((int(bandwith),url))
		_, best = min((abs(int(x[0]) - bw), x) for x in self.bandwith_list)

		url = baseurl.replace('fairplay.m3u8', '') + best[1]
		title = self['liste'].getCurrent()[0][0]
		mp_globals.player_agent = wbAgent
		self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='watchbox')