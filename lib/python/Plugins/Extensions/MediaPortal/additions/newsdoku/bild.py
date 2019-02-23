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

base_url = "https://www.bild.de"
default_cover = "file://%s/bild.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class bildFirstScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Bild.de")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(("Startseite", "/video/startseite/bildchannel-home/video-home-15713248.bild.html", "3-position-teaserreihe-100-videos-47971084,contentContextId=15713248"))
		self.genreliste.append(("News", "/video/clip/news/news-15477962.bild.html", "neueste-videos-3-47902306,contentContextId=15477962"))
		self.genreliste.append(("Politik", "/video/clip/politik/politik-15714862.bild.html", "neueste-videos-3-47902306,contentContextId=15714862"))
		self.genreliste.append(("Regional", "/video/clip/regional/regional-15716814.bild.html", "neueste-videos-3-47902306,contentContextId=15716814"))
		self.genreliste.append(("Unterhaltung", "/video/clip/unterhaltung/unterhaltung-15478026.bild.html", "neueste-videos-3-47902306,contentContextId=15478026"))
		self.genreliste.append(("Sport", "/video/clip/sport/sport-15717150.bild.html", "3-position-teaserreihe-x-viele-videos-sport-42003590,contentContextId=15717150"))
		self.genreliste.append(("Auto", "/video/clip/auto/auto-15711140.bild.html", "neueste-videos-3-47902306,contentContextId=15711140"))
		self.genreliste.append(("Lifestyle", "/video/clip/lifestyle/lifestyle-15716870.bild.html", "neueste-videos-3-47902306,contentContextId=15716870"))
		self.genreliste.append(("Futtern", "/video/clip/futtern/futtern-47049016.bild.html", "neueste-videos-3-47902306,contentContextId=47049016"))
		self.genreliste.append(("Viral", "/video/clip/virale-videos/virale-videos-36659638.bild.html", "neueste-videos-3-47902306,contentContextId=36659638"))
		self.genreliste.append(("Digital", "/video/clip/digital/digital-15884812.bild.html", "neueste-videos-3-47902306,contentContextId=15884812"))
		self.genreliste.append(("Games", "/video/clip/spiele/spiele-15885178.bild.html", "neueste-videos-3-47902306,contentContextId=15885178"))
		self.genreliste.append(("Bild-Live", "/video/clip/bild-live/bild-live-54351602.bild.html", "neueste-videos-3-47902306,contentContextId=54351602"))
		self.genreliste.append(("Bild-Boxx", "/video/clip/bild-boxx/bild-boxx-34731956.bild.html", "neueste-videos-3-47902306,contentContextId=34731956"))
		self.genreliste.append(("Bild-Reporter", "/video/clip/bild-reporter/bild-reporter-36659552.bild.html", "neueste-videos-3-47902306,contentContextId=36659552"))
		self.genreliste.append(("Bild-Daily", "/video/clip/bild-daily/bild-daily-41607010.bild.html", "neueste-videos-3-47902306,contentContextId=41607010"))
		self.genreliste.append(("Tiervideos", "/video/clip/tiervideos/tiervideos-25998606.bild.html", "neueste-videos-3-47902306,contentContextId=25998606"))
		self.genreliste.append(("Motorsport", "/video/clip/motorsport/motorsport-15883290.bild.html", "neueste-videos-3-47902306,contentContextId=15883290"))
		self.genreliste.append(("Boxen", "/video/clip/boxen/boxen-15883202.bild.html", "neueste-videos-3-47902306,contentContextId=15883202"))
		self.genreliste.append(("Fußball", "/video/clip/fussball/fussball-15716788.bild.html", "neueste-videos-3-47902306,contentContextId=15716788"))
		self.genreliste.append(("Bundesliga", "/video/clip/bundesliga-bei-bild/bundesliga-bei-bild-33009168.bild.html", "neueste-videos-3-47902306,contentContextId=33009168"))
		self.genreliste.append(("2. Bundesliga", "/video/clip/2-bundesliga/zweite-liga-tore-highlights-starteite-31149208.bild.html", "neueste-videos-3-47902306,contentContextId=31149208"))
		self.genreliste.append(("Top Ligen", "/video/clip/premier-league/ligue-1-serie-a-primera-division-47933904.bild.html", "neueste-videos-3-47902306,contentContextId=47933904"))
		self.genreliste.append(("Knops Kult-Liga", "/video/clip/knops-kult-liga/knops-kult-liga-15718778.bild.html", "neueste-videos-3-47902306,contentContextId=15718778"))
		self.genreliste.append(("Leser-Reporter", "/video/clip/leserreporter/leser-reporter-15714330.bild.html", "neueste-videos-3-47902306,contentContextId=15714330"))
		self.genreliste.append(("Herr Gerstenberg", "/video/clip/word/word-39692016.bild.html", "neueste-videos-3-47902306,contentContextId=39692016"))
		self.genreliste.append(("Erotik", "/video/clip/erotik/erotik-15716836.bild.html", "neueste-videos-3-47902306,contentContextId=15716836"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def getTriesEntry(self):
		return config.ParentalControl.retries.setuppin

	def pincheckok(self, pincode):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		more = self['liste'].getCurrent()[0][2]
		if pincode:
			self.session.open(bildSecondScreen, url, name, more)

	def keyOK(self):
		name = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		more = self['liste'].getCurrent()[0][2]
		self.session.open(bildSecondScreen, url, name, more)

class bildSecondScreen(MPScreen):

	def __init__(self, session, link, name, more):
		self.link = link
		self.name = name
		self.more = more
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("Bild.de")
		self['ContentTitle'] = Label("Genre: %s" % self.name)
		self['name'] = Label(_("Please wait..."))

		self.page = 1
		self.lastpage = 1

		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.filmliste = []
		if self.page > 1:
			url = base_url + "/video/buehnenelemente/" + self.more + ",fromTeaser=%s,inTeaserReihe=true,isEndlessScrolling=true,toTeaser=25,view=teaserOnly.bild.html" % str((self.page-1)*25)
		else:
			url = base_url + self.link
		twAgentGetPage(url).addCallback(self.parseData).addErrback(self.dataError)

	def parseData(self, data):
		if 'class="btn-add">Mehr anzeigen</a>' in data:
			self.lastpage = self.page + 1
		if self.lastpage > 1:
			self['Page'].setText(_("Page:"))
			self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		videos =  re.findall('video-id.*?data-video-json="(.*?)".*?class="kicker">(.*?)</span>.*?class="headline">(.*?)</span>', data, re.S)
		for (Url, Title1, Title2) in videos:
			if not re.match('.*?bild-plus', Url):
				Url = base_url + Url
				Title = Title1.strip() + " - " + Title2.strip()
				self.filmliste.append((decodeHtml(Title), Url))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"),"",""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		self.videourl = None
		title = self['liste'].getCurrent()[0][0]
		self['name'].setText(title)
		jsonurl = self['liste'].getCurrent()[0][1]
		twAgentGetPage(jsonurl).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		parse = re.findall('description":\s"(.*?)",.*?"durationSec":(\d+),.*?poster":\s"(.*?)".*?src":"(.*?.mp4)"', data, re.S)
		if parse:
			Handlung = parse[0][0]
			m, s = divmod(int(parse[0][1]), 60)
			Runtime = _("Runtime:") + " %02d:%02d" % (m, s)
			coverUrl = parse[0][2]
			self.videourl = parse[0][3]
		else:
			coverUrl = None
			Handlung = ""
		self['handlung'].setText(Runtime + "\n\n" + decodeHtml(Handlung))
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		if self.videourl:
			self.playVideo(self.videourl)

	def playVideo(self, url):
		title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(title, url)], showPlaylist=False, ltype='bild')