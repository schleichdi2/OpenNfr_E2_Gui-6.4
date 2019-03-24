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
default_cover = "file://%s/orf.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class ORFGenreScreen(MPScreen):

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

		self['title'] = Label("ORF TVthek")
		self['ContentTitle'] = Label(_("Genre:"))

		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste.append(('Sendungen A-Z', 'https://tvthek.orf.at/profiles'))
		self.genreliste.append(('Film & Serie', 'https://tvthek.orf.at/profiles/genre/Film-Serie/2703833'))
		self.genreliste.append(('Doku & Reportage', 'https://tvthek.orf.at/profiles/genre/Doku-Reportage/1173'))
		self.genreliste.append(('Information', 'https://tvthek.orf.at/profiles/genre/Information/2703825'))
		self.genreliste.append(('Kultur', 'https://tvthek.orf.at/profiles/genre/Kultur/1175'))
		self.genreliste.append(('Religion', 'https://tvthek.orf.at/profiles/genre/Religion/1655'))
		self.genreliste.append(('Regionales', 'https://tvthek.orf.at/profiles/genre/Regionales/3309573'))
		self.genreliste.append(('Wissenschaft', 'https://tvthek.orf.at/profiles/genre/Wissenschaft/13776490'))
		self.genreliste.append(('Wetter', 'https://tvthek.orf.at/profiles/genre/Wetter/2703827'))
		self.genreliste.append(('Volksgruppen', 'https://tvthek.orf.at/profiles/genre/Volksgruppen/70443'))
		self.genreliste.append(('Magazin', 'https://tvthek.orf.at/profiles/genre/Magazin/1176'))
		self.genreliste.append(('Unterhaltung', 'https://tvthek.orf.at/profiles/genre/Unterhaltung/13776489'))
		self.genreliste.append(('Talk', 'https://tvthek.orf.at/profiles/genre/Talk/13776488'))
		self.genreliste.append(('Sport', 'https://tvthek.orf.at/profiles/genre/Sport/1178'))
		self.genreliste.append(('Kinder', 'https://tvthek.orf.at/profiles/genre/Kinder/2703801'))
		self.genreliste.append(('Comedy & Satire', 'https://tvthek.orf.at/profiles/genre/Comedy-Satire/2703835'))
		self.genreliste.append(('Diskussion', 'https://tvthek.orf.at/profiles/genre/Diskussion/2703831'))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(ORFSubGenreScreen, Name, Link)

class ORFSubGenreScreen(MPScreen):

	def __init__(self, session, Name, Link):
		self.Name = Name
		self.Link = Link
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

		self['title'] = Label("ORF TVthek")
		self['ContentTitle'] = Label(_("Genre:") + " %s" % self.Name)


		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		getPage(self.Link).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		sendungen = re.findall('<article.*?title="(.*?)".*?href="(.*?)".*?img\sdata-src="(.*?)"', data, re.S)
		if sendungen:
			self.genreliste = []
			for (title, url, image) in sendungen:
				if not "AD | " in title and not "(ÖGS)" in title:
					self.genreliste.append((decodeHtml(title), url, title, image))
			self.genreliste.sort(key=lambda t : t[0].lower())
		if len(self.genreliste) == 0:
			self.genreliste.append(('Keine Sendungen gefunden!', None, None, None))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(ORFFilmeListeScreen, Link, Name)

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][3]
		if streamPic == None:
			return
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		CoverHelper(self['coverArt']).getCover(streamPic)

class ORFFilmeListeScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("ORF TVthek")
		self['ContentTitle'] = Label(_("Genre:") + " %s" % self.Name)

		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		url = self.Link
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if "other_episodes" in self.Link:
			folgen = re.findall('<article.*?href="(.*?)".*?class="time">(.*?)</span.*?class="date-as-string">(.*?)</p>', data, re.S)
			if folgen:
				for (url, time, date) in folgen:
					self.filmliste.append((decodeHtml(date + ', ' + time), url))
		else:
			folgen = re.findall('class="date">(.*?)</span.*?class="time">(.*?)</span', data, re.S)
			if folgen:
				for (date, time) in folgen:
					self.filmliste.append((decodeHtml(date + ', ' + time), self.Link))
				more = re.findall('class="related-videos">.*?&quot;(.*?)&quot;', data, re.S)
				self.Link = "https://tvthek.orf.at" + more[0].replace('&amp;','&').replace('\/','/')
				self.loadPage()
			else:
				self.filmliste.append(('Momentan ist keine Sendung in der TVthek vorhanden.', None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self['name'].setText('')

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url:
			self.session.open(ORFStreamListeScreen, url)

class ORFStreamListeScreen(MPScreen):

	def __init__(self, session, Link):
		self.Link = Link
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

		self['title'] = Label("ORF TVthek")
		self['ContentTitle'] = Label(_("Selection:"))


		self.keyLocked = True
		self.streamliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		getPage(self.Link).addCallback(self.gotPageData).addErrback(self.dataError)

	def gotPageData(self, data):
		parse = re.search('jsb_VideoPlaylist" data-jsb="(.*?)"></div>', data, re.S)
		folgen = re.findall('episode_id.*?title":"(.*?)","description":(.*?),".*?preview_image_url":"(.*?)","sources":(\[.*?\])', parse.group(1).replace('&quot;','"').replace('\/','/'), re.S)
		if folgen:
			self.streamliste = []
			for (title, desc, image, urls) in folgen[:-1]:
				url = re.search('"quality":"Q8C","quality_string":"Sehr hoch","src":"(http[s]?://apasfiis.sf.apa.at/ipad/.*?)"', urls, re.S)
				if not url:
					url = re.search('"quality":"Q6A","quality_string":"Hoch","src":"(http[s]?://apasfiis.sf.apa.at/ipad/.*?)"', urls, re.S)
				title = title.replace('\\"','"')
				if desc == "null":
					desc = ""
				else:
					desc = desc.strip('"')
				self.streamliste.append((decodeHtml(title),url.group(1).replace('\/','/').replace('https','http'),image.replace('\/','/'),desc))
			self.ml.setList(map(self._defaultlistleft, self.streamliste))
			self.keyLocked = False
			self.showInfos()

	def keyOK(self):
		if self.keyLocked:
			return
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(SimplePlayer, self.streamliste, playIdx=self['liste'].getSelectedIndex(), playAll=True, showPlaylist=False, ltype='orf')

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][2]
		if streamPic == None:
			return
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamHandlung = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(decodeHtml(streamHandlung))
		CoverHelper(self['coverArt']).getCover(streamPic)