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

config_mp.mediaportal.radio_base = ConfigText(default="http://www.rad.io", fixed_size=False)

default_cover = "file://%s/radio.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
base_url = config_mp.mediaportal.radio_base.value

def check_playlist(url):
	import requests
	servers = []
	if url.lower().endswith('.m3u'):
		try:
			s = requests.session()
			page = s.get(url, timeout=15)
			data = page.content
			servers = [
				l for l in data.splitlines()
				if l.strip() and not l.strip().startswith('#')
			]
		except:
			pass
	elif url.lower().endswith('.pls'):
		try:
			s = requests.session()
			page = s.get(url, timeout=15)
			data = page.content
			servers = [
				l.split('=')[1] for l in data.splitlines()
				if l.lower().startswith('file')
			]
		except:
			pass
	if servers:
		return random.choice(servers)
	return url

class RadioGenreScreen(MPScreen):

	def __init__(self, session):

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Radio")
		self['ContentTitle'] = Label(_("Genre:"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)
		self.onClose.append(self.restoreRadio)

	def loadPage(self):
		self.genreliste = [
			(_('Favorites'),None),
			('Radio.de',"http://www.radio.de"),
			('Radio.at',"http://www.radio.at"),
			('Radio.fr',"http://www.radio.fr"),
			('Radio.es',"http://www.radio.es"),
			('Radio.it',"http://www.rad.io"),
			('Radio.pt',"http://www.rad.io"),
			('Radio.dk',"http://www.rad.io"),
			('Radio.se',"http://www.rad.io"),
			('Radio.pl',"http://www.rad.io"),
			('Radio.net',"http://www.rad.io")]

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Genre = self['liste'].getCurrent()[0][0]
		Url = self['liste'].getCurrent()[0][1]

		if Genre == _('Favorites'):
			self.session.open(RadioPlaylist)
		else:
			config_mp.mediaportal.radio_base.value = Url
			config_mp.mediaportal.radio_base.save()
			configfile_mp.save()
			global base_url
			base_url = config_mp.mediaportal.radio_base.value
			self.session.open(RadioSubGenreScreen, Genre, Url)

	def restoreRadio(self):
		config_mp.mediaportal.is_radio.value = False

class RadioSubGenreScreen(MPScreen):

	def __init__(self, session, genre, url):
		self.genre = genre
		self.url = url

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label(self.genre)
		self['ContentTitle'] = Label(_("Genre:"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [
			(_('Local Stations'),self.url+"/info/account/getmostwantedbroadcastlists?sizeoflists=100",'localBroadcasts'),
			(_('Top Stations'),self.url+"/info/account/getmostwantedbroadcastlists?sizeoflists=100",'topBroadcasts'),
			(_('All Stations'),self.url+"/info/menu/broadcastsofcategory?category=_",''),
			(_('Genre'),self.url+"/info/menu/valuesofcategory?category=_genre",''),
			(_('Topic'),self.url+"/info/menu/valuesofcategory?category=_topic",''),
			(_('Country'),self.url+"/info/menu/valuesofcategory?category=_country",''),
			(_('City'),self.url+"/info/menu/valuesofcategory?category=_city",''),
			(_('Language'),self.url+"/info/menu/valuesofcategory?category=_language",'')]

		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Genre = self['liste'].getCurrent()[0][0]
		Url = self['liste'].getCurrent()[0][1]
		Sub = self['liste'].getCurrent()[0][2]

		if Genre == _("Top Stations") or Genre == _("All Stations") or Genre == _("Local Stations") or Genre == _("Recommended Stations"):
			self.session.open(RadioListeScreen, self.genre, Url, sub=Sub)
		else:
			self.session.open(RadioSubValueGenreScreen, self.genre, Genre, Url)

class RadioSubValueGenreScreen(MPScreen):

	def __init__(self, session, topgenre, genre, url):
		self.topgenre = topgenre
		self.genre = genre
		self.url = url

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label(self.topgenre)
		self['ContentTitle'] = Label(_(self.genre))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		getPage(self.url, agent="XBMC").addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		jsondata = json.loads(data)
		for each in jsondata:
			self.genreliste.append((str(each),))
		self.genreliste.sort(key=lambda t : t[0].lower())
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Value = self['liste'].getCurrent()[0][0]

		self.session.open(RadioListeScreen, self.topgenre, self.url.replace('valuesofcategory','broadcastsofcategory'), Value)

class RadioListeScreen(MPScreen, ThumbsHelper, SearchHelper):

	def __init__(self, session, genre, url, value=None, sub=''):
		self.genre = genre
		self.url = url
		self.value = value
		self.sub = sub

		MPScreen.__init__(self, session, skin='MP_Plugin', widgets=('MP_widget_search',), default_cover=default_cover)
		ThumbsHelper.__init__(self)
		SearchHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"long5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"cancel": self.keyCancel,
			"green": self.keyAdd,
			"yellow" : self.keyPageNumber
		}, -1)

		self.keyLocked = True
		self['title'] = Label(self.genre)
		self['ContentTitle'] = Label(_("Stations:"))
		self['F2'] = Label(_("Add to Favorites"))
		self['F3'].setText(_("Page"))

		self.page = 1
		self.lastpage = 1

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def goToNumber(self, num):
		if self.sub == '':
			self.keyNumberGlobal(num, self.streamList)
			self.showSearchkey(num)

	def goToLetter(self, key):
		if self.sub == '':
			self.keyLetterGlobal(key, self.streamList)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		if self.genre in ['Radio.net', 'Radio.it', 'Radio.pt', 'Radio.dk', 'Radio.se', 'Radio.pl'] and self.sub == "topBroadcasts":
			url = "http://www.%s/stations/" % self.genre.lower()
		else:
			url = self.url
			if self.value:
				url = url + "&value=" + urllib.quote_plus(self.value)
			if self.lastpage > 1:
				url = url + "&start=" + str((self.page-1)*100)
		getPage(url, agent="XBMC").addCallback(self.getStations).addErrback(self.dataError)

	def getStations(self, data):
		self.streamList = []
		if self.genre in ['Radio.net', 'Radio.it', 'Radio.pt', 'Radio.dk', 'Radio.se', 'Radio.pl'] and self.sub == "topBroadcasts":
			parse = re.search('.*?class="main-content"(.*?)search-footer', data, re.S)
			stations = re.findall('<img\ssrc="(.*?\/)c\d+.png".*?alt="(.*?)".*?now-playing="(\d+)"', parse.group(1), re.S)
			for (img,name,id) in stations:
				self.streamList.append((name, id, img+"c175.png"))
		else:
			jsondata = json.loads(data)
			if self.sub != '':
				jsondata = jsondata[self.sub]
			if len(jsondata) == 100 and not "sizeoflists" in self.url:
				self.lastpage = 999
			if self.lastpage > 1:
				self['Page'].setText(_("Page:"))
				self['page'].setText(str(self.page))
			for each in jsondata:
				if str(each['broadcastType']) == "1":
					self.streamList.append((str(each['name']).strip(), str(each['id']), str(each['pictureBaseURL'])+"c175.png"))
		if self.sub == '':
			self.streamList.sort(key=lambda t : t[0].lower())
		if len(self.streamList) == 0:
			self.streamList.append((_('No stations found!'), None, None))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.th_ThumbsQuery(self.streamList, 0, 1, 2, None, None, 1, 1, mode=0)
		self.showInfos()

	def showInfos(self):
		self['name'].setText(self['liste'].getCurrent()[0][0])
		stationId = self['liste'].getCurrent()[0][1]
		if stationId:
			url = base_url + "/info/broadcast/getbroadcastembedded?broadcast=%s" % stationId
			getPage(url, agent="XBMC").addCallback(self.getInfos).addErrback(self.dataError)

	def keyOK(self):
		if self.keyLocked:
			return
		stationId = self['liste'].getCurrent()[0][1]
		if not stationId:
			return
		url = base_url + "/info/broadcast/getbroadcastembedded?broadcast=%s" % stationId
		getPage(url, agent="XBMC").addCallback(self.getStreamURL).addErrback(self.dataError)

	def getInfos(self, data):
		jsondata = json.loads(data)
		image = str(jsondata['pictureBaseURL'])+"c175.png"
		CoverHelper(self['coverArt']).getCover(image)
		genre = ''
		for node in jsondata["genres"]:
			genre = genre + ", " + str(node)
		genre = genre.strip(', ')
		if genre == "":
			genre = "---"
		city = str(jsondata["city"])
		if city == "":
			city = "---"
		country = str(jsondata["country"])
		if country == "":
			country = "---"
		descr = str(jsondata["shortDescription"])
		self['handlung'].setText(_("Genre:")+" "+genre+"\n"+_("Country")+": "+country+"\n"+_("City")+": "+city+"\n"+descr)

	def getStreamURL(self, data):
		jsondata = json.loads(data)
		url = str(jsondata['streamUrls'][0]['streamUrl'])
		url = check_playlist(url)
		stationName = self['liste'].getCurrent()[0][0]
		stationCover = str(jsondata['pictureBaseURL'])+"c175.png"
		config_mp.mediaportal.is_radio.value = True
		self.session.open(SimplePlayer, [(stationName, url, stationCover)], showPlaylist=False, ltype='radio', playerMode='RADIO', cover=True)

	def keyAdd(self):
		stationName = self['liste'].getCurrent()[0][0]
		stationId = self['liste'].getCurrent()[0][1]
		if self.keyLocked or not stationId:
			return
		fn = config_mp.mediaportal.watchlistpath.value+"mp_radio_playlist"
		if not fileExists(fn):
			open(fn,"w").close()
		try:
			writePlaylist = open(fn, "a")
			writePlaylist.write('"%s" "%s"\n' % (stationName, stationId))
			writePlaylist.close()
			message = self.session.open(MessageBoxExt, _("Selection was added to the favorites."), MessageBoxExt.TYPE_INFO, timeout=3)
		except:
			pass

class RadioPlaylist(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"cancel": self.keyCancel,
			"red": self.keyDel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Radio")
		self['ContentTitle'] = Label(_("Favorites:"))
		self['F1'] = Label(_("Delete"))

		self.playList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadStations)

	def loadStations(self):
		self.playList = []
		if not fileExists(config_mp.mediaportal.watchlistpath.value+"mp_radio_playlist"):
			open(config_mp.mediaportal.watchlistpath.value+"mp_radio_playlist","w").close()
		if fileExists(config_mp.mediaportal.watchlistpath.value+"mp_radio_playlist"):
			path = config_mp.mediaportal.watchlistpath.value+"mp_radio_playlist"

		if fileExists(path):
			readStations = open(path,"r")
			for rawData in readStations.readlines():
				data = re.findall('"(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(stationName, stationId) = data[0]
					self.playList.append((stationName, stationId))
			self.playList.sort()
			readStations.close()
		if len(self.playList) == 0:
			self.playList.append((_('No entries found!'), None, default_cover))
		self.ml.setList(map(self._defaultlistleft, self.playList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		exist = self["liste"].getCurrent()
		if exist:
			self['name'].setText(self['liste'].getCurrent()[0][0])
			stationId = self['liste'].getCurrent()[0][1]
			url = base_url + "/info/broadcast/getbroadcastembedded?broadcast=%s" % stationId
			getPage(url, agent="XBMC").addCallback(self.getInfos).addErrback(self.dataError)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stationId = self['liste'].getCurrent()[0][1]
		url = base_url + "/info/broadcast/getbroadcastembedded?broadcast=%s" % stationId
		getPage(url, agent="XBMC").addCallback(self.getStreamURL).addErrback(self.dataError)

	def getInfos(self, data):
		jsondata = json.loads(data)
		image = str(jsondata['pictureBaseURL'])+"c175.png"
		CoverHelper(self['coverArt']).getCover(image)
		genre = ''
		for node in jsondata["genres"]:
			genre = genre + ", " + str(node)
		genre = genre.strip(', ')
		if genre == "":
			genre = "---"
		city = str(jsondata["city"])
		if city == "":
			city = "---"
		country = str(jsondata["country"])
		if country == "":
			country = "---"
		descr = str(jsondata["shortDescription"])
		self['handlung'].setText(_("Genre:")+" "+genre+"\n"+_("Country")+": "+country+"\n"+_("City")+": "+city+"\n"+descr)

	def getStreamURL(self, data):
		jsondata = json.loads(data)
		url = str(jsondata['streamUrls'][0]['streamUrl'])
		url = check_playlist(url)
		stationName = self['liste'].getCurrent()[0][0]
		stationCover = str(jsondata['pictureBaseURL'])+"c175.png"
		config_mp.mediaportal.is_radio.value = True
		self.session.open(SimplePlayer, [(stationName, url, stationCover)], showPlaylist=False, ltype='radio', playerMode='RADIO', cover=True)

	def keyDel(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		i = self['liste'].getSelectedIndex()
		c = j = 0
		l = len(self.playList)
		fn = config_mp.mediaportal.watchlistpath.value+"mp_radio_playlist"
		try:
			f1 = open(fn, 'w')
			while j < l:
				if j != i:
					(stationName, stationId) = self.playList[j]
					f1.write('"%s" "%s"\n' % (stationName, stationId))
				j += 1
			f1.close()
			self.loadStations()
		except:
			pass