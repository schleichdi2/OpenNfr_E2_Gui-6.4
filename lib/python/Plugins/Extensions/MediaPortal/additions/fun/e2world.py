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

default_cover = "file://%s/e2world.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class e2world(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("E2WORLD")
		self['ContentTitle'] = Label(_("Selection:"))

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste = []
		self.genreliste.append(("E2WORLD", "http://e2world.de/feed/episode/"))
		self.genreliste.append(("ARCHIV", "http://e2world.de/feed/archiv/"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(e2worldMain, Link, Name)

class e2worldMain(MPScreen):

	def __init__(self, session, Link, Name):
		self.link = Link
		self.name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(self.name)
		self['ContentTitle'] = Label("Videos:")
		self['name'] = Label(_("Please wait..."))

		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = True
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.streamList = []
		url = self.link
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		videos = re.findall('<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<enclosure\surl="(.*?)"\slength.*?<itunes:summary>(.*?)</itunes:summary>.*?<itunes:image\shref="(.*?)"\s/>', data, re.S)
		if videos:
			for (title,url,stream,handlung,pic) in videos:
				self.streamList.append((decodeHtml(title),url,handlung,stream,pic))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False
			self['name'].setText('')
			self.showInfos()

	def showInfos(self):
		self.name = self['liste'].getCurrent()[0][0]
		handlung = self['liste'].getCurrent()[0][2]
		pic = self['liste'].getCurrent()[0][4]
		self['handlung'].setText(decodeHtml(handlung))
		self['name'].setText(self.name)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		stream = self['liste'].getCurrent()[0][3]
		if stream:
			self.session.open(SimplePlayer, [(self.name, stream)], showPlaylist=False, ltype='e2world')