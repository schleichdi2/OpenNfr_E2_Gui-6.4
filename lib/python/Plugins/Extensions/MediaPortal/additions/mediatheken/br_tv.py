# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt

mainLink = "http://www.br.de/mediathek/video"

class BRGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin')

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("BR-Mediathek")
		self['ContentTitle'] = Label("Auswahl des Genres")

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = []
		self.genreliste.append(("Sendungen A bis Z - TV ", "1"))
		self.genreliste.append(("Suche - TV", "2"))
		self.genreliste.append(("Suche - TV ganze Sendungen", "5"))
		self.genreliste.append(("Programm Bayerisches Fernsehen", "3"))
		self.genreliste.append(("Programm ARD-alpha", "4"))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		genreName = self['liste'].getCurrent()[0][0]
		self.genreFlag = self['liste'].getCurrent()[0][1]
		if self.genreFlag == "2" or self.genreFlag == "5": # Suche TV
			self.session.openWithCallback(self.searchCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = "", is_dialog=True)
		elif self.genreFlag == "3": # Programm
			url = mainLink + "/programm/index.html?tab=BFS"
			genreName = "Bayerisches Fernsehen"
			self.session.open(BRDateScreen,url,genreName,self.genreFlag)
		elif self.genreFlag == "4": # Programm
			url = mainLink + "/programm/index.html?tab=ARD-alpha"
			genreName = "ARD-alpha"
			self.session.open(BRDateScreen,url,genreName,self.genreFlag)
		elif self.genreFlag == "1": # Sendungen A-Z
			self.session.open(BRPreSelect,genreName,self.genreFlag)
		else:
			self.session.open(BRPreSelect,genreName,self.genreFlag)

	def searchCallback(self, callbackStr):
		if callbackStr is not None:
			callbackStr = callbackStr.replace(' ','+')
			if self.genreFlag =="2":
				url = '%s/suche/suche-104.html?query=%s' % (mainLink, callbackStr)
			else:
				url = '%s/suche/suche-104.html?query=%s&entireBroadcast=true' % (mainLink,callbackStr)
			genreName = 'Suche nach: %s' % callbackStr
			self.session.open(BRStreamScreen, url, genreName, '2', '')

class BRDateScreen(MPScreen):

	def __init__(self,session,url,genreName,genreFlag):
		self.url = url
		self.gN = genreName
		self.gF = genreFlag
		MPScreen.__init__(self, session, skin='MP_Plugin')

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("BR-Mediathek")
		self['ContentTitle'] = Label("Auswahl der Sendetages")


		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText("Auswahl des Sendetages")
		self.genreliste = []
		getPage(self.url).addCallback(self.loadPageData).addErrback(self.dataError)
		self.keyLocked = False

	def loadPageData(self, data):
		self.keyLocked = True
		self.filmliste = []
		self.dateliste = []
		datelist = re.findall('<td class="( |today )">\n<a href="/mediathek/video/(.*?)".*?data-date="\d*-(\d\d-\d\d).*?title="(.*?)"', data, re.S)
		if datelist:
			for (x, url, date, datetxt) in datelist:
				url ="%s/%s" % (mainLink,url)
				self.dateliste.append((datetxt, url, date))
		if len(self.dateliste) == 0:
			self.dateliste.append(('Keine Daten gefunden.', None, None))
		self.ml.setList(map(self._defaultlistleft, self.dateliste))
		today = datetime.date.today().strftime('%m-%d')
		for position, item in enumerate(self.dateliste):
			if item[2] == today:
				self['liste'].moveToIndex(position)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		datum = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self.session.open(BRStreamScreen, url, self.gN, self.gF, datum)

class BRPreSelect(MPScreen):

	def __init__(self,session,genreName,genreFlag):
		self.gN = genreName
		self.gF = genreFlag
		MPScreen.__init__(self, session, skin='MP_Plugin')

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("BR-Mediathek")
		self['ContentTitle'] = Label("Auswahl des Buchstabens")


		self.genreliste = []
		self.keyLocked = True
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText("Auswahl des Buchstabens")
		self.genreliste = []
		for c in xrange(26):
			self.genreliste.append((chr(ord('A') + c), None))
		self.genreliste.insert(0, ('0-9', None))
		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		self.gN = auswahl
		self.session.open(BRPostSelect,auswahl,self.gN,self.gF, "dummy")

