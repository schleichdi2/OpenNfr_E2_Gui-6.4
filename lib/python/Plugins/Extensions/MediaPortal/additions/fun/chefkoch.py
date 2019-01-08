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

basename = "Chefkoch.de"
baseurl ="http://www.chefkoch.de"
securl= "http://www.chefkoch.de/video/artikel/"

default_cover = "file://%s/chefkoch.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class chefkochGenreScreen(MPScreen):

	def __init__(self, session):

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"	: self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre:")
		self['name'] = Label(_("Please wait..."))
		self.keyLocked = True

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		u = "%s/video" % baseurl
		getPage(u).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		raw = re.findall('class="navigation">(.*?)</ul>', data, re.S)
		if raw:
			parse = re.findall('<li\sclass="navigation.*?<a href="(.*?)"\sclass="link.*?>(.*?)</a>', raw[0], re.S)
			for (url, title) in parse:
				title = decodeHtml(title).strip()
				if title != "Club of Cooks":
					self.genreliste.append((title,url))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
		self['name'].setText('')

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if self.keyLocked:
			return
		self.session.open(chefvids, name, url)

class chefvids(MPScreen):

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
		self['title'] = Label(basename)
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		getPage(self.url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		parse = re.findall('class="teaser-box.*?href="/video/artikel/(.*?)".*?img\ssrc="(.*?)".*?<h2>(.*?)</h2>', data, re.S)
		if parse:
			for (url,pic,title) in parse:
				self.filmliste.append((decodeHtml(title).strip(),url,pic))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		self.vid = None
		title = self['liste'].getCurrent()[0][0]
		link = securl + self['liste'].getCurrent()[0][1]
		pic = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)
		getPage(link).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		self.desc = re.findall('itemprop="description" content="(.*?)"', data, re.S)
		self.runtime = re.findall('L.*?nge: <strong>(.*?)</strong>', data, re.S)
		self.vid = re.findall('contentUrl" content="(.*?)"(?:\s/)>', data, re.S)
		if self.desc and self.runtime and self.vid:
			d = "Länge: %s\n%s" % (self.runtime[0],(decodeHtml(self.desc[0])))
		else:
			d = ""
		self['handlung'].setText(d)

	def keyOK(self):
		if self.keyLocked:
			return
		if self.vid:
			self.vid = self.vid[0].replace('https','http')
			name = self['liste'].getCurrent()[0][0]
			self.session.open(SimplePlayer, [(name, str(self.vid))], cover=False, showPlaylist=False, ltype='chefkoch', useResume=False)