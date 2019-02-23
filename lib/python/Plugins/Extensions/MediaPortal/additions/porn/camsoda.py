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

BASEURL = "https://www.camsoda.com/api/v1/browse/"

default_cover = "file://%s/camsoda.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
camsodaAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 8_0_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12A366 Safari/600.1.4"

class camsodaGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel
		}, -1)

		self['title'] = Label("CamSoda.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.genreData)
		self.tags = ["toys", "feet", "latina", "curvy", "shaved-pussy", "18", "fetish", "teen", "big-tits", "lovense", "brunette", "ohmibod", "squirter", "petite", "ass", "nature", "cum", "college", "pussy", "anal", "squirt", "small-tits", "blonde", "black", "bbw", "dildo", "new", "lush", "sexy", "naked", "lesbian", "blowjob", "bigass", "hairy-pussy", "bondage", "young", "couple", "tits", "ebony", "pvt", "boobs", "horny", "milf", "fuck", "hidden-cam", "latin", "hot", "wet", "fingering", "bigboobs", "redhead", "muscle", "bigtits", "big-ass", "cumshow", "c2c", "asian", "toy", "cute", "oil", "natural", "pornstar", "pussyplay", "dance", "twerk", "shaved", "deepthroat", "show", "masturbation", "big", "amateur", "play", "tattoos", "bj", "spank", "ride", "naughty", "booty", "daddy", "sex", "flash", "tease", "suck", "sweet", "fun", "hitachi", "dp", "thick", "skype", "hairy", "finger", "creampie", "nipples", "girl", "topless", "dirty", "pregnant", "heels", "clit", "spit"]

	def genreData(self):
		self.genreliste.append(("Most Viewed", "online"))
		self.genreliste.append(("Top Rated", "online"))
		self.tags.sort()
		for tag in self.tags:
			self.genreliste.append((tag.replace('-',' ').title(), "tag-"+tag))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(camsodaFilmScreen, Link, Name)

class camsodaFilmScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions2", "MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"upUp" : self.key_repeatedUp,
			"rightUp" : self.key_repeatedUp,
			"leftUp" : self.key_repeatedUp,
			"downUp" : self.key_repeatedUp,
			"upRepeated" : self.keyUpRepeated,
			"downRepeated" : self.keyDownRepeated,
			"rightRepeated" : self.keyRightRepeated,
			"leftRepeated" : self.keyLeftRepeated
		}, -1)

		self['title'] = Label("CamSoda.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = BASEURL + self.Link
		self.filmQ.put(url)
		if not self.eventL.is_set():
			self.eventL.set()
			self.loadPageQueued()

	def loadPageData(self, data):
		self.ml.moveToIndex(0)
		jsondata = json.loads(data)
		for node in jsondata["results"]:

			if node.has_key("tpl"):
				if node.has_key("schedule_private") and node["schedule_private"] == 1:
					continue
				stream_name = str(node["tpl"][5])
				if stream_name != "":
					Title = str(node["tpl"][1])
					Name = str(node["tpl"][0])
					enc = stream_name.split('-')[-1]
					try:
						tsize = str(node["tpl"][6])
					except:
						try:
							tsize = str(node["thumb_small"]).split('/')[-3]
						except:
							tsize = str(node["thumb"]).split('/')[-3]
					Image = 'https://thumbs-orig.camsoda.com/thumbs/' + stream_name + '/' + enc + '/' + tsize + '/null/' + Name + '.jpg'
					Viewers = node["tpl"][2]
					descr = str(node["tpl"][4])
					self.filmliste.append((Title, Name, Image, Viewers, descr))
			else:
				if node.has_key("status"):
					status = str(node["status"])
				else:
					status = ""
				if status != "offline" and status != "private":
					stream_name = str(node["stream_name"])
					if stream_name != "":
						Title = str(node["display_name"])
						Name = str(node["username"])
						enc = stream_name.split('-')[-1]
						if str(node["thumb"]).startswith('//'):
							Image = "https:" + str(node["thumb"])
						else:
							try:
								tsize = str(node["tsize"])
							except:
								try:
									tsize = str(node["thumb_small"]).split('/')[-3]
								except:
									tsize = str(node["thumb"]).split('/')[-3]
							Image = 'https://thumbs-orig.camsoda.com/thumbs/' + stream_name + '/' + enc + '/' + tsize + '/null/' + Name + '.jpg'
						Viewers = node["connections"]
						descr = str(node["subject_html"])
						self.filmliste.append((Title, Name, Image, Viewers, descr))
		if len(self.filmliste):
			if self.Name != "Top Rated":
				self.filmliste.sort(key=lambda t : t[3], reverse=True)
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, 1, 1, mode=1)
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.loadPicQueued()
		else:
			self.filmliste.append((_('No livestreams found!'), None, None, None, None))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()
		self.keyLocked = False

	def showInfos(self):
		Url = self['liste'].getCurrent()[0][1]
		if Url == None:
			return
		title = self['liste'].getCurrent()[0][0]
		viewers = str(self['liste'].getCurrent()[0][3])
		descr = self['liste'].getCurrent()[0][4]
		self['name'].setText(title)
		self['handlung'].setText("Viewers: %s\n%s" % (viewers, descr))

	def keyOK(self):
		if self.keyLocked:
			return
		name = self['liste'].getCurrent()[0][1]
		self['name'].setText(_('Please wait...'))
		url = "https://www.camsoda.com/api/v1/video/vtoken/" + name + "?username=guest_" + str(random.randrange(100, 55555))
		getPage(url, agent=camsodaAgent).addCallback(self.play_stream).addErrback(self.dataError)

	def play_stream(self, data):
		jsondata = json.loads(data)
		try:
			token = str(jsondata["token"])
			app = str(jsondata["app"])
			server = str(jsondata["edge_servers"][0])
			stream_name = str(jsondata["stream_name"])
			url = "https://%s/%s/mp4:%s_aac/playlist.m3u8?token=%s" % (server, app, stream_name, token)
		except:
			url = None
		if url:
			title = self['liste'].getCurrent()[0][0]
			self['name'].setText(title)
			mp_globals.player_agent = camsodaAgent
			self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='camsoda')
		else:
			self.session.open(MessageBoxExt, _("Cam is currently offline."), MessageBoxExt.TYPE_INFO)