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

baseurl ="http://www.pokerstars.tv"
ptvAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'

default_cover = "file://%s/pokerstars.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class pokerGenreScreen(MPScreen):

	def __init__(self, session):

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Pokerstars.tv")
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = baseurl + "/en/tv/channels/"
		getPage(url, agent=ptvAgent).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.findall('class="channel-list-item-box".*?href="(.*?)".*?src=.*?alt="(.*?)"', data, re.S)
		if parse:
			for (url,title) in parse:
				url = baseurl + url
				self.genreliste.append((decodeHtml(title),url))
			self.genreliste.sort()
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self['name'].setText("")

	def subnavcheck(self, data, name, url):
		check = re.findall('class="subNav">.*?<li class="cat-item">', data, re.S)
		if check:
			self.session.open(subnav, name, url)
		else:
			self.session.open(vids, name, url)

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if self.keyLocked:
			return
		getPage(url, agent=ptvAgent).addCallback(self.subnavcheck, name, url).addErrback(self.dataError)

class subnav(MPScreen):

	def __init__(self, session,name,url):
		self.url = url
		self.name = name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Pokerstars.tv")
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		getPage(self.url, agent=ptvAgent).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.findall('<li\sclass="cat-item">.*?<a\shref="(.*?)">(.*?)</a>', data, re.S)
		if parse:
			for (url,title) in parse:
				title = title.strip()
				url = baseurl + url
				self.filmliste.append((decodeHtml(title),url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self['name'].setText("")

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(vids, name, url)

class vids(MPScreen):

	def __init__(self, session,name,url):
		self.url = url
		self.name = name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Pokerstars.tv")
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		getPage(self.url, agent=ptvAgent).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.findall('summary">.*?href="(.*?)"\stitle="(.*?)".*?src="(.*?)"\s/>.*?class="play-icon">', data, re.S)
		if parse:
			for (url,title,pic) in parse:
				if pic.startswith("//"):
					pic = "http:"+pic
				self.filmliste.append((decodeHtml(title),url,pic))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		self['name'] = Label(_("Please wait..."))
		url = baseurl + self['liste'].getCurrent()[0][1]
		getPage(url, agent=ptvAgent).addCallback(self.getID).addErrback(self.dataError)

	def getID(self, data):
		id = re.findall('video\sid.*?data-account="(.*?)".*?data-video-id="(.*?)"', data, re.S)
		if id:
			url = 'https://edge.api.brightcove.com/playback/v1/accounts/%s/videos/%s' % (id[0][0], id[0][1])
			getPage(url, agent=ptvAgent, headers={'Accept':'application/json;pk=BCpkADawqM3sHGtdSMkF8i2PaiJ_d80U27WemZ7iCLP-9C1sxUoTeTfeECM8LcCVKswW7-C06UeXnq1rHWqwt4t9GnMI7mXiqQ0o-RDSIDRtDA25a6RC9-N0ZEhCwcWDAxpdhU7LDIY4xsfE'}).addCallback(self.getStream).addErrback(self.dataError)

	def getStream(self, data):
		video = re.findall('"width":\d+,"src":"(.*?)",', data, re.S)
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		self.session.open(SimplePlayer, [(title, video[-1])], showPlaylist=False, ltype='pokerstars')