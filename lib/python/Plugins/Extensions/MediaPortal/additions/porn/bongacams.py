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

BASEURL = "https://en.bongacams.com/"

default_cover = "file://%s/bongacams.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
bongacamsAgent = "Mozilla/5.0 (iPad; CPU OS 8_1_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12B466 Safari/600.1.4"
ck = {}
json_headers = {
	'Accept':'application/json',
	'Accept-Language':'en,en-US;q=0.7,en;q=0.3',
	'X-Requested-With':'XMLHttpRequest',
	'Content-Type':'application/x-www-form-urlencoded',
	'Referer':'https://en.bongacams.com/',
	'Origin':'https://en.bongacams.com',
	}

class bongacamsGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
		}, -1)


		self['title'] = Label("BongaCams.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		getPage(BASEURL).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('categories_list(.*?)class="panel_item">', data, re.S)
		Cats = re.findall('href="\/(.*?)">(.*?)</a', parse.group(1), re.S)
		if Cats:
			for (Url, Title) in Cats:
				self.genreliste.append((Title, Url))
		self.genreliste.sort()
		self.genreliste.insert(0, ("Couple", "couples"))
		self.genreliste.insert(0, ("Female", "females"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(bongacamsFilmScreen, Link, Name)

class bongacamsFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions2", "MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"upUp" : self.key_repeatedUp,
			"rightUp" : self.key_repeatedUp,
			"leftUp" : self.key_repeatedUp,
			"downUp" : self.key_repeatedUp,
			"upRepeated" : self.keyUpRepeated,
			"downRepeated" : self.keyDownRepeated,
			"rightRepeated" : self.keyRightRepeated,
			"leftRepeated" : self.keyLeftRepeated,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("BongaCams.com")
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
		if self.Link == "couples":
			livetab = "couples"
			category = ""
		else:
			livetab = "females"
			category = self.Link
		url = BASEURL + "tools/listing_v3.php?livetab=" + livetab + "&online_only=true&offset=" + str((self.page*24)-24) + "&category=" + category
		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued(headers=json_headers)

	def loadPageData(self, data):
		self.ml.moveToIndex(0)
		jsondata = json.loads(data)
		lastp = jsondata["total_count"]
		lastp = round((float(lastp) / 24) + 0.5)
		self.lastpage = int(lastp)
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		for node in jsondata["models"]:
			if node.has_key('display_name'):
				Title = str(node["display_name"])
			else:
				continue
			Url = str(node["username"])
			Image = 'http:' + str(node["thumb_image"])
			Status = str(node["about_me"])
			if not node["is_away"] and not str(node["room"])=="private" and not str(node["room"])=="vip":
				self.filmliste.append((Title, Url, Image, Status))
		if len(self.filmliste):
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.loadPicQueued()
		else:
			self.filmliste.append((_('No livestreams found!'), None, None, None, None, None, None, None))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()
		self.keyLocked = False

	def showInfos(self):
		Url = self['liste'].getCurrent()[0][1]
		if Url == None:
			return
		title = self['liste'].getCurrent()[0][0]
		status = self['liste'].getCurrent()[0][3]
		self['name'].setText(title)
		self['handlung'].setText(status)

	def keyOK(self):
		if self.keyLocked:
			return
		self.username = self['liste'].getCurrent()[0][1]
		self['name'].setText(_('Please wait...'))
		url = BASEURL + self.username
		getPage(url, agent=bongacamsAgent, cookies=ck).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		amf = re.search('.*?directServiceUrl\s=\s\'\/(.*?)\'\+\$', data, re.S).group(1)
		url = BASEURL + amf + str(random.randint(2100000, 3200000))
		getPage(url, agent=bongacamsAgent, cookies=ck, method='POST', postdata='method=getRoomData&args%5B%5D='+self.username+'&args%5B%5D=false', headers=json_headers).addCallback(self.play_stream).addErrback(self.dataError)

	def play_stream(self, data):
		url = re.findall('"videoServerUrl":"(.*?)"', data, re.S)
		if url:
			url = 'https:' + url[-1].replace('\/','/') + '/hls/stream_' + self.username + '/chunks.m3u8'
			title = self['liste'].getCurrent()[0][0]
			self['name'].setText(title)
			mp_globals.player_agent = bongacamsAgent
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='bongacams')
		else:
			self.session.open(MessageBoxExt, _("Cam is currently offline."), MessageBoxExt.TYPE_INFO)