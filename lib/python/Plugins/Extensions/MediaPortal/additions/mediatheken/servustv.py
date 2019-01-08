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

baseurl = "https://www.servus.com"
stvAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
default_cover = "file://%s/servustv.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class sTVGenreScreen(MPScreen):

	def __init__(self, session):

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("ServusTV")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Aktuelles", "/de/aktuelles"))
		self.genreliste.append(("Abenteuer", "/de/abenteuer"))
		self.genreliste.append(("Dokumentarfilm", "/de/dokumentarfilm"))
		self.genreliste.append(("Kultur", "/de/kultur"))
		self.genreliste.append(("Natur", "/de/natur"))
		self.genreliste.append(("Sport", "/de/sport"))
		self.genreliste.append(("Unterhaltung", "/de/unterhaltung"))
		self.genreliste.append(("Volkskultur", "/de/volkskultur"))
		self.genreliste.append(("Wissen", "/de/wissen"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		url = baseurl + url
		self.session.open(sTVids,name,url)

class sTVids(MPScreen):

	def __init__(self, session,name,url):
		self.Link = url
		self.Name = name
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

		self.keyLocked = True
		self['title'] = Label("ServusTV")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['name'] = Label(_("Please wait..."))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		getPage(self.Link, agent=stvAgent).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		parse = re.search('row products(.*?)id="foot"', data, re.S)
		shows = re.findall('video-play"\shref="(.*?([A-Z0-9-]+)\/)">.*?src="(https://da\d{0,2}.rbmbtnx.net/.*?\.jpg).*?class="card-title"><a href=".*?">(.*?)</a>', parse.group(1), re.S)
		if shows:
			for (url,id,image,title) in shows:
				self.filmliste.append((decodeHtml(title),id,image,url))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.ml.moveToIndex(0)
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		url = self['liste'].getCurrent()[0][3]
		url = baseurl + url
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)
		self['handlung'].setText('')
		getPage(url, agent=stvAgent).addCallback(self.getDescr).addErrback(self.dataError)

	def getDescr(self, data):
		descr = re.findall('class="product-content.*?</div><br>(.*?)(?:</div>|<div)', data, re.S)
		if descr:
			descr = decodeHtml(stripAllTags(descr[0].replace('<br /><br />', '\n').replace('<br />', '\n')))
			self['handlung'].setText(descr)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		url = 'https://stv.rbmbtnx.net/api/v1/manifests/%s.m3u8' % url
		basepath = 'https://stv.rbmbtnx.net/api/v1/manifests/'
		getPage(url, agent=stvAgent).addCallback(self.loadplaylist, basepath).addErrback(self.dataError)

	def loadplaylist(self, data, basepath):
		bandwith_list = []
		match_sec_m3u8=re.findall('BANDWIDTH=(\d+).*?\n((?!#).*?m3u8)', data, re.S)
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
		self.bandwith_list = []
		for each in match_sec_m3u8:
			bandwith,url = each
			self.bandwith_list.append((int(bandwith),url))
		_, best = min((abs(int(x[0]) - bw), x) for x in self.bandwith_list)
		url = basepath + best[1]
		Name = self['liste'].getCurrent()[0][0]
		mp_globals.player_agent = stvAgent
		self.session.open(SimplePlayer, [(Name, url)], showPlaylist=False, ltype='servustv')