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

default_cover = "file://%s/heisevideo.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
heiseAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
baseUrl = 'http://www.heise.de'

class HeiseTvGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0"	: self.closeAll,
			"cancel": self.keyCancel
		}, -1)


		self['title'] = Label("heise Video")
		self['ContentTitle'] = Label("Genres")
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.data_rubrikid="2523"
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self['name'].setText(_('Please wait...'))
		getPage(baseUrl+'/video').addCallback(self.buildMenu).addErrback(self.dataError)

	def buildMenu(self, data):
		m = re.search('<ul id="teaser_reiter_nav">(.*?)</ul>', data, re.S)
		if m:
			list = re.findall('href="#(reiter.*?)">(.*?)</a></li>', m.group(1), re.S)
			if list:
				for r, n in list:
					nm = decodeHtml(n)
					m2 = re.search('<a href="(\?teaser=.*?);.*?into=%s' % r, data)
					if m2:
						self.genreliste.append((nm, 1, n, '/video/%s;offset=%%d;into=%s&hajax=1' % (m2.group(1), r)))
		list = re.findall('<section class="kasten video.*?<h3><span></span>(.*?)</h3>', data, re.S)
		if list:
			for x in list:
				if not [1 for item in self.genreliste if item[1] == x]:
					nm = decodeHtml(x)
					self.genreliste.append((nm, 3, x, '/video'))
		m = re.search('<section id="cttv_archiv">(.*?)</section>', data, re.S)
		if m:
			list = re.findall('data-jahr="(.*?)"', m.group(1), re.S)
			if list:
				for j in list:
					nm = "c't-TV Archiv %s" % j
					url = '/video/includes/cttv_archiv_json.pl?jahr=%s&rubrik=%s' % (j, self.data_rubrikid)
					self.genreliste.append((nm, 2, nm, url))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self['name'].setText(_("Selection:"))

	def keyOK(self):
		if self.keyLocked:
			return
		genreID = self['liste'].getCurrent()[0][1]
		genre = self['liste'].getCurrent()[0][0]
		raw_genre = self['liste'].getCurrent()[0][2]
		Link = self['liste'].getCurrent()[0][3]
		self.session.open(HeiseTvListScreen, genreID, Link, genre, raw_genre)

class HeiseTvListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreID, Link, stvGenre, raw_genre):
		self.genreID = genreID
		self.Link = Link
		self.genreName = stvGenre
		self.rawGenre = raw_genre
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"0" : self.closeAll,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("heise Video")
		self['ContentTitle'] = Label(self.genreName)
		self['Page'] = Label(_("Page:"))

		if self.genreID != 1:
			self['Page'].hide()
			self['page'].hide()

		self.page = 0
		self.lastpage = 999
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		if self.genreID == 1:
			url = baseUrl+(self.Link % (self.page * 10))
		else:
			url = baseUrl+self.Link
		getPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		if self.genreID == 1:
			json_data = json.loads(data)
			stvDaten = re.findall('class=\"rahmen\">.*?<img src=\"(.*?)\".*?<h3><a href=\"(.*?)\">(.*?)</a>.*?<p>(.*?)<a href=\"', str(json_data['actions'][1]['html']), re.S)
			if stvDaten:
				for (img,href,title,desc) in stvDaten:
					title = decodeHtml(title).strip()
					desc = decodeHtml(desc).strip()
					img = baseUrl + img
					self.filmliste.append((title, href, img, desc))
			self['page'].setText(str(self.page+1))
		elif self.genreID == 2:
			json_data = json.loads(data[1:-2])
			for item in json_data:
				title = str(item['titel'])
				desc = str(item['anrisstext'])
				url = str(item['url'])
				if item['anrissbild'].has_key('src'):
					img = baseUrl + str(item['anrissbild']['src'])
				else:
					img = None
				self.filmliste.append((title, url, img, desc))
		elif self.genreID == 3:
			patt = '<section class="kasten video.*?<h3><span></span>%s</h3>(.*?)</section>' % self.rawGenre
			m = re.search(patt, data, re.S)
			if m:
				stvDaten = re.findall('<img.*?src="(.*?)".*?<h4><a href="(.*?)">(.*?)</a></h4>', m.group(1), re.S)
				if stvDaten:
					for (img,href,title) in stvDaten:
						title = decodeHtml(title)
						if img.startswith('//'):
							img = 'https:' + img
						self.filmliste.append((title,href,img,''))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'),'','',''))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
		else:
			self.keyLocked = False
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, 999, mode=1)
			self.showInfos()

	def showInfos(self):
		stvTitle = self['liste'].getCurrent()[0][0]
		stvImage = self['liste'].getCurrent()[0][2]
		desc = self['liste'].getCurrent()[0][3]
		self['name'].setText(stvTitle)
		self['handlung'].setText(desc)
		CoverHelper(self['coverArt']).getCover(stvImage)

	def keyOK(self):
		if self.keyLocked:
			return
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		url = baseUrl + self['liste'].getCurrent()[0][1]
		getPage(url).addCallback(self.getVid).addErrback(self.dataError)

	def getVid(self, data):
		entryid = re.findall('entry-id="(.*?)"', data, re.S)
		if entryid:
			partnerid = "2238431"
			url = "https://cdnapisec.kaltura.com/p/%s/sp/%s00/playManifest/entryId/%s/format/applehttp/protocol/https/a.m3u8" % (partnerid, partnerid, entryid[0])
			getPage(url, agent=heiseAgent).addCallback(self.loadplaylist, partnerid, entryid[0]).addErrback(self.dataError)

	def loadplaylist(self, data, partnerid, entry_id):
		self.bandwith_list = []
		match_sec_m3u8=re.findall('BANDWIDTH=(.*?),.*?RESOLUTION=(.*?).*?https://.*?flavorId\/(.*?)\/.*?.m3u8', data, re.S)
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
			bandwith,resolution,url = each
			self.bandwith_list.append((int(bandwith),url))
		_, best = min((abs(int(x[0]) - bw), x) for x in self.bandwith_list)
		url = "https://cdnapisec.kaltura.com/p/%s/sp/%s00/playManifest/entryId/%s/flavorIds/%s/" % (partnerid, partnerid, entry_id, best[1])
		getPage(url, agent=heiseAgent).addCallback(self.getVideo).addErrback(self.dataError)

	def getVideo(self, data):
		vid = re.findall('url="(.*?)"', data, re.S)
		if vid:
			title = self['liste'].getCurrent()[0][0]
			self['name'].setText(title)
			self.keyLocked = False
			url = vid[0].replace('&amp;','&')
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='heisetv')

	def keyPageDown(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		if self.genreID != 1:
			return
		if not self.page < 2:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		if self.genreID != 1:
			return
		if self.page < self.lastpage:
			self.page += 1
			self.loadPage()