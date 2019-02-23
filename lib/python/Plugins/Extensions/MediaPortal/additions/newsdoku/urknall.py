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
#############################################################################################

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

default_cover = "file://%s/urknall.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class UrknallFilmListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok"    : self.keyOK,
			"0" : self.closeAll,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("Urknall, Weltall und das Leben")
		self['ContentTitle'] = Label("Videos:")
		self['name'] = Label("Video Auswahl")

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		url = "https://www.urknall-weltall-leben.de/media/com_jamegafilter/de_de/1.json"
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		from collections import OrderedDict
		movies = json.loads(data, object_pairs_hook=OrderedDict)
		for item in movies:
			print str(movies[item]["name"])
			url = "https://www.urknall-weltall-leben.de/" + str(movies[item]["url"])
			image = "https://www.urknall-weltall-leben.de/" + str(movies[item]["thumbnail"])
			title = str(movies[item]["name"])
			try:
				severity = str(movies[item]["attr"]["ct3"]["frontend_value"][-1]).replace('[','').replace(']','')
			except:
				severity = "---"
			try:
				length = str(movies[item]["attr"]["ct12"]["frontend_value"])
			except:
				length = "---"
			self.filmliste.append((title,url,image,length,severity))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		length = self['liste'].getCurrent()[0][3]
		severity = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(pic)
		url = self['liste'].getCurrent()[0][1]
		self['handlung'].setText('Länge: %s min\nSchwierigkeit: %s' % (length,severity))
		getPage(url).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		parse = re.search('class="itemIntroText">(.*?)</div>', data, re.S)
		if parse:
			descr = decodeHtml(stripAllTags(parse.group(1)).strip())
			length = self['liste'].getCurrent()[0][3]
			severity = self['liste'].getCurrent()[0][4]
			self['handlung'].setText('Länge: %s min\nSchwierigkeit: %s\n%s' % (length,severity,descr))

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			self.keyLocked = True
			getPage(url).addCallback(self.getlink).addErrback(self.dataError)

	def getlink(self, data):
		parse = re.findall('www.*?(?:-nocookie|-gdprlock|)(?:.com|)/(v|embed)/(.*?)"', data, re.S)
		if parse:
			title = self['liste'].getCurrent()[0][0]
			self.session.open(YoutubePlayer,[(title, parse[0][1], None)],playAll= False,showPlaylist=False,showCover=False)
		else:
			message = self.session.open(MessageBoxExt, _("This video is not available."), MessageBoxExt.TYPE_INFO, timeout=5)
		self.keyLocked = False