class BRPostSelect(MPScreen, ThumbsHelper):

	def __init__(self,session,auswahl,genreName,genreFlag,mediaFlag):
		self.auswahl = auswahl
		self.gN = genreName
		self.gF = genreFlag
		self.mF = mediaFlag
		MPScreen.__init__(self, session, skin='MP_Plugin')
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown
		}, -1)

		self['title'] = Label("BR-Mediathek")
		self['ContentTitle'] = Label("Auswahl der Inhalte")

		self.keyLocked = True
		self.genreliste = []
		self.page = 1
		self.lastpage = 1
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		if self.gF == "1":
			url = "%s/sendungen/index.html#letter=%s" % (mainLink,self.auswahl)
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.keyLocked = True
		self.genreliste = []
		abc = re.search('</span> '+self.auswahl+'</h3>(.*?)</ul>', data, re.S)
		if abc:
			sendungen = re.findall('<a href="/mediathek/video(.*?)" title.*?<img src="(.*?)".*?<span>(.*?)<', abc.group(1), re.S)
			if sendungen:
				for (url,img,title) in sendungen:
					img = 'http://www.br.de%s' % img
					title = decodeHtml(title)
					url = "%s/%s" % (mainLink,url)
					self.genreliste.append((title,url,img))
			else:
				self.genreliste.append(("keine Sendungen gefunden",'',None))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.keyLocked = False
			self.th_ThumbsQuery(self.genreliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()
		else:
			self.genreliste.append(("keine Sendungen gefunden",'',None))
			self.ml.setList(map(self._defaultlistleft, self.genreliste))
			self.keyLocked = False

	def showInfos(self):
		streamPic = self['liste'].getCurrent()[0][2]
		if streamPic == None:
			return
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		CoverHelper(self['coverArt']).getCover(streamPic)

	def keyOK(self):
		if self.keyLocked:
			return
		streamLink = self['liste'].getCurrent()[0][1]
		if streamLink == None:
			return
		self.session.open(BRStreamScreen,streamLink,self.gN,self.gF,'')

class BRStreamScreen(MPScreen, ThumbsHelper):

	def __init__(self, session,streamLink,genreName,genreFlag, datum):
		self.streamLink = streamLink
		self.gN = genreName
		self.gF = genreFlag
		self.datum = datum
		MPScreen.__init__(self, session, skin='MP_Plugin')
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel": self.keyCancel,
			"5" : self.keyShowThumb,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			}, -1)

		self['ContentTitle'] = Label("Auswahl des Clips")
		self['title'] = Label("BR-Mediathek")

		self['Page'] = Label(_("Page:"))
		self.page = 1
		self.lastpage = 1
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		if self.page == 1:
			url = self.streamLink
		else:
			url = "%s&page=%d" % (self.streamLink,self.page)
		print url
		getPage(url).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		self.filmliste = []
		self['page'].setText(str(self.page))
		ispages = re.findall('page=(\d+)&', data, re.S)
		if ispages:
			self.lastpage = int(max(ispages, key=lambda x:int(x)))
			if int(ispages[0]) == self.lastpage:
				self.lastpage += 1
		else:
			self.lastpage = 1
		self['page'].setText("%d / %d" % (self.page,self.lastpage))
		self.filmliste = []
		if self.gF == "3" or self.gF == "4":
			if self.gF == "3":
				sender = 'BFS'
			elif self.gF == "4":
				sender = 'ARD-alpha'
			filmbereich = re.search('<section id="'+sender+'"(.*?)</section>', data, re.S)
			if filmbereich:
				sendungen = re.findall('<dl class="epgBroadcast videoAvailable.*?data-ondemand_url="/mediathek/video/(.*?)".*?<time datetime="(.*?)".*?span>(.*?)<', filmbereich.group(1), re.S)
				if sendungen:
					for (url,zeit,title) in sendungen:
						url = "%s/%s" % (mainLink,url)
						title = decodeHtml(title)
						uhrzeit = re.search('T(\d\d:\d\d:\d\d)+', zeit)
						if uhrzeit:
							self.filmliste.append((title,url,uhrzeit.group(1)))
						else:
							self.filmliste.append((title,url,zeit))
				else:
					self.filmliste.append(("keine Sendungen gefunden", None, ''))
				self.ml.setList(map(self.BRBody1, self.filmliste))
				self.th_ThumbsQuery(self.filmliste, 0, 1, None, None, '<meta property="og:image" content="(.*?)"', self.page, self.lastpage, mode=1)
				self.showInfos()
				self.keyLocked = False
		else:
			playcontainer = re.search('containerPlayer container(.*?)containerContentTabs', data, re.S)
			if playcontainer:
				sendungen = re.findall('thumbnail".content="(.*?)".*?<h3>(.*?)</h3>.*?<li class="title">(.*?)<.*?class="duration".*?">(.*?)</time', playcontainer.group(1), re.S)
				if sendungen:
					for (image,name,episode,duration) in sendungen:
						title = '%s - %s' % (name, episode)
						url = "%s" % self.streamLink
						self.filmliste.append((decodeHtml(title),url,image,duration))

			seriescontainer = re.search('container(TeaserSeries|TeaserHome|Search) container(.*?)containerTeaser', data, re.S)
			if seriescontainer:
				sendungen = re.findall('article class=.*?a href="/mediathek/video(.*?)".*?<img src="(.*?)".*?class="name">(.*?)<.*?"episode">(.*?)<.*?class="duration".*?">(.*?)</time', seriescontainer.group(2), re.S)
				if sendungen:
					for (url,image,name,episode,duration) in sendungen:
						title = '%s - %s' % (name, episode)
						image = 'http://www.br.de%s' % image
						url = "%s%s" % (mainLink,url)
						self.filmliste.append((decodeHtml(title),url,image,duration))
			extrasuche = re.search('/mediathek/video/(suche/suche-104.html\?broadcast=.*?)\'', data, re.S)
			if extrasuche:
				f = re.search('=(.*?)$', extrasuche.group(1))
				searchstr = f.group(1)
				self.filmliste.append(('... weitere ganze Sendungen suchen von %s' % searchstr,extrasuche.group(1),None,''))
				self.filmliste.append(('... weitere Clips suchen von %s' % searchstr,extrasuche.group(1),None,''))
			if len(self.filmliste) == 0:
				self.filmliste.append(('- Keine Folgen gefunden.', None, None, ''))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.th_ThumbsQuery(self.filmliste, 0, 1, 2, None, None, self.page, self.lastpage, mode=1)
			self.showInfos()
			self.keyLocked = False

	def showInfos(self):
		streamName = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		self['name'].setText(streamName)
		if self.gF == "3" or self.gF == "4":
			if url == None:
				return
			else:
				getPage(url, agent=std_headers).addCallback(self.loadPageInfos).addErrback(self.dataError)
		else:
			streamPic = self['liste'].getCurrent()[0][2]
			if streamPic == None:
				return
			else:
				CoverHelper(self['coverArt']).getCover(streamPic)
			if url == None:
				return
			else:
				self.duration = self['liste'].getCurrent()[0][3]
				getPage(url, agent=std_headers).addCallback(self.loadPageInfos).addErrback(self.dataError)

	def loadPageInfos(self, data):
		try:
			if self.gF == "3" or self.gF == "4":
				playcontainer = re.search('containerPlayer container(.*?)containerTeaserRecommend', data, re.S)
				if playcontainer:
					info = re.findall('"thumbnail" content="(.*?)".*?class="duration".*?">(.*?)</time.*?bcastContent">.*?<p>(.*?)</p>', playcontainer.group(1), re.S)
					if info:
						for (cover, duration, handlung) in info:
							CoverHelper(self['coverArt']).getCover(cover)
							handlung = handlung.replace('<strong>','').replace('</strong>',' ').replace('<br/>','').replace('\n',' ')
							self['handlung'].setText('%s - %s' % (duration, decodeHtml(handlung)))
			else:
				handlung = re.search('bcastContent">\n<p>(.*?)</p>', data, re.S)
				if handlung:
					handlung = handlung.group(1).replace('<strong>','').replace('</strong>',' ').replace('<br/>','').replace('\n',' ')
					self['handlung'].setText('%s - %s' % (self.duration, decodeHtml(handlung)))
				else:
					self['handlung'].setText('%s - Keine Infos gefunden.' % self.duration)
		except AttributeError, e:
			print "AttributeError: ", e

	def keyOK(self):
		if self.keyLocked:
			return
		self['name'].setText(_("Please wait..."))
		title = self['liste'].getCurrent()[0][0]
		url = self['liste'].getCurrent()[0][1]
		if re.match('... weitere ganze', title):
			url = '%s/%s&entireBroadcast=true' % (mainLink,url)
			self.session.open(BRStreamScreen, url, title, '2', '')
		elif re.match('... weitere Clips', title):
			url = '%s/%s' % (mainLink,url)
			self.session.open(BRStreamScreen, url, title, '2', '')
		else:
			print url
			if url == None:
				return
			else:
				getPage(url).addCallback(self.get_xmlLink).addErrback(self.dataError)

	def get_xmlLink(self, data):
		streamxml = re.search('setup\(\{dataURL:\'/mediathek/video/(.*?)\'', data, re.S)
		if streamxml:
			url = "%s/%s" % (mainLink,streamxml.group(1))
			getPage(url).addCallback(self.get_streamLink).addErrback(self.dataError)

	def get_streamLink(self, data):
		streamlink = re.findall('(http://cdn-storage.br.de.*?.mp4)<', data)
		if streamlink:
				playlist = []
				title = self['liste'].getCurrent()[0][0]
				playlist.append((title, streamlink[-1]))
				self.session.open(SimplePlayer, playlist, showPlaylist=False, ltype='BR')