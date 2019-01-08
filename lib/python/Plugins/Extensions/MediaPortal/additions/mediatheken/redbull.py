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

default_cover = "file://%s/redbull.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
base_url ="https://api.redbull.tv/v3/"
rb_token = None

def _header():
	header = {}
	header['Accept'] = 'application/json, text/plain, */*'
	header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36'
	header['Accept-Encoding'] = 'deflate'
	header['Referer'] = 'https://www.redbull.tv/'
	header['Origin'] = 'https://www.redbull.tv'
	header['Host'] = 'api.redbull.tv'
	if rb_token:
		header['Authorization'] = rb_token
	return header

class RBtvGenreScreen(MPScreen):

	def __init__(self, session, name="", url=None, level=0, image=None):
		self.name = name
		self.url = url
		self.level = level
		self.image = image

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

		self['title'] = Label("Red Bull TV")
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self.keyLocked = True
		self.offset = 0

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml


		self.onLayoutFinish.append(self.getToken)

	def getToken(self):
		self['name'].setText(_("Please wait..."))
		if rb_token and self.url:
			url = self.url  + "?offset=%s&limit=20" % self.offset
			getPage(url, headers=_header()).addCallback(self.getGenre).addErrback(self.dataError)
		else:
			url = base_url + "session?category=personal_computer&os_family=http"
			getPage(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36'}).addCallback(self.parseToken).addErrback(self.dataError)

	def parseToken(self, data):
		global rb_token
		rb_token = re.findall('token":"(.*?)"', data, re.S)[0]
		url = base_url + "products/channels"
		getPage(url, headers=_header()).addCallback(self.getGenre).addErrback(self.dataError)

	def getGenre(self, data):
		json_data = json.loads(data)
		if json_data.has_key('collections'):
			if len(json_data["collections"]) > 0:
				if self.level > 2:
					title = str(json_data["title"])
					if json_data.has_key('duration'):
						duration = str(json_data["duration"])
					else:
						duration = None
					if json_data.has_key('long_description'):
						descr = str(json_data["long_description"])
					elif json_data.has_key('short_description'):
						descr = str(json_data["short_description"])
					else:
						descr = ""
					if json_data.has_key('subheading'):
						subtitle = str(json_data["subheading"])
						title = title + " - " + subtitle
					if "/video/" in str(json_data["share_url"]):
						url = str(json_data["share_url"])
					else:
						url = "https://www.redbull.tv/video/%s" % str(json_data["links"][0]["id"])
					image = "https://resources.redbull.tv/%s/rbtv_display_art_landscape/im:i:w_500,q_70" % str(json_data["id"])
					self.genreliste.append((title, url, image, 5, True, descr, duration))
				for item in json_data["collections"]:
					if self.level == 0:
						title = str(item["label"])
						url = base_url + "collections/" + str(item["id"])
						if title != "Featured Channels":
							self.genreliste.append((title, url, default_cover, 1, False, "", None))
					elif self.level == 2:
						title = str(item["label"])
						url = base_url + "collections/" + str(item["id"])
						if title != "Related Channels":
							if title != "Upcoming Live Events":
								self.genreliste.append((title, url, self.image, 3, False, "", None))
					else:
						title = str(item["label"])
						url = base_url + "collections/" + str(item["id"])
						self.genreliste.append((title, url, default_cover, 5, False, "", None))
			else:
				title = str(json_data["title"])
				if json_data.has_key('duration'):
					duration = str(json_data["duration"])
				else:
					duration = None
				if json_data.has_key('long_description'):
					descr = str(json_data["long_description"])
				elif json_data.has_key('short_description'):
					descr = str(json_data["short_description"])
				else:
					descr = ""
				if json_data.has_key('subheading'):
					subtitle = str(json_data["subheading"])
					title = title + " - " + subtitle
				if "/video/" in str(json_data["share_url"]):
					url = str(json_data["share_url"])
				else:
					url = "https://www.redbull.tv/video/%s" % str(json_data["links"][0]["id"])
				image = "https://resources.redbull.tv/%s/rbtv_display_art_landscape/im:i:w_500,q_70" % str(json_data["id"])
				self.genreliste.append((title, url, image, 5, True, descr, duration))
		elif json_data.has_key('items'):
			if self.level == 1:
				for item in json_data["items"]:
					title = str(item["title"])
					if self.name == "Formats":
						img = "background"
					else:
						img = "display_art"
					url = base_url + "products/" + str(item["id"])
					image = "https://resources.redbull.tv/%s/rbtv_%s_landscape/im:i:w_400,q_70" % (str(item["id"]), img)
					self.genreliste.append((title, url, image, 2, False, "", None))
			else:
				for item in json_data["items"]:
					title = str(item["title"])
					if item.has_key('duration'):
						duration = str(item["duration"])
					else:
						duration = None
					if item.has_key('long_description'):
						descr = str(item["long_description"])
					elif item.has_key('short_description'):
						descr = str(item["short_description"])
					else:
						descr = ""
					if item.has_key('subheading'):
						subtitle = str(item["subheading"])
						title = title + " - " + subtitle
					if "/video/" in str(item["share_url"]):
						url = str(item["share_url"])
						play = True
					else:
						if str(json_data["item_type"]) == "video":
							play = True
							url = "https://www.redbull.tv/video/%s" % str(item["id"])
						else:
							url = base_url + "products/" + str(item["id"])
							play = False
					image = "https://resources.redbull.tv/%s/rbtv_display_art_landscape/im:i:w_500,q_70" % str(item["id"])
					self.genreliste.append((title, url, image, 4, play, descr, duration))
		if json_data.has_key('meta'):
			total = json_data["meta"]["total"]
			offset = json_data["meta"]["offset"]
			if total > offset:
				self.offset += 20
				self.getToken()
			else:
				self.ml.setList(map(self._defaultlistcenter, self.genreliste))
				self.keyLocked = False
				self.showInfos()
		else:
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
			self.keyLocked = False
			self.showInfos()

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		pic = self['liste'].getCurrent()[0][2]
		descr = self['liste'].getCurrent()[0][5]
		runtime = self['liste'].getCurrent()[0][6]
		if runtime:
			m, s = divmod(int(runtime)/1000, 60)
			h, m = divmod(m, 60)
			runtime = _("Runtime:") + " %02d:%02d:%02d\n\n" % (h, m, s)
		else:
			runtime = ""
		self['name'].setText(title)
		self['handlung'].setText(runtime+descr)
		CoverHelper(self['coverArt']).getCover(pic)

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][2]
		level = self['liste'].getCurrent()[0][3]
		play = self['liste'].getCurrent()[0][4]
		if play:
			self['name'].setText(_('Please wait...'))
			getPage(url).addCallback(self.loadm3u8).addErrback(self.dataError)
		else:
			self.session.open(RBtvGenreScreen, name, url, level, image)

	def loadm3u8(self, data):
		self.keyLocked = True
		url = re.findall('video_product":{"url":"(.*?)"', data, re.S)
		if not url:
			self.session.open(MessageBoxExt, _("This event is not yet available."), MessageBoxExt.TYPE_INFO, timeout=3)
			self.keyLocked = False
		else:
			getPage(url[0]).addCallback(self.loadplaylist).addErrback(self.dataError)

	def loadplaylist(self, data):
		self.bandwith_list = []
		match_sec_m3u8=re.findall('BANDWIDTH=(.*?),.*?RESOLUTION=(.*?),.*?(https://.*?m3u8)', data, re.S)
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
		for each in match_sec_m3u8:
			bandwith,resolution,url = each
			self.bandwith_list.append((int(bandwith),url))
		_, best = min((abs(int(x[0]) - bw), x) for x in self.bandwith_list)
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		self.keyLocked = False
		self.session.open(SimplePlayer, [(title, best[1])], showPlaylist=False, ltype='redbulltv')