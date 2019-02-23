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
default_cover = "file://%s/netzkino.png" % (config_mp.mediaportal.iconcachepath.value + "logos")
agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"

class netzKinoGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel
		}, -1)

		self['title'] = Label("Netzkino")
		self['ContentTitle'] = Label("Genre:")

		self.genreliste = []
		self.suchString = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.genreliste.append(('Suche', 'search'))
		self.genreliste.append(('Neu bei Netzkino', 'neu'))
		self.genreliste.append(('Netzkino Exklusiv', 'netzkino-exklusiv'))
		self.genreliste.append(('NetzkinoPlus Highlights', 'netzkinoplus-highlights'))
		self.genreliste.append(('Unsere Empfehlungen der Woche', 'empfehlungen_woche'))
		self.genreliste.append(('Highlights', 'highlights'))
		self.genreliste.append(('Beste Bewertung', 'beste-bewertung'))
		self.genreliste.append(('Meistgesehene Filme', 'meisgesehene_filme'))
		self.genreliste.append(('Filme mit Auszeichnungen', 'filme_mit_auszeichnungen'))
		self.genreliste.append(('Letzte Chance - Nur noch kurze Zeit verfügbar', 'letzte-chance'))
		self.genreliste.append(('Top 20', 'top-20-frontpage'))
		self.genreliste.append(('Beliebte Animes', 'beliebte-animes'))
		self.genreliste.append(('Kurzfilme', 'frontpage-kurzfilme'))
		self.genreliste.append(('Starkino', 'starkino-frontpage'))
		self.genreliste.append(('Themenkino', 'themenkino-frontpage'))
		self.genreliste.append(('HD-Kino', 'hdkino'))
		self.genreliste.append(('Animekino', 'animekino'))
		self.genreliste.append(('Actionkino', 'actionkino'))
		self.genreliste.append(('Dramakino', 'dramakino'))
		self.genreliste.append(('Thrillerkino', 'thrillerkino'))
		self.genreliste.append(('Liebesfilmkino', 'liebesfilmkino'))
		self.genreliste.append(('Scifikino', 'scifikino'))
		self.genreliste.append(('Arthousekino', 'arthousekino'))
		self.genreliste.append(('Queerkino', 'queerkino'))
		self.genreliste.append(('Spaßkino', 'spasskino'))
		self.genreliste.append(('Asiakino', 'asiakino'))
		self.genreliste.append(('Horrorkino', 'horrorkino'))
		self.genreliste.append(('Kinderkino', 'kinderkino'))
		self.genreliste.append(('Prickelkino', 'prickelkino'))
		self.genreliste.append(('Kino ab 18', 'kinoab18'))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyOK(self):
		Name = self['liste'].getCurrent()[0][0]
		genreID = self['liste'].getCurrent()[0][1]
		if Name == "Suche":
			self.suchen()
		else:
			self.session.open(netzKinoFilmeScreen, genreID, Name)

	def SuchenCallback(self, callback = None):
		if callback is not None and len(callback):
			Name = "Suche"
			self.suchString = callback
			Link = urllib.quote(self.suchString).replace(' ', '%20')
			self.session.open(netzKinoFilmeScreen, Link, Name)

class netzKinoFilmeScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreID, Name):
		self.genreID = genreID
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("Netzkino")
		self['ContentTitle'] = Label("Film Auswahl: %s" % self.Name)
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		self['name'].setText(_("Please wait..."))
		if self.Name == "Suche":
			url = "http://api.netzkino.de.simplecache.net/capi-2.0a/search?q=%s&d=www&l=de-DE&v=v1.2.0" % self.genreID
		else:
			url = "http://api.netzkino.de.simplecache.net/capi-2.0a/categories/%s.json?d=www&l=de-DE&v=v1.2.0" % self.genreID
			if self.Name == "HD-Kino":
				url = url.split('?')[0]
		getPage(url, agent=agent, headers={'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'Origin': 'http://www.netzkino.de/', 'Referer': 'http://www.netzkino.de/'}).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		json_data = json.loads(data)
		for node in json_data["posts"]:
			if node["custom_fields"].has_key('Streaming'):
				Title = str(node["title"])
				Inhalt = stripAllTags(str(node["content"]))
				if node.has_key('thumbnail'):
					Image = str(node["thumbnail"])
				else:
					Image = str(node["custom_fields"]["Artikelbild"][0])
				Stream = str(node["custom_fields"]["Streaming"][0])
				IMDb = str(node["custom_fields"]["IMDb-Bewertung"][0])
				FSK = str(node["custom_fields"]["FSK"][0])
				Jahr = str(node["custom_fields"]["Jahr"][0])
				if node["custom_fields"].has_key('Regisseur'):
					Regie = str(node["custom_fields"]["Regisseur"][0])
				else:
					Regie = "---"
				if node["custom_fields"].has_key('Stars'):
					Stars = str(node["custom_fields"]["Stars"][0])
				else:
					Stars = "---"
				Descr = "Jahr: "+Jahr+"\nIMDb-Rating: "+IMDb+"\nFSK: "+FSK+"\nRegie: "+Regie+"\nStars: "+Stars+"\n\n"+Inhalt
				Url = "http://pmd.netzkino-seite.netzkino.de/%s.mp4" % Stream
				self.filmliste.append((Title,Image,Url,Descr))
		if len(self.filmliste) == 0:
			self.filmliste.append((_("No videos found!"),default_cover,None,""))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 2, 1, None, None, 1, 1)
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][1]
		Descr = self['liste'].getCurrent()[0][3]
		self['name'].setText(Title)
		self['handlung'].setText(Descr)
		CoverHelper(self['coverArt']).getCover(Image)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = self['liste'].getCurrent()[0][2]
		Title = self['liste'].getCurrent()[0][0]
		if Link:
			self.session.open(SimplePlayer, [(Title, Link)], showPlaylist=False, ltype='netzkino')