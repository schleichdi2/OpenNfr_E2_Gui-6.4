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
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

default_cover = "file://%s/cczwei.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class cczwei(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("CC2.tv")
		self['ContentTitle'] = Label("Folgen:")
		self.streamList = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.keyLocked = False
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://cc2.tv/daten/20161213181538.php"
		getPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		parse = re.search('class="block"><h4>Videosendungen(.*)', data, re.S)
		videos = re.findall('class="blockchen">.*?:\sFolge\s(\d+)(.*?)(?:Youtube|H.264|H264).*?(?:</a>|</a><br>)(.*?)</ul', parse.group(1), re.S)
		if videos:
			for (folge, urldata, title) in videos:
				url = re.search('.*?href="https://(?:youtu.be/|www.youtube.com/watch\?v=)(.*?)"', urldata, re.S)
				if url:
					url = url.group(1)
				else:
					url = re.search('.*?href="(.*?)"', urldata, re.S)
					url = url.group(1)
				title = title.replace('\r\n<br>',', ').replace('   ','').replace('Youtube, HD 1080p','').replace('<br>',', ').strip().strip(', ').strip(',')
				title = "Folge %s - %s" % (folge, stripAllTags(title.replace(', , , ','').replace(', , ','').replace('mehr</a>','')))
				self.streamList.append((decodeHtml(title), url.strip()))
			self.ml.setList(map(self._defaultlistleft, self.streamList))
			self.keyLocked = False

	def keyOK(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		url = self['liste'].getCurrent()[0][1]
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(YoutubePlayer,[(Title, url, None)],playAll= False,showPlaylist=False,showCover=False)