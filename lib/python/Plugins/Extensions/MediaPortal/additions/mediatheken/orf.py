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
		self.genreliste.append(('Sendungen A-Z', 'https://tvthek.orf.at/profiles/a-z'))
		self.genreliste.append(('Thema', 'https://tvthek.orf.at/profiles'))
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
		if self.Name == "Sendungen A-Z":
			preparse = re.findall('letter_group_headline">(.*?)</h3(.*?)</div', data, re.S)
			for (letter, data) in preparse:
				sendungen = re.findall('<article class="item">.*?img\ssrc="(.*?)".*?item_title">(.*?)</h4', data, re.S)
				if sendungen:
					for (image, title) in sendungen:
						if letter == "#":
							letter = "0"
						self.genreliste.append((decodeHtml(title), letter, title, image))
				self.genreliste.sort(key=lambda t : t[0].lower())
		elif self.Name == "Thema":
			themen = re.findall('<li class="base_list_item(?: current|) js_filter_element">.*?href="(.*?)".*?base_list_item_headline">(.*?)</h4>', data, re.S)
			if themen:
				for (url, title) in themen:
					self.genreliste.append((decodeHtml(title), url, url, default_cover))
				self.genreliste.sort(key=lambda t : t[0].lower())
		else:
			parse = re.search('subheadline">Verfügbare\sSendungen(.*?)<footer', data, re.S)
			sendungen = re.findall('base_list_item_headline">(.*?)</.*?class="episode_image">.*?src="(.*?)".*?</figure>', parse.group(1), re.S)
			if sendungen:
				self.genreliste = []
				for (title, image) in sendungen:
					self.genreliste.append((decodeHtml(title), self.Link, title, image))
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
		Letter = self['liste'].getCurrent()[0][1]
		Link = self['liste'].getCurrent()[0][2]
		if Letter:
			if Letter.startswith('/profiles'):
				Link = "http://tvthek.orf.at" + Link
				self.session.open(ORFSubGenreScreen, Name, Link)
			else:
				self.session.open(ORFFilmeListeScreen, Link, Letter, Name)

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][3]
		if streamPic == None:
			return
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		CoverHelper(self['coverArt']).getCover(streamPic)

class ORFFilmeListeScreen(MPScreen):

	def __init__(self, session, Link, Letter, Name):
		self.Link = Link
		self.Letter = Letter
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
		if self.Letter.startswith('http'):
			url = self.Letter
		else:
			url = "http://tvthek.orf.at/profiles/letter/%s" % self.Letter
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		Link = self.Link.replace('(','\(').replace(')','\)').replace('[','\[').replace(']','\]').replace('|','\|')
		parse = re.search('base_list_item_headline">'+Link+'(.*?)</ul>', data, re.S)
		folgen = re.findall('a\shref="(.*?)".*?meta_date">(.*?)</span.*?meta_time">(.*?)</span', parse.group(1), re.S)
		self.filmliste = []
		if folgen:
			for (url, date, time) in folgen:
				self.filmliste.append((decodeHtml(date + ', ' + time),url))
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