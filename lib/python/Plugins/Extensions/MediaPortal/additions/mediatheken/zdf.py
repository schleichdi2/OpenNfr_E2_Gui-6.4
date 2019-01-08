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
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

BASE_URL = "https://www.zdf.de"
default_cover = "file://%s/zdf.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class ZDFGenreScreen(MPScreen):

	def __init__(self, session):
		self.keyLocked = True
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"	: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("ZDF Mediathek")
		self['ContentTitle'] = Label("Genre:")
		self['name'].setText(_("Selection:"))

		self.genreliste = []
		self.suchString = ''
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self.loadPageData()

	def loadPageData(self):
		self.genreliste = []
		self.genreliste.append(("Suche", "1", "/"))
		self.genreliste.append(("Sendungen A bis Z", "2", "/"))
		self.genreliste.append(("Sendung verpasst?", "3", "/"))
		self.genreliste.append(("Podcasts", "4", "/"))
		self.genreliste.append(("Rubriken", "5", "/"))
		self.genreliste.append(("ZDF", "6", "/"))
		self.genreliste.append(("ZDFneo", "7", "https://www.zdf.de/assets/2400_ZDFneo-100~768x432"))
		self.genreliste.append(("ZDFinfo", "8", "https://www.zdf.de/assets/2400_ZDFinfo-100~768x432"))
		self.genreliste.append(("ZDFtivi", "9", "https://www.zdf.de/assets/ueber-zdftivi-sendungstypical-100~768x432"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		cur = self['liste'].getCurrent()[0][1]
		streamPic = self['liste'].getCurrent()[0][2]
		if streamPic.startswith('http'):
			CoverHelper(self['coverArt']).getCover(streamPic)
		else:
			CoverHelper(self['coverArt']).getCover(default_cover)

	def keyOK(self):
		if self.keyLocked:
			return
		genreName = self['liste'].getCurrent()[0][0]
		genreFlag = self['liste'].getCurrent()[0][1]
		streamPic = self['liste'].getCurrent()[0][2]
		if genreFlag == "1": # Suche
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.suchString, is_dialog=True)
		elif genreFlag == "6":	# ZDF
			streamLink = "%s/suche?q=&from=&to=&sender=ZDF&attrs=&contentTypes=episode" % BASE_URL
			self.session.open(ZDFStreamScreen,streamLink,genreName,genreFlag,streamPic)
		elif genreFlag == "7":	# ZDFneo
			streamLink = "%s/suche?q=&from=&to=&sender=ZDFneo&attrs=&contentTypes=episode" % BASE_URL
			self.session.open(ZDFStreamScreen,streamLink,genreName,genreFlag,streamPic)
		elif genreFlag == "8":	# ZDFinfo
			streamLink = "%s/suche?q=&from=&to=&sender=ZDFinfo&attrs=&contentTypes=episode" % BASE_URL
			self.session.open(ZDFStreamScreen,streamLink,genreName,genreFlag,streamPic)
		elif genreFlag == "9":	# ZDFtivi
			streamLink = "%s/suche?q=&from=&to=&sender=ZDFtivi&attrs=&contentTypes=episode" % BASE_URL
			self.session.open(ZDFStreamScreen,streamLink,genreName,genreFlag,streamPic)
		else:
			self.session.open(ZDFPreSelect,genreName,genreFlag)

	def searchCallback(self, callback):
		genreFlag = self['liste'].getCurrent()[0][1]
		if callback is not None and len(callback):
			self.suchString = callback
			genreName = "Suche - " + self.suchString
			streamLink = "%s/suche?q=%s&from=&to=&sender=alle+Sender&attrs=" % (BASE_URL,callback.replace(' ', '+'))
			self.session.open(ZDFStreamScreen,streamLink,genreName,genreFlag,default_cover)

class ZDFPreSelect(MPScreen):

	def __init__(self,session,genreName,genreFlag):
		self.keyLocked = True
		self.gN = genreName
		self.gF = genreFlag
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

		self['title'] = Label("ZDF Mediathek")
		self['ContentTitle'] = Label(_("Selection:") + " %s" % self.gN)

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		url = ""
		self['name'].setText(_("Please wait..."))
		if self.gF != "4":
			self.loadPageData("")
		else:
			url = "%s/service-und-hilfe/podcast" % BASE_URL
			getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.genreliste = []
		if self.gF == "2":	# A-Z
			for c in xrange(26):
				self.genreliste.append((chr(ord('A') + c)," ",default_cover))
			self.genreliste.insert(0, ('0-9'," ",default_cover))
		elif self.gF == "3":	# Sendung verpasst?
			for q in range (0,60,1):
				if q == 0:
					s1 = " - Heute"
				elif q == 1:
					s1 = " - Gestern"
				else:
					s1 = ""
				s2 = (datetime.date.today()+datetime.timedelta(days=-q)).strftime("%d.%m.%y")
				s3 = (datetime.date.today()+datetime.timedelta(days=-q)).strftime("20%y-%m-%d")
				self.genreliste.append((s2+s1,s3,default_cover))
		elif self.gF == "4":	# Podcast
			folgen = re.findall('<td headers="t-1">(.*?)</td>.*?"t-2">(.*?)</td.*?"t-3"><a href="(.*?)"', data, re.S)
			if folgen:
				for (title,info,assetId) in folgen:
					title = decodeHtml(title)
					if "Video" in info:
						self.genreliste.append((title,assetId,default_cover))
		elif self.gF == "5":	# Rubriken
			self.genreliste.append(("Bestbewertet", "13", "https://www.zdf.de/assets/service-best-bewertet-100~768x432"))
			self.genreliste.append(("Meistgesehen", "14", "https://www.zdf.de/assets/service-meist-gesehen-100~768x432"))
			self.genreliste.append(("Comedy/Show", "1", "https://www.zdf.de/assets/comedy-100~768x432"))
			self.genreliste.append(("Doku/Wissen", "2", "https://www.zdf.de/assets/doku-wissen-102~768x432"))
			self.genreliste.append(("Filme", "3", "https://www.zdf.de/assets/film-serien-100~768x432"))
			self.genreliste.append(("Geschichte", "4", "https://www.zdf.de/assets/geschichte-106~768x432"))
			self.genreliste.append(("Kinder", "5", "https://www.zdf.de/assets/zdftivi-home-100~768x432"))
			self.genreliste.append(("Krimi", "6", "https://www.zdf.de/assets/krimi-100~768x432"))
			self.genreliste.append(("Kultur", "7", "https://www.zdf.de/assets/kultur-102~768x432"))
			self.genreliste.append(("Nachrichten", "8", "https://www.zdf.de/assets/nachrichten-100~768x432"))
			self.genreliste.append(("Politik/Gesellschaft", "9", "https://www.zdf.de/assets/politik-100~768x432"))
			self.genreliste.append(("Serien", "10", "https://www.zdf.de/assets/film-serien-100~768x432"))
			self.genreliste.append(("Sport", "11", "https://www.zdf.de/assets/zdfsport-logo-hintergrund-100~768x432"))
			self.genreliste.append(("Verbraucher", "12", "https://www.zdf.de/assets/verbraucher-100~768x432"))
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		self['name'].setText(self['liste'].getCurrent()[0][0])
		CoverHelper(self['coverArt']).getCover(self['liste'].getCurrent()[0][2])

	def keyOK(self):
		if self.keyLocked:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		extra = self['liste'].getCurrent()[0][1]
		if self.gF == "2":	# A-Z
			if auswahl == "0-9":
				streamLink = "%s/sendungen-a-z?group=0+-+9" % BASE_URL
			else:
				streamLink = "%s/sendungen-a-z?group=%s" % (BASE_URL,auswahl.lower())
			select = self.gN + " - " + auswahl
			self.session.open(ZDFPostSelect,select,self.gF,streamLink)
		elif self.gF == "3":	# Sendung verpasst?
			streamLink = "%s/sendung-verpasst?airtimeDate=%s" % (BASE_URL,extra)
			select = self.gN + " - " + auswahl
			self.session.open(ZDFStreamScreen,streamLink,select,self.gF,default_cover)
		elif self.gF == "4":	# Podcast
			select = self.gN + " - " + auswahl
			self.session.open(ZDFStreamScreen,extra,select,self.gF,default_cover)
		elif self.gF == "5":	# Rubriken
			extra = self['liste'].getCurrent()[0][1]
			if extra == "1":
				streamLink = "%s/comedy-show" % BASE_URL
			if extra == "2":
				streamLink = "%s/doku-wissen" % BASE_URL
			if extra == "3":
				streamLink = "%s/filme" % BASE_URL
			if extra == "4":
				streamLink = "%s/geschichte" % BASE_URL
			if extra == "5":
				streamLink = "%s/kinder" % BASE_URL
			if extra == "6":
				streamLink = "%s/krimi" % BASE_URL
			if extra == "7":
				streamLink = "%s/kultur" % BASE_URL
			if extra == "8":
				streamLink = "%s/nachrichten" % BASE_URL
			if extra == "9":
				streamLink = "%s/politik-gesellschaft" % BASE_URL
			if extra == "10":
				streamLink = "%s/serien" % BASE_URL
			if extra == "11":
				streamLink = "%s/sport" % BASE_URL
			if extra == "12":
				streamLink = "%s/verbraucher" % BASE_URL
			if extra == "13":
				streamLink = "%s/bestbewertet" % BASE_URL
			if extra == "14":
				streamLink = "%s/meist-gesehen" % BASE_URL
			select = self.gN + " - " + auswahl
			self.session.open(ZDFStreamScreen,streamLink,select,self.gF,default_cover)

class ZDFPostSelect(MPScreen, ThumbsHelper):

	def __init__(self,session,genreName,genreFlag,streamLink):
		self.gN = genreName
		self.gF = genreFlag
		self.streamLink = streamLink
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

		self['title'] = Label("ZDF Mediathek")
		self['ContentTitle'] = Label(_("Selection:") + " %s" % self.gN)
		self['name'] = Label(_("Please wait..."))

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_("Please wait..."))
		url = self.streamLink
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if int(self.gF) > 5:	# ZDF, ZDFneo, ZDFinfo, ZDFtivi
			self.genreliste = []
			treffer = re.findall('<div class="image">.*?<img src="(.*?)" title="(.*?)".*?<div class="text">.*?<a href=".*?<a href=".*?">(.*?)<.*?a href=".*?">.*? B.*?</div>', data, re.S)
			for (image,info,title) in treffer:
				info = info.replace("\n"," ")
				info = decodeHtml(info)
				handlung = decodeHtml(info)
				title = decodeHtml(title)
				asset = image.split('/')
				assetId = asset[3]
				image = image.replace("94x65","485x273")
				image = "%s%s" % ("http://www.zdf.de",image)
				handlung = decodeHtml(info)
				self.genreliste.append((title,assetId,handlung,image))
		else:
			self.genreliste = []
			articles = re.findall('(<article.*?</article>)', data, re.S)
			if articles:
				for article in articles:
					data = re.sub('itemprop="image" content=""','',article,flags=re.S)
					folgen = re.findall('picture class.*?class="m-16-9"\s+data-srcset="(.*?)[\"|\s].*?class="teaser-cat-category">(.*?)</span>.*?m-border\">.*?data-plusbar-title=\"(.*?)\".*?data-plusbar-url=\"(.*?)\"', data, re.S)
					if folgen:
						for (image,genre,title,url) in folgen:
							genre = decodeHtml(genre).strip().split("|")[0].strip()
							title = decodeHtml(title)
							handlung = ""
							if genre:
								if genre != "":
									handlung = handlung + "\nKontext: "+genre
							self.genreliste.append((title,url,handlung,image))
			if len(self.genreliste) == 0:
				self.genreliste.append(("Keine abspielbaren Inhalte verfügbar",None,"",default_cover))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False
		self.th_ThumbsQuery(self.genreliste, 0, 1, 3, None, None, 1, 1, mode=1)
		self.showInfos()

	def showInfos(self):
		self['handlung'].setText(self['liste'].getCurrent()[0][2])
		image = self['liste'].getCurrent()[0][3]
		self['name'].setText(self['liste'].getCurrent()[0][0])
		if self.gF != "4":
			CoverHelper(self['coverArt']).getCover(image)

	def keyOK(self):
		if self.keyLocked:
			return
		sendung = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		image = self['liste'].getCurrent()[0][3]
		if not streamLink:
			return
		select = self.gN + " - " + sendung
		self.session.open(ZDFStreamScreen,streamLink,select,self.gF,image,sendung)

