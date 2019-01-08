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

default_cover = "file://%s/spiegeltv.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
BASE_URL = 'https://www.spiegel.tv/'
cid = 0

class spiegeltvGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("SPIEGEL.TV")
		self['ContentTitle'] = Label(_("Genre:"))
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.getCID)

	def getCID(self):
		getPage(BASE_URL).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		global cid
		cid = re.findall('"cid":"(.*?)",', data, re.S)[0]
		self.filmliste.append(("Neu auf SPIEGEL.TV", "new", ""))
		self.filmliste.append(("Meistgesehen", "hot", ""))
		self.filmliste.append(("Sendungen", "allshows", ""))
		self.filmliste.append(("Themen", "allplaylists", ""))
		self.filmliste.append(("Studios", "allstudios", ""))
		self.filmliste.append(("Filme", "playlists", "2543-popcorn-film-schauen-und-zuruecklehnen"))
		self.ml.setList(map(self._defaultlistcenter, self.filmliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		method = self['liste'].getCurrent()[0][1]
		param = self['liste'].getCurrent()[0][2]
		self.session.open(spiegeltvListScreen, Name, method, param)

class spiegeltvListScreen(MPScreen):

	def __init__(self, session, name, method, param):
		self.Name = name
		self.method = method
		self.param = param

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("SPIEGEL.TV")
		self['ContentTitle'] = Label("Auswahl: %s" % self.Name)
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.page = 1
		self.lastpage = 1

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		self.keyLocked = True

		url = "http://www.spiegel.tv/gateway/service.php"
		self.postdata = {'cid':cid,
				'method':self.method,
				'cgw':'html5',
				'param':self.param,
				'start':(self.page-1)*25,
				'isu':0,
				'uhs':0,
				'agc':0,
				'wbp':0,
				'client':748,
				'cdlang':'de'
				}
		getPage(url, method='POST',  postdata=urlencode(self.postdata), headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		data = str(json.loads(data)['contents'])
		if "navigatemore" in data:
			self.lastpage = self.page + 1
		if self.lastpage > 1:
			self['Page'].setText(_("Page:"))
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		if self.method in ["allshows", "allstudios", "allplaylists"]:
			shows = re.findall("(<a href.*?data-navigateto='(.*?)' data-navigateparam='(.*?)'.*?<img class='icon' src='(.*?)'.*?\salt='(.*?)'.*?class=(?:'tholderbottom'|'autocut addinfo')>.*?</div>)", data, re.S)
			for (entry,method,param,image,title) in shows:
				subtitle = re.findall("cardsubtitle'>(.*?)</div>", entry, re.S)
				if subtitle and subtitle[0] != "&nbsp;":
					title = decodeHtml(title + " - " + subtitle[0])
				image = image.replace('.webp','.jpg')
				self.filmliste.append((title, image, method, param, "sub"))
		else:
			shows = re.findall("(<a href='/videos/.*?data-vid='(.*?)'.*?img(?:\sclass='tleft'|)\ssrc='(.*?)'.*?cardsubtitle'>(.*?)</div.*?cardtitle'>(.*?)</div.*?class=(?:'tholderbottom'|'autocut addinfo')>.*?</div>)", data, re.S)
			for (entry,vid,image,subtitle,title) in shows:
				image = image.replace('.webp','.jpg')
				if subtitle != "":
					title = decodeHtml(title + " - " + subtitle)
				desc = re.findall("class='tdesc'>(.*?)</div>", entry, re.S)
				if desc:
					desc = decodeHtml(desc[0]).strip()
				else:
					desc = ""
				info = re.findall("class=(?:'tholderbottom'|'autocut addinfo')>(.*?)</div>", entry, re.S)
				if info:
					info = stripAllTags(info[0])
					if "|" in info:
						runtime = decodeHtml(info.split('|')[0].strip())
						studio = decodeHtml(info.split('|')[1].strip())
					else:
						if "Min." in info:
							runtime = info
							studio = "---"
						else:
							runtime = "---"
							studio = info
				else:
					runtime = "---"
					studio = "---"
				descr = _("Runtime:") + " " + runtime + "\n" + "Studio: " + studio + "\n\n" + desc
				self.filmliste.append((title, image, vid, descr, ""))
		if len(self.filmliste) == 0:
			self.filmliste.append((_('No videos found!'), default_cover, None, "", ""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][1]
		descr = self['liste'].getCurrent()[0][3]
		type = self['liste'].getCurrent()[0][4]
		if type == "":
			self['handlung'].setText(descr)
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		sub = self['liste'].getCurrent()[0][4]
		Name = self['liste'].getCurrent()[0][0]
		if sub != "":
			method = self['liste'].getCurrent()[0][2]
			param = self['liste'].getCurrent()[0][3]
			self.session.open(spiegeltvListScreen, Name, method, param)
		else:
			id = self['liste'].getCurrent()[0][2]
			videourl = None
			if id:
				from Plugins.Extensions.MediaPortal.resources import nexx
				videourl = nexx.getVideoUrl(id, False, operation='spiegeltv')
			if videourl:
				self.session.open(SimplePlayer, [(Name, videourl)], showPlaylist=False, ltype='spiegeltv')