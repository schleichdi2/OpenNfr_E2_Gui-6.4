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
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

default_cover = "file://%s/shoutcast.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
BASE_URL = "https://directory.shoutcast.com/"

agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'

json_headers = {
	'Accept':'application/json',
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/x-www-form-urlencoded',
	}

class ShoutcastGenreScreen(MPScreen):

	def __init__(self, session, subgenre=""):
		self.subgenre = subgenre

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self.keyLocked = True
		self['title'] = Label("shoutcast")
		self['ContentTitle'] = Label(_("Genre:"))

		self.genreliste = []
		self.suchString = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)
		self.onClose.append(self.restoreRadio)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		twAgentGetPage(BASE_URL, agent=agent).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if self.subgenre != "":
			preparse = re.search('class="main-genre.*?name=%s"(.*?)</ul' % self.subgenre, data, re.S)
			if preparse:
				genres = re.findall('class="sub-genre.*?name=(.*?)"', preparse.group(1), re.S)
				for genre in genres:
					self.genreliste.append((genre.replace('%20',' ').replace('%26','&'),genre.replace('%20',' ').replace('%26','&'),"sub"))
				self.genreliste.sort(key=lambda t : t[0].lower())
				self.genreliste.insert(0, (_("All Stations"),self.subgenre.replace('%20',' ').replace('%26','&'),"sub"))
		else:
			genres = re.findall('class="main-genre.*?name=(.*?)"', data, re.S)
			for genre in genres:
				self.genreliste.append((genre.replace('%20',' ').replace('%26','&'),genre,"main"))
			self.genreliste.sort(key=lambda t : t[0].lower())
			self.genreliste.insert(0, (_("Top Stations"),_("Top Stations"),"top"))
			self.genreliste.insert(0, (_("Search"),_("Search"),"search"))

		if len(self.genreliste) == 0:
			self.genreliste.append((_('No genres found!'), None, None))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self['name'].setText('')

	def keyOK(self):
		if self.keyLocked:
			return
		Genre = self['liste'].getCurrent()[0][0]
		Id = self['liste'].getCurrent()[0][1]
		Type = self['liste'].getCurrent()[0][2]
		if not Type:
			return
		elif Type == "main":
			self.session.open(ShoutcastGenreScreen, Id)
		elif Type == "sub":
			self.session.open(ShoutcastStationsScreen, Genre, Id, Type)
		elif Type == "top":
			self.session.open(ShoutcastStationsScreen, Genre, Id, Type)
		elif Type == "search":
			self.suchen()

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "Suche"
			self.suchString = callback
			self.session.open(ShoutcastStationsScreen, _("Search"), self.suchString, "search")

	def restoreRadio(self):
		config_mp.mediaportal.is_radio.value = False

class ShoutcastStationsScreen(MPScreen):

	def __init__(self, session, genre, id, type):
		self.genre = genre
		self.id = id
		self.type = type

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"cancel": self.keyCancel,
			"yellow" : self.keySort,
		}, -1)

		self.keyLocked = True
		self['title'] = Label("shoutcast")
		self['ContentTitle'] = Label(_("Stations:"))
		self['F3'] = Label(_("Sort"))

		self.sort = "listeners"
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		if self.type == "top":
			url = BASE_URL + "/Home/Top"
			postdata = {'genrename': ''}
		elif self.type == "search":
			url = BASE_URL + "/Search/UpdateSearch"
			postdata = {'query': self.id}
		else:
			url = BASE_URL + "/Home/BrowseByGenre"
			postdata = {'genrename': self.id}
		twAgentGetPage(url, method='POST', postdata=urlencode(postdata), agent=agent, headers=json_headers).addCallback(self.getStations).addErrback(self.dataError)

	def getStations(self, data):
		jsondata = json.loads(data)
		for each in jsondata:
			name = str(each["Name"])
			id = str(each["ID"])
			bitrate = str(each["Bitrate"])
			genre = str(each["Genre"])
			listeners = str(each["Listeners"])
			format = str(each["Format"])
			if format == "audio/mpeg":
				format = "MP3"
			elif format == "audio/aacp":
				format = "AAC"
			self.streamList.append((name,id,bitrate,genre,listeners,format))
		if self.sort == "station":
			self.streamList.sort(key=lambda t : t[0])
		elif self.sort == "listeners":
			self.streamList.sort(key=lambda t : int(t[4]), reverse=True)
		elif self.sort == "genre":
			self.streamList.sort(key=lambda t : t[3])
		elif self.sort == "bitrate":
			self.streamList.sort(key=lambda t : int(t[2]), reverse=True)
		elif self.sort == "format":
			self.streamList.sort(key=lambda t : t[5])
		if len(self.streamList) == 0:
			self.streamList.append((_('No stations found!'), None, "","","",""))
		self.ml.setList(map(self._defaultlistleft, self.streamList))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		self['name'].setText(self['liste'].getCurrent()[0][0])
		bitrate = self['liste'].getCurrent()[0][2]
		genre = self['liste'].getCurrent()[0][3]
		listeners = self['liste'].getCurrent()[0][4]
		format = self['liste'].getCurrent()[0][5]
		self['handlung'].setText(_("Genre:")+" "+genre+"\n"+_("Listeners")+": "+listeners+"\n"+_("Bitrate")+": "+bitrate+"\n"+_("Format")+": "+format)

	def keySort(self):
		if self.keyLocked:
			return
		rangelist = [[_('Station'), 'station'], [_('Listeners'), 'listeners'], [_('Genre'), 'genre'], [_('Bitrate'), 'bitrate'], [_('Format'), 'format']]
		self.session.openWithCallback(self.keySortAction, ChoiceBoxExt, title=_('Select Action'), list = rangelist)

	def keySortAction(self, result):
		if result:
			self.sort = result[1]
			self.loadPage()

	def keyOK(self):
		if self.keyLocked:
			return
		stationId = self['liste'].getCurrent()[0][1]
		if not stationId:
			return
		url = BASE_URL + "/Player/GetStreamUrl"
		postdata = {'station': stationId}
		twAgentGetPage(url, method='POST', postdata=urlencode(postdata), agent=agent, headers=json_headers).addCallback(self.getStreamURL).addErrback(self.dataError)

	def getStreamURL(self, data):
		name = self['liste'].getCurrent()[0][0]
		url = data[1:-1]
		config_mp.mediaportal.is_radio.value = True
		self.session.open(SimplePlayer, [(name, url, 'file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png')], showPlaylist=False, ltype='shoutcast', playerMode='RADIO', cover=True)