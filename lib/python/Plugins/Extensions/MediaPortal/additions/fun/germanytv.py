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
from Plugins.Extensions.MediaPortal.resources.simpleplayer import SimplePlayer, SimplePlaylist
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

default_cover = "file://%s/germanytv.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class germanytvChannelScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Germany-TV")
		self['ContentTitle'] = Label(_("Menu"))
		self['name'] = Label(_("Selection:"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(('Science-TV', 'http://www.science-tv.com'))
		self.genreliste.append(('Medizin-TV', 'http://www.medizin-tv.tv.grid-tv.com'))
		#self.genreliste.append(('Opera-TV', 'http://www.opera-tv.tv.grid-tv.com'))
		#self.genreliste.append(('Worldnews-TV', 'http://www.worldnews-tv.tv.grid-tv.com'))
		#self.genreliste.append(('Lasershow-TV', 'http://www.lasershow-tv.germany-tv.com'))
		self.genreliste.append(('Fashionguide-TV', 'http://www.fashionguide-tv.tv.grid-tv.com'))
		#self.genreliste.append(('Fly-HDTV', 'http://www.fly-hdtv.tv.grid-tv.com'))
		#self.genreliste.append(('Auto-TV', 'http://www.auto-tv.tv.grid-tv.com'))
		#self.genreliste.append(('FineArts-TV', 'http://www.finearts-hdtv.tv.grid-tv.com'))
		#self.genreliste.append(('Rechtsberater-TV', 'http://www.rechtsberater-tv.tv.grid-tv.com'))
		self.genreliste.sort()
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(germanytvGenreScreen, url, name)

class germanytvGenreScreen(MPScreen):

	def __init__(self, session, baseurl, name):
		self.baseurl = baseurl
		self.name = name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label(self.name)
		self['ContentTitle'] = Label(_("Menu"))
		self['name'] = Label(_("Selection:"))
		self['F1'] = Label(_("Exit"))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml


		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		twAgentGetPage(self.baseurl).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		aktuell = re.findall('href="([a-zA-Z0-9\/\,\_]+)"><span>(?:Sender|aktuelles Programm|Auto-TV|Hauptsender)</span>', data, re.S)
		if aktuell:
			self.genreliste.append(('Aktuelles Programm', 1, '%s%s?contentpart=prog_video' % (self.baseurl, aktuell[0])))
		abruf = re.findall('href="([a-zA-Z0-9\/\,\_]+)"><span>(?:Filme auf Abruf|OnDemand)</span>', data, re.S)
		if abruf:
			self.genreliste.append(('Filme auf Abruf', 2, '%s%s' % (self.baseurl, abruf[0])))
		vorschau = re.findall('href="([a-zA-Z0-9\/\,\_\-]+)"><span>(?:TV-Programmvorschau|Programmhinweis)</span>', data, re.S)
		if vorschau:
			self.genreliste.append(('TV-Programmvorschau', 3, '%s%s' % (self.baseurl, vorschau[0])))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		genreID = self['liste'].getCurrent()[0][1]
		genre = self['liste'].getCurrent()[0][0]
		tvLink = self['liste'].getCurrent()[0][2]
		if genreID == 1:
			self.session.open(
				GermanyTVPlayer2,
				[(genre, tvLink)],
				'%s - aktuelles Programm' % self.name
				)
		else:
			self.session.open(germanytvListScreen, genreID, tvLink, genre, self.name, self.baseurl)

class germanytvListScreen(MPScreen):

	def __init__(self, session, genreID, tvLink, stvGenre, name, baseurl):
		self.genreID = genreID
		self.tvLink = tvLink
		self.genreName = stvGenre
		self.name = name
		self.baseurl = baseurl
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"	: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label(self.name)
		self['ContentTitle'] = Label("Genre: %s" % self.genreName)
		self['F1'] = Label(_("Exit"))
		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		twAgentGetPage(self.tvLink).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		if self.genreID == 2:
			stvDaten = re.findall('<a href="\?v=(.*?)" title="(.*?)".*?<img src="(.*?)".*?_time">(.*?)<', data)
			if stvDaten:
				for (href,title,img,dura) in stvDaten:
					self.filmliste.append(('',title.replace(' - ','\n',1).replace('&amp;','&')+' ['+dura+']',href,img))
				self.keyLocked = False
			else:
				self.filmliste.append((_('No videos found!'),'','',''))
			self.ml.setList(map(self.TvListEntry, self.filmliste))
		elif self.genreID == 3:
			m = re.search('<div id="bx_main_c">(.*?)</table>', data, re.S)
			if m:
				stvDaten = re.findall('<td .*?<strong>(.*?)</strong></td>.*?title="(.*?)"><img src="(.*?)".*?onclick=', m.group(1), re.S)
			if stvDaten:
				for (ptime,title,img) in stvDaten:
					title = title.replace(' - ','\n\t',1).replace('&amp;','&')
					self.filmliste.append((ptime+'\t',title,'',img))
				self.keyLocked = False
			else:
				self.filmliste.append((_('No program data found!'),'','',''))
			self.ml.setList(map(self.TvListEntry, self.filmliste))
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setItemHeight(height*2)

	def keyOK(self):
		if self.keyLocked:
			return
		if self.genreID == 2:
			self.session.open(
				GermanyTVPlayer,
				self.filmliste,
				self.baseurl + "/inc/mod/video/play.php/vid,%s/q,mp4/hq,1/typ,ondemand/file.mp4",
				playIdx = self['liste'].getSelectedIndex(),
				playAll = True,
				listTitle = self.genreName
				)

class GermanyTVPlaylist(SimplePlaylist):

	def playListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1].replace('\n',' - ')))
		return res

class GermanyTVPlayer(SimplePlayer):

	def __init__(self, session, playList, tvLink, playIdx=0, playAll=False, listTitle=None):
		self.tvLink = tvLink
		SimplePlayer.__init__(self, session, playList, playIdx, playAll, listTitle, useResume=False)

	def getVideo(self):
		tvLink = self.tvLink % self.playList[self.playIdx][2]
		tvTitle = self.playList[self.playIdx][1]
		self.playStream(tvTitle, tvLink)

	def openPlaylist(self, pl_class=GermanyTVPlaylist):
		SimplePlayer.openPlaylist(self, pl_class)

class GermanyTVPlayer2(SimplePlayer):

	def __init__(self, session, playList, tvTitle, playIdx=0, playAll=False, listTitle=None):
		self.tvLink = None
		self.tryCount = 7
		self.tvTitle = tvTitle

		SimplePlayer.__init__(self, session, playList, playIdx, playAll, listTitle, showPlaylist=False, useResume=False)

	def getVideo(self):
		url = self.playList[self.playIdx][1]
		twAgentGetPage(url).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		tvStream = re.findall('video src=&quot;(.*?)&quot;', data)
		if tvStream:
			if self.tvLink != tvStream[0]:
				self.tvLink = tvStream[0].replace('q,mp4/','q,mp4/hq,1/')
				self.playStream(self.tvTitle, self.tvLink)
			elif self.tryCount:
				self.tryCount -= 1
				self.getVideo()

	def doEofInternal(self, playing):
		if playing == True:
			self.tryCount = 7
			reactor.callLater(1, self.getVideo)