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
default_cover = "file://%s/arte.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class arteFirstScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("arte Mediathek")
		self['ContentTitle'] = Label(_("Genre:"))
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.suchString = ''
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)


	def genreData(self):
		self.filmliste.append(("Suche", "search"))
		self.filmliste.append(("Meistgesehen", "http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/mostViewed/page/%%PAGE%%/limit/50/de"))
		self.filmliste.append(("Letzte Chance", "http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/lastChance/page/%%PAGE%%/limit/50/de"))
		self.filmliste.append(("Sendungen A-Z", "http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/magazines/de"))
		self.filmliste.append(("Themen", "by_channel"))
		self.filmliste.append(("Datum", "by_date"))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		if Name == "Suche":
			self.suchen()
		elif 'http://' in Link:
			self.session.open(arteSecondScreen, Link, Name)
		else:
			self.session.open(arteSubGenreScreen, Link, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "Suche"
			self.suchString = callback
			Link = urllib.quote(self.suchString).replace(' ', '%20')
			self.session.open(arteSecondScreen, Link, Name)

class arteSubGenreScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("arte Mediathek")
		self['ContentTitle'] = Label(_("Genre:") + " %s" % Name)
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		if self.Name == "Datum":
			today = datetime.date.today()
			for daynr in range(-21,22):
				day1 = today -datetime.timedelta(days=daynr)
				dateselect =  day1.strftime('%Y-%m-%d')
				link = 'http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/programs/%s/de' % dateselect
				self.filmliste.append((dateselect, link))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
			self.ml.moveToIndex(21)
		elif self.Name == "Themen":
			# http://www.arte.tv/hbbtvv2/services/web/index.php/EMAC/teasers/categories/v2/de
			link = 'http://www.arte.tv/hbbtvv2/services/web/index.php/EMAC/teasers/category/%s/de'
			self.filmliste.append(('Aktuelles und Gesellschaft', link % 'ACT'))
			self.filmliste.append(('Kino', link % 'CIN'))
			self.filmliste.append(('Fernsehfilme und Serien', link % 'SER'))
			self.filmliste.append(('Kultur und Pop', link % 'CPO'))
			self.filmliste.append(('ARTE Concert', link % 'ARS'))
			self.filmliste.append(('Wissenschaft', link % 'SCI'))
			self.filmliste.append(('Entdeckung der Welt', link % 'DEC'))
			self.filmliste.append(('Geschichte', link % 'HIS'))
			self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(arteSecondScreen, Link, Name)

class arteSecondScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
		}, -1)

		self['title'] = Label("arte Mediathek")
		self['ContentTitle'] = Label(_("Selection:") + " %s" % self.Name)

		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self['name'].setText(_('Please wait...'))
		url = self.Link
		if self.Name == "Suche":
			url = "https://www.arte.tv/guide/api/api/zones/de/listing_SEARCH/?limit=100&query=%s&page=%s" % (url, str(self.page))
		else:
			url = url.replace('%%PAGE%%',str(self.page))
			if "/teasers/category/" in url:
				id = url.split('/')[-2]
				url2 = "http://www.arte.tv/hbbtvv2/services/web/index.php/EMAC/teasers/category/v2/%s/de" % id
				getPage(url2, agent=std_headers, headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'Referer': self.Link}).addCallback(self.parseData).addErrback(self.dataError)
		getPage(url, agent=std_headers, headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'Referer': self.Link}).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		json_data = json.loads(data)
		if "teasers" in self.Link:
			if json_data.has_key('category'):
				for node in json_data["category"]:
					if str(node["type"]) == "category":
						title = "Thema: " + str(node["title"])
						code = str(node["code"])
						url = 'http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/subcategory/%s/page/1/limit/100/de' % code
						self.filmliste.append((decodeHtml(title), url, default_cover, "", "subcat"))
				self.filmliste.sort()
			if json_data.has_key('teasers'):
				if json_data["teasers"].has_key('highlights') and len(json_data["teasers"]["highlights"]) > 0:
					for node in json_data["teasers"]["highlights"]:
						kind = str(node['kind'])
						if kind in ["SHOW", "BONUS"]:
							url = "https://api.arte.tv/api/player/v1/config/de/%s" % str(node['programId'])
						else:
							url = str(node['programId'])
						if node['subtitle']:
							title = "%s - %s" % (str(node['title']), str(node['subtitle']))
						else:
							title = str(node['title'])
						title = "Highlight: " + title
						image = str(node['imageUrl'])
						if node['teaserText']:
							descr = str(node['teaserText'])
						else:
							descr = ""
						self.filmliste.append((decodeHtml(title), url, image, descr, kind))
					self.filmliste.sort()
				if json_data["teasers"].has_key('collections') and len(json_data["teasers"]["collections"]) > 0:
					for node in json_data["teasers"]["collections"]:
						kind = str(node['kind'])
						programid = str(node['programId'])
						if node['subtitle']:
							title = "%s - %s" % (str(node['title']), str(node['subtitle']))
						else:
							title = str(node['title'])
						title = "Collection: " + title
						image = str(node['imageUrl'])
						if node['teaserText']:
							descr = str(node['teaserText'])
						else:
							descr = ""
						self.filmliste.append((decodeHtml(title), programid, image, descr, kind))
					self.filmliste.sort()
				if json_data["teasers"].has_key('playlists') and len(json_data["teasers"]["playlists"]) > 0:
					for node in json_data["teasers"]["playlists"]:
						kind = str(node['kind'])
						programid = str(node['programId'])
						if node['subtitle']:
							title = "%s - %s" % (str(node['title']), str(node['subtitle']))
						else:
							title = str(node['title'])
						title = "Playlist: " + title
						image = str(node['imageUrl'])
						if node['teaserText']:
							descr = str(node['teaserText'])
						else:
							descr = ""
						self.filmliste.append((decodeHtml(title), programid, image, descr, kind))
					self.filmliste.sort()
				if json_data["teasers"].has_key('magazines') and len(json_data["teasers"]["magazines"]) > 0:
					for node in json_data["teasers"]["magazines"]:
						title = "Sendung: " + str(node["label"]["de"])
						url = str(node["url"])
						image = default_cover
						self.filmliste.append((decodeHtml(title), url, image, "", "sendung"))
					self.filmliste.sort()
		else:
			if json_data.has_key('programs'):
				for node in json_data["programs"]:
					if node['video']:
						if node['video']['kind'] in ["CLIP", "MANUAL_CLIP", "TRAILER"]:
							continue
						if node['video']['subtitle']:
							title = "%s - %s" % (str(node['video']['title']), str(node['video']['subtitle']))
						else:
							title = str(node['video']['title'])
						if node['video']['durationSeconds']:
							m, s = divmod(node['video']['durationSeconds'], 60)
							Runtime = _("Runtime:") + " %02d:%02d" % (m, s)
						else:
							Runtime = _("Runtime:") + " --:--"
						if node['video']['broadcastBegin']:
							date = str(node['video']['broadcastBegin'])
							date = re.findall('.*?,\s(\d{2})\s(\w+)\s(\d{4})\s(.*?)\s\+', date)
							date = _("Date:") + " " + date[0][0] + ". " + date[0][1] + " " + date[0][2] + ", " + date[0][3] + "\n"
						else:
							date = ""
						if node['video']['fullDescription']:
							descr = str(node['video']['fullDescription'])
						elif node['video']['shortDescription']:
							descr = str(node['video']['shortDescription'])
						elif node['video']['teaserText']:
							descr = str(node['video']['teaserText'])
						else:
							descr = ""
						handlung = "%s%s\n\n%s" % (date, Runtime, descr)
						image = str(node['video']['imageUrl'])
						url = "https://api.arte.tv/api/player/v1/config/de/%s" % str(node['video']['programId'])
						self.filmliste.append((decodeHtml(title), url, image, handlung, ""))
			elif json_data.has_key('videos'):
				if json_data.has_key('meta'):
					self.lastpage = json_data["meta"]["pages"]
					if self.lastpage > 1:
						self['Page'].setText(_("Page:"))
						self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
				for node in json_data["videos"]:
					if node['subtitle']:
						title = "%s - %s" % (str(node['title']), str(node['subtitle']))
					else:
						title = str(node['title'])
					if node['durationSeconds']:
						m, s = divmod(node['durationSeconds'], 60)
						Runtime = _("Runtime:") + " %02d:%02d" % (m, s)
					else:
						Runtime = _("Runtime:") + " --:--"
					if node['broadcastBegin']:
						date = str(node['broadcastBegin'])
						date = re.findall('.*?,\s(\d{2})\s(\w+)\s(\d{4})\s(.*?)\s\+', date)
						date = _("Date:") + " " + date[0][0] + ". " + date[0][1] + " " + date[0][2] + ", " + date[0][3] + "\n"
					else:
						date = ""
					if node['fullDescription']:
						descr = str(node['fullDescription'])
					elif node['shortDescription']:
						descr = str(node['shortDescription'])
					elif node['teaserText']:
						descr = str(node['teaserText'])
					else:
						descr = ""
					handlung = "%s%s\n\n%s" % (date, Runtime, descr)
					image = str(node['imageUrl'])
					url = "https://api.arte.tv/api/player/v1/config/de/%s" % str(node['programId'])
					self.filmliste.append((decodeHtml(title), url, image, handlung, ""))
			elif json_data.has_key('magazines'):
				for node in json_data["magazines"]:
					if node['subtitle']:
						title = "%s - %s" % (str(node['title']), str(node['subtitle']))
					else:
						title = str(node['title'])
					if node['fullDescription']:
						descr = str(node['fullDescription'])
					else:
						descr = str(node['shortDescription'])
					image = str(node['imageUrl'])
					kind = str(node['kind'])
					url = str(node['programId'])
					self.filmliste.append((decodeHtml(title), url, image, descr, kind))
			elif json_data.has_key('data'):
				if json_data.has_key('nextPage'):
					if json_data["nextPage"]:
						self.lastpage = self.page + 1
					if self.lastpage > 1:
						self['Page'].setText(_("Page:"))
						self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
				for node in json_data["data"]:
					if node['subtitle']:
						title = "%s - %s" % (str(node['title']), str(node['subtitle']))
					else:
						title = str(node['title'])
					if node['duration']:
						m, s = divmod(node['duration'], 60)
						Runtime = _("Runtime:") + " %02d:%02d" % (m, s)
					else:
						continue
					handlung = "%s\n\n%s" % (Runtime, str(node['description']))
					url = "https://api.arte.tv/api/player/v1/config/de/%s" % str(node['programId'])
					self.filmliste.append((decodeHtml(title), url, str(node['images']['landscape']['resolutions'][-1]['url']), handlung, ""))

			if len(self.filmliste) == 0:
				self.filmliste.append((_("No videos found!"), '','','','',''))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		self.ImageUrl = self['liste'].getCurrent()[0][2]
		handlung = self['liste'].getCurrent()[0][3]
		self['name'].setText(_(title))
		self['handlung'].setText(handlung)
		CoverHelper(self['coverArt']).getCover(self.ImageUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		self.title = self['liste'].getCurrent()[0][0]
		link = self['liste'].getCurrent()[0][1]
		kind = self['liste'].getCurrent()[0][4]
		if link.startswith('http') and kind != "subcat":
			getPage(link, headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}).addCallback(self.getStream).addErrback(self.dataError)
		else:
			id = self['liste'].getCurrent()[0][1]
			if kind == "subcat":
				url = id
			elif kind != "sendung":
				url = "http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/collection/%s/%s/de" % (kind, id)
			else:
				url = "http://www.arte.tv/hbbtvv2/services/web/index.php/%s/de" % id
			self.session.open(arteSecondScreen, url, self.title)

	def getStream(self, data):
		json_data  = json.loads(data)
		if json_data["videoJsonPlayer"].has_key('VSR'):
			try:
				url = str(json_data["videoJsonPlayer"]["VSR"]["HTTPS_SQ_1"]["url"])
			except:
				url = None
		else:
			url = None
		if url:
			self.session.open(SimplePlayer, [(self.title, url, self.ImageUrl)], showPlaylist=False, ltype='arte')
		else:
			self.session.open(MessageBoxExt, _("This video is not available."), MessageBoxExt.TYPE_INFO, timeout=5)