class ZDFStreamScreen(MPScreen, ThumbsHelper):

	def __init__(self, session,streamLink,genreName,genreFlag,image,sendung="---"):
		self.streamL = streamLink
		self.gN = genreName
		self.gF = genreFlag
		self.sendung = sendung
		self.image = image
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
			"prevBouquet" : self.keyPageDown
			}, -1)

		self['title'] = Label("ZDF Mediathek")
		self['ContentTitle'] = Label(_("Selection:") + " %s" % self.gN)

		self.page = 1
		self.lastpage = 1
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		if self.gF == "1" or self.gF == "6" or self.gF == "7" or self.gF == "8" or self.gF == "9":
			self.streamLink = self.streamL + "&page=" + str(self.page)
		else:
			self.streamLink = self.streamL
		self['name'].setText(_("Please wait..."))
		getPage(self.streamLink).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		pages = re.search('result-count="(.*?)"',data)
		if pages != None and pages.group(1) != None:
			self.lastpage = int(int(pages.group(1)))/24+1
		if self.lastpage == 0:
			self.lastpage = 1
		if self.lastpage > 1:
			self['Page'].setText(_("Page:"))
			self['page'].setText(str(self.page)+' / '+str(self.lastpage))
		self.filmliste = []
		typ,image,title,info,assetId,sender,sendung,dur = "","","","","","","",""
		if self.gF == "3": # Sendung verpasst?
			genre = ""
			articles = re.findall('(<article.*?</article>)', data, re.S)
			for article in articles:
				data = re.sub('<div class="img-container x-large-8 x-column">','<source class="m-16-9" data-srcset="/static~Trash">',article, flags=re.S)
				data = re.sub('itemprop="image" content=""','',data,flags=re.S)
				treffer = re.findall('<article.*?picture class.*?data-srcset="(.*?)[\"|\s].*?\"teaser-label\".*?</span>(.*?)<strong>(.*?)<.*?title=\"(.*?)\".*?teaser-info.*?>(.*?)<.*?data-plusbar-id=\"(.*?)\".*?data-plusbar-path=\"(.*?)\"', data, re.S)
				if treffer:
					for (image,airtime,clock,title,dur,assetId,assetPath) in treffer:
						if "/static" in image:
							try:
								if "m-16-9" in data:
									image = re.search('<source class=\"m-16-9\".*?data-srcset=\"(.*?)[\s|\"]', data, re.S)
									image = image.group(1)
									if image.startswith('/static'):
										image = BASE_URL + image
							except:
								image = "ToBeParsed~xyz"
						if "?layout" in image:
							image = image.split("=")[0]+"="
						else:
							image = image.split("~")[0]
						if image == "ToBeParsed":
							image = self.image
						elif image[-1] == "=":
							image += "768x432"
						else:
							if not "/static" in image:
								image += "~768x432"
						title = decodeHtml(title)
						assetId = "https://api.zdf.de/content/documents/zdf/"+assetId+".json?profile=player"
						assetPath = BASE_URL + assetPath
						try:
							sendung = re.findall('class="teaser-cat\s{0,1}">.*?class="teaser-cat-brand">(.*?)</span',data,re.S)[0]
							sendung = decodeHtml(sendung)
							sendung = sendung.split("|")[-1].strip()
						except:
							sendung = "---"
						if 'class="teaser-cat ">' in data:
							try:
								genre = " ("+re.search('class="teaser-cat\s{0,1}">.*?class="teaser-cat-category">(.*?)</span',data,re.S).group(1).strip().split("|")[0].strip()+")"
							except:
								pass
						handlung = "Sendung: "+decodeHtml(sendung)+genre+"\nDatum: "+airtime+clock+"\nLaufzeit: "+dur
						self.filmliste.append((title,assetId,handlung,image,title,assetPath))
		elif self.gF == "4": # Podcast
			image = re.search('<itunes:image href="(.*?)"',data).group(1)
			treffer = re.findall('<item>.*?<title>(.*?)</ti.*?<itunes:summary>(.*?)</itunes.*?<enclosure url="(.*?)".*?<pubDate>(.*?)</pub.*?<itunes:duration>(.*?)</it', data, re.S)
			if treffer:
				for (title,info,streamLink,airtime,dur) in treffer:
					info = info.replace("\n"," ")
					info = decodeHtml(info)
					airtime = airtime.split(" +")[0]
					title = decodeHtml(title)
					m, s = divmod(int(dur), 60)
					dur = "%02d:%02d" % (m, s)
					handlung = "Kanal: Podcast"+"\nDatum: "+airtime+"\nLaufzeit: "+dur+"\n\n"+info
					self.filmliste.append((title,streamLink,handlung,image,title,''))
		else:
			articles = re.findall('(<article.*?</article>|class="content-box".*?<article)', data, re.S)
			for article in articles:
				data = re.sub('<div class="img-container x-large-8 x-column">','<source class="m-16-9" data-srcset="/static~Trash">',article, flags=re.S)
				data = re.sub('itemprop="image" content=""','',data,flags=re.S)
				airtimedata = None
				dur = ""
				sender = ""
				assetId = ""
				title = ""
				image = ""
				info = ""
				genre = ""
				if "<time datetime" in data and not "m-border" in data:
					continue
				if "Beiträge" in data:
					continue
				elif "m-border\">" in data:
					airtimedata = re.search('time datetime=.*?>(.*?)<',data)
				if airtimedata:
					airtime = airtimedata.group(1)
				else:
					airtime = '---'
				if 'm-border">' in data:
					dur = re.search('m-border\">(.*?)<',data).group(1)
					if "Bilder" in dur:
						continue
				else:
					continue
				if "data-station" in data:
					sender = re.search('data-station="(.*?)"',data).group(1)
				else:
					sender = "---"
				if not "data-plusbar-id=" in data:
					continue
				else:
					assetId = re.search('data-plusbar-id="(.*?)"',data).group(1)
				if not "data-plusbar-path=" in data:
					continue
				else:
					assetPath = re.search('data-plusbar-path="(.*?)"',data).group(1)
				if '<source class="m-16-9"' in data:
					image = re.search('<source class=\"m-16-9\".*?data-srcset=\"(.*?)[,\"]',data)
					if image:
						image = image.group(1)
						if "?layout" in image:
							image = image.split("=")[0]+"="
						else:
							image = image.split("~")[0]
					else:
						image = ""
				if image != "":
					if "/static" in image:
						try:
							if "https:\/\/www.zdf.de\/assets\/" in data:
								image = re.search('https:\\\/\\\/www.zdf.de\\\/assets\\\/(.*?)~',data)
							if image:
								image = image.group(1)
								image = "https://www.zdf.de/assets/"+image
						except:
							try:
								image = re.search("data-zdfplayer-teaser-image-overwrite=\'\{(.*?)\&#",data)
								if image:
									image = image.group(1)+"="
									image = image.replace("\/","/")
									image = "https"+image.split("https")[1]
							except:
								image = default_cover
					if image == None:
						image = default_cover
					elif image[-1] == "=":
						image += "768x432"
					else:
						image += "~768x432"
				else:
					image = default_cover
				if not 'data-plusbar-title=' in data or "Aktuell im EPG" in data:
					continue
				else:
					title = re.search('data-plusbar-title="(.*?)"',data).group(1)
				if 'description">' in data and not 'description"><' in data:
					info = re.findall('description">(.*?)<',data,re.S)[0]
					info = decodeHtml(stripAllTags(info).strip())
				try:
					sendung = re.findall('class="teaser-cat\s{0,1}">.*?class="teaser-cat-brand">(.*?)</span',data,re.S)[0]
					sendung = decodeHtml(sendung)
					sendung = sendung.split("|")[-1].strip()
				except:
					sendung = "---"
				if self.gF != "1" and sendung == "---":
					sendung = self.sendung
				if 'class="teaser-cat ">' in data:
					try:
						genre = " ("+re.search('class="teaser-cat\s{0,1}">.*?class="teaser-cat-category">(.*?)</span',data,re.S).group(1).strip().split("|")[0].strip()+")"
					except:
						pass
				handlung = "Sendung: "+decodeHtml(sendung)+genre+"\nSender: "+sender+"\nDatum: "+airtime+"\nLaufzeit: "+dur+"\n\n"+info
				assetId = "https://api.zdf.de/content/documents/zdf/"+assetId+".json?profile=player"
				assetPath = BASE_URL + assetPath
				self.filmliste.append((decodeHtml(title),assetId,handlung,image,sendung,assetPath))
			if self.filmliste == []:
				self.filmliste.append(("Keine abspielbaren Inhalte verfügbar",None,"",default_cover,None))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.th_ThumbsQuery(self.filmliste, 0, 1, 3, None, None, self.page, self.lastpage, mode=1)
		self.showInfos()

	def showInfos(self):
		self['name'].setText(self['liste'].getCurrent()[0][0])
		if self['liste'].getCurrent()[0][3] == "" or self['liste'].getCurrent()[0][3] == "/":
			CoverHelper(self['coverArt']).getCover(default_cover)
		else:
			self.streamPic = self['liste'].getCurrent()[0][3]
			self['handlung'].setText(self['liste'].getCurrent()[0][2])
			CoverHelper(self['coverArt']).getCover(self.streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		self['name'].setText(_("Please wait..."))
		streamName = self['liste'].getCurrent()[0][0]
		streamLink = self['liste'].getCurrent()[0][1]
		if self.gF == "4":	# Podcast
			playlist = []
			playlist.append((streamName, streamLink))
			self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='zdf')
			self['name'].setText(self['liste'].getCurrent()[0][0])
		else:
			streamPath = self['liste'].getCurrent()[0][5]
			getPage(streamPath).addCallback(self.getToken).addErrback(self.dataError)

	def getToken(self,data):
		self.token = re.findall('data-zdfplayer-jsb.*?apiToken":\s"(.*?)",', data, re.S)[0]
		streamLink = self['liste'].getCurrent()[0][1]
		getPage(streamLink, headers={'Api-Auth':'Bearer %s' % self.token, 'Accept':'application/vnd.de.zdf.v1.0+json'}).addCallback(self.getTemplateJson).addErrback(self.dataError)

	def getTemplateJson(self,data):
		a = json.loads(data)
		try:
			url = "https://api.zdf.de" + str(a['location'])
			getPage(url, headers={'Api-Auth':'Bearer %s' % self.token, 'Accept':'application/vnd.de.zdf.v1.0+json'}).addCallback(self.getTemplateJson).addErrback(self.dataError)
		except:
			b = a['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd-template']
			if b:
				b = b.replace('{playerId}','ngplayer_2_3')
				b = "https://api.zdf.de"+b
				getPage(str(b), headers={'Api-Auth':'Bearer %s' % self.token, 'Accept':'application/vnd.de.zdf.v1.0+json'}).addCallback(self.getContentJson).addErrback(self.dataError)

	def getContentJson(self,data):
		a = json.loads(data)
		b = []
		for x in range (0,5,1):
			try:
				b.append((a['priorityList'][1]['formitaeten'][0]['qualities'][x]['audio']['tracks'][0]['uri']))
			except:
				break
		self.keyLocked = False
		streamName = self['liste'].getCurrent()[0][0]
		c = b[0]
		c = c.replace("1496k","3296k")
		c = c.replace("p13v13","p15v13")
		c = c.replace("p13v14","p15v14")
		url = str(c).replace("https","http")
		if '.f4m' in url:
			b = []
			for x in range (0,5,1):
				try:
					b.append((a['priorityList'][0]['formitaeten'][0]['qualities'][x]['audio']['tracks'][0]['uri']))
				except:
					break
			self.keyLocked = False
			url = str(b[0])
		playlist = []
		playlist.append((streamName, url))
		self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='zdf')
		self['name'].setText(streamName)