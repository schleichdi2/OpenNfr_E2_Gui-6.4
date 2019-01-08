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
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage

default_cover = "file://%s/srg.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class SRGGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("SRG Play Channels")
		self['ContentTitle'] = Label("Auswahl des Senders")

		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		self.genreliste.append(('SRF', ''))
		self.genreliste.append(('RTS', ''))
		self.genreliste.append(('RTR', ''))
		self.genreliste.append(('RSI', ''))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		channel = self['liste'].getCurrent()[0][0]
		self.session.open(SRGListScreen, channel)

class SRGListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, channel):
		self.channel = channel
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Play %s" % self.channel)
		self['ContentTitle'] = Label("Auswahl der Sendung")

		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = "http://il.srf.ch/integrationlayer/1.0/ue/%s/tv/assetGroup/editorialPlayerAlphabetical.json" % self.channel.lower()
		twAgentGetPage(url, gzip_decoding=True).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.genreliste = []
		listJson = json.loads(data)
		try:
			for node in listJson["AssetGroups"]["Show"]:
				serie = node["title"].encode('utf-8')
				id = node["id"].encode('utf-8')
				try:
					image = node['Image']['ImageRepresentations']['ImageRepresentation'][0]['url'].encode('utf-8')
					image = image.replace('/16x9','')
				except:
					image = None
				try:
					handlung = node["description"].encode('utf-8')
				except:
					handlung = ""
				self.genreliste.append((decodeHtml(serie), id, image, handlung))
		except:
			pass
		self.genreliste.sort(key=lambda t : t[0].lower())
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.genreliste, 0, 1, 2, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamHandlung = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(decodeHtml(streamHandlung))
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		serie = self['liste'].getCurrent()[0][0]
		streamGenreLink = self['liste'].getCurrent()[0][1]
		self.session.open(SRGFilmeListeScreen, streamGenreLink, serie, self.channel)

class SRGFilmeListeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, streamGenreLink, serie, channel):
		self.streamGenreLink = streamGenreLink
		self.serie = serie
		self.channel = channel
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("Play %s" % self.channel)
		self['ContentTitle'] = Label("Folgen Auswahl")
		self['F2'] = Label(_("Page"))

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 999

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = "http://il.srf.ch/integrationlayer/1.0/ue/%s/assetSet/listByAssetGroup/%s.json?pageNumber=%s&pageSize=10" % (self.channel.lower(), self.streamGenreLink, str(self.page))
		twAgentGetPage(url, gzip_decoding=True).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		try:
			listJson = json.loads(data)
			try:
				self.getLastPage(str(listJson["AssetSets"]["@maxPageNumber"]), '', '(\d+)')
			except:
				self.lastpage = 1
			for node in listJson["AssetSets"]["AssetSet"]:
					try:
						serie = node["title"].encode("utf-8")
						url = node["Assets"]["Video"][0]["id"].encode("utf-8")
						try:
							videotitle = node["Assets"]["Video"][0]["AssetMetadatas"]["AssetMetadata"][0]["title"].encode("utf-8")
							if serie != videotitle:
								serie = "%s - %s" % (serie, videotitle)
						except:
							pass
						try:
							desc = node["Assets"]["Video"][0]["AssetMetadatas"]["AssetMetadata"][0]["description"].encode("utf-8").strip()
						except:
							desc = ""
						try:
							image = node["Assets"]["Video"][0]["Image"]["ImageRepresentations"]["ImageRepresentation"][0]["url"].encode("utf-8")
							image = image.replace('/16x9','')
						except:
							image = None
						self.filmliste.append((decodeHtml(serie), url, desc, image))
					except:
						pass
		except:
			pass
		if len(self.filmliste) == 0:
			self.filmliste.append(('Keine Sendungen gefunden.', None, '', None))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self['Page'].setText('')
			self['page'].setText('')
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.th_ThumbsQuery(self.filmliste, 0, 1, 3, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamHandlung = self['liste'].getCurrent()[0][2]
		self['handlung'].setText(streamHandlung)
		streamPic = self['liste'].getCurrent()[0][3]
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		staffel = self['liste'].getCurrent()[0][0]
		urlid = self['liste'].getCurrent()[0][1]
		if urlid:
			self.session.open(SRGStreamScreen, self.serie, staffel, urlid, self.channel)

class SRGStreamScreen(MPScreen):

	def __init__(self, session, serie, staffel, urlid, channel):
		self.serie = serie
		self.staffel = staffel
		self.urlid = urlid
		self.channel = channel
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Play %s" % self.channel)
		self['ContentTitle'] = Label("Auswahl des Streams - %s" % self.staffel)

		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		url = 'http://il.srf.ch/integrationlayer/1.0/ue/%s/video/play/%s.json' % (self.channel.lower(), self.urlid)
		twAgentGetPage(url, gzip_decoding=True).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.genreliste = []
		try:
			listJson = json.loads(data)
			try:
				streamurl = listJson["Video"]["Downloads"]["Download"]
				for playlist in streamurl:
					protoname = playlist['@protocol'].encode("utf-8")
					for urldata in playlist["url"]:
						myurl = urldata["text"].encode("utf-8")
						quali = urldata['@quality'].encode("utf-8")
						self.genreliste.append(('%s %s' % (protoname, quali) , myurl))
			except:
				pass
			try:
				streamurl = listJson["Video"]["Playlists"]['Playlist']
				for playlist in streamurl:
					protoname = playlist['@protocol'].encode("utf-8")
					if protoname == "HTTP-HLS":
						for urldata in playlist["url"]:
							myurl = urldata["text"].encode("utf-8")
							quali = urldata['@quality'].encode("utf-8")
							self.genreliste.append(('%s %s' % (protoname, quali) , myurl))
			except:
				pass
		except:
			pass
		if len(self.genreliste) == 0:
			self.genreliste.append(('Keine Sendungen gefunden.',''))
		self.genreliste.sort()
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if '.m3u8' in url:
			twAgentGetPage(url, gzip_decoding=True).addCallback(self.loadplaylist).addErrback(self.dataError)
		else:
			self.session.open(SimplePlayer, [(self.serie, url)], showPlaylist=False, ltype='srg')

	def loadplaylist(self, data):
		try:
			bandwith_list = []
			match_sec_m3u8=re.findall('BANDWIDTH=(\d+).*?\n(.*?m3u8)', data, re.S)
			videoPrio = int(config_mp.mediaportal.videoquali_others.value)
			if videoPrio == 2:
				bw = int(match_sec_m3u8[-2][0])
			elif videoPrio == 1:
				bw = int(match_sec_m3u8[-2][0])/2
			else:
				bw = int(match_sec_m3u8[-2][0])/3
			for each in match_sec_m3u8:
				bandwith,url = each
				bandwith_list.append((int(bandwith),url))
			_, best = min((abs(int(x[0]) - bw), x) for x in bandwith_list)
			url = best[1]

			self.session.open(SimplePlayer, [(self.serie, url)], showPlaylist=False, ltype='srg')
		except:
			url = self['liste'].getCurrent()[0][1].replace("srfvodhd-vh.akamaihd", "hdvodsrforigin-f.akamaihd")
			twAgentGetPage(url, gzip_decoding=True).addCallback(self.loadplaylist).addErrback(self.dataError)