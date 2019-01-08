# 	-*-	coding:	utf-8	-*-
from Plugins.Extensions.MediaPortal.plugin import _
from imports import *
from keyboardext import VirtualKeyBoardExt
from Components.Sources.StaticText import StaticText
from Components.Pixmap import MovingPixmap
from thread import allocate_lock
from debuglog import printlog as printl
import mp_globals

thumb_cookies = CookieJar()
thumb_ck = {}
thumb_agent = ''

class ThumbsHelper:
	def __init__(self):
		self.defaultThumb = False #config_mp.mediaportal.showAsThumb.value
		self.toShowThumb = False
		self.th_filmList = []
		self.th_filmnamePos = None
		self.th_filmurlPos = None
		self.th_filmimageurlPos = None
		self.th_filmnameaddPos = None
		self.th_pageregex = None
		self.th_filmpage = 1
		self.th_filmpages = 1
		self.th_mode = 0
		self.th_pagefix = 0
		self.th_maxtoken = 16
		self.th_coverlink = None

	def keyShowThumb(self):
			if self.keyLocked:
				return
			self.th_keyShowThumb(self.th_filmList, self.th_filmnamePos, self.th_filmurlPos, self.th_filmimageurlPos, self.th_filmnameaddPos, self.th_pageregex, self.th_filmpage, self.th_filmpages, mode=self.th_mode, pagefix=self.th_pagefix, maxtoken=self.th_maxtoken, coverlink=self.th_coverlink)

	def th_ThumbsQuery(self, th_filmList, th_filmnamePos, th_filmurlPos, th_filmimageurlPos=None, th_filmnameaddPos=None, th_pageregex=None, th_filmpage=1, th_filmpages=999, mode=0 , pagefix=0, maxtoken=16, coverlink=None, agent=None, cookies=None):
		self.th_filmList = th_filmList
		self.th_filmnamePos = th_filmnamePos
		self.th_filmurlPos = th_filmurlPos
		self.th_filmimageurlPos = th_filmimageurlPos
		self.th_filmnameaddPos = th_filmnameaddPos
		self.th_pageregex = th_pageregex
		self.th_filmpage = th_filmpage
		self.th_filmpages = th_filmpages
		self.th_mode = mode
		self.th_pagefix = pagefix
		self.th_maxtoken = maxtoken
		self.th_coverlink = coverlink
		global thumb_ck
		thumb_ck = cookies
		global thumb_agent
		thumb_agent = agent

		try:
			self.keyLocked = False
		except NameError:
			pass
		if self.toShowThumb == True:
			try:
				self._thumbcallback(th_filmList,th_filmnamePos,th_filmurlPos,th_filmimageurlPos,th_filmnameaddPos,th_pageregex,th_filmpage,th_filmpages)
			except AttributeError:
				pass
		elif self.defaultThumb == True:
			self.keyShowThumb()

	def th_keyShowThumb(self, th_filmList=[], th_filmnamePos=0, th_filmurlPos=1, th_filmimageurlPos=2, th_filmnameaddPos=3, th_pageregex=None, th_filmpage=1, th_filmpages=999, **kwargs):
		if self.keyLocked:
			return
		self.toShowThumb = True
		try:
			self.session.openWithCallback(self.th_showThumbCallback, ShowThumbscreen, self.th_showThumbCallback, th_filmList, th_filmnamePos, th_filmurlPos, th_filmimageurlPos, th_filmnameaddPos, th_pageregex, th_filmpage, th_filmpages, **kwargs)
		except RuntimeError:
			pass

	def th_showThumbCallback(self, *args):
		if args:
			self._thumbcallback = args[2]
			if args[1] is None:
				try:
					self['liste'].moveToIndex(args[0])
				except KeyError:
					try:
						self['liste'].moveToIndex(args[0])
					except KeyError:
						print "TH keine Filmliste gefunden"
				try:
					self.showInfos()
				except AttributeError:
					try:
						self.loadPicQueued()
					except AttributeError:
						try:
							self.loadPic()
						except AttributeError:
							pass
				self.keyOK()

			elif args[1] == -9:
				if self.defaultThumb == True:
					self.keyCancel()
				else:
					self.toShowThumb = False
					#EXIT
			elif args[1] == -5:
				self.defaultThumb = False
				self.toShowThumb = False
				#EXIT
			else:
				self.page = int(args[1])+int(args[3])
				try:
					self.keyPageUp()
				except AttributeError:
					try:
						self.keyPageUpFast()
					except AttributeError:
						print "TH Error, no PageUP found"
						#EXIT

class ShowThumbscreen(MPScreen):

	def __init__(self, session, callbacknewpage=None, filmList=[], filmnamePos=0, filmurlPos=1, filmimageurlPos=2, filmnameaddPos=3, pageregex=None, filmpage=1, filmpages=999, **kwargs):
		self._callbacknewpage = callbacknewpage
		self.filmList = filmList
		self.filmnamePos = filmnamePos
		self.filmurlPos = filmurlPos
		self.filmimageurlPos = filmimageurlPos
		self.filmimageurlPos = filmimageurlPos
		self.filmnameaddPos = filmnameaddPos
		self.pageregex = pageregex
		self.filmpage = filmpage
		self.filmpages = filmpages
		self._no_picPath = "%s/images/default_cover.png" % mp_globals.pluginPath

		mode = kwargs.get('mode', 0)
		self.method = kwargs.get('method', None)
		self.postdata = kwargs.get('postdata', None)
		self.posturl = kwargs.get('posturl', None)
		self.coverlink = kwargs.get('coverlink', None)
		self.maxtoken = kwargs.get('maxtoken', 16)
		self.pagefix = kwargs.get('pagefix', 0)
		#varliablen groessen der Thumbs definieren
		if mode == 1:
			if mp_globals.videomode == 2:
				self.picX = 350
				self.picY = 200
				self.spaceX = 55
				self.spaceY = 65
				xoffset = 120
				yoffset = 155
				fontsize = 25
				textsize = 30
			else:
				self.picX = 233
				self.picY = 133
				self.spaceX = 37
				self.spaceY = 43
				xoffset = 80
				yoffset = 103
				fontsize = 17
				textsize = 20
			self.coverframe = 'pic_frame_mode1.png'

		else:
			if mp_globals.videomode == 2:
				self.picX = 240
				self.picY = 330
				self.spaceX = 40
				self.spaceY = 65
				xoffset = 105
				yoffset = 155
				fontsize = 25
				textsize = 30
			else:
				self.picX = 160
				self.picY = 220
				self.spaceX = 27
				self.spaceY = 43
				xoffset = 70
				yoffset = 103
				fontsize = 17
				textsize = 20
			self.coverframe = 'pic_frame_mode0.png'

		# Thumbs Geometrie, groesse und Anzahl berechnen
		if mp_globals.videomode == 2:
			size_w = 1700
			size_h = 850
			thumboffset = 15
		else:
			size_w = 1133
			size_h = 566
			thumboffset = 10
		self.thumbsX = size_w / (self.spaceX + self.picX)  # thumbnails in X
		self.thumbsY = size_h / (self.spaceY + self.picY)  # thumbnails in Y
		self.thumbsC = self.thumbsX * self.thumbsY  # all thumbnails

		# Skin XML der Thumbs erstellen
		self.positionlist = []
		skincontent = ""
		posX = -1
		for x in range(self.thumbsC):
			posY = x / self.thumbsX
			posX += 1
			if posX >= self.thumbsX:
				posX = 0
			absX = xoffset + self.spaceX + (posX * (self.spaceX + self.picX))
			absY = yoffset + self.spaceY + (posY * (self.spaceY + self.picY))
			self.positionlist.append((absX, absY))  # Postition der Thumbs speichern um spaeter das Movingimage darzustellen
			skincontent += "<widget source=\"label" + str(x) + "\" render=\"Label\" position=\"" + str(absX + 2) + "," + str(absY + self.picY - 2) + "\" size=\"" + str(self.picX - 2) + "," + str(textsize * 2) + "\" font=\"" + mp_globals.font + ";" + str(fontsize) + "\" zPosition=\"3\" transparent=\"1\" valign=\"top\" halign=\"center\" foregroundColor=\"" + mp_globals.ThumbViewTextForeground + "\" backgroundColor=\"" + mp_globals.ThumbViewTextBackground + "\" />"
			skincontent += "<widget name=\"thumb" + str(x) + "\" position=\"" + str(absX + thumboffset) + "," + str(absY + thumboffset) + "\" size=\"" + str(self.picX - 2 * thumboffset) + "," + str(self.picY - 2 * thumboffset) + "\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"

		# Load Skin XML
		MPScreen.__init__(self, session, skin='MP_Thumbs')

		# Skin komlett aufbauen
		self.skin_dump = self.skin
		self.skin_dump += "<widget name=\"frame\" position=\"" + str(absX) + "," + str(absY) + "\" size=\"" + str(self.picX) + "," + str(self.picY) + "\" zPosition=\"1\" transparent=\"0\" alphatest=\"blend\" />"
		self.skin_dump += skincontent
		self.skin_dump += "</screen>"
		self.skin = self.skin_dump

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)

		self["thumb_actions"] = HelpableActionMap(self, "MP_Actions", {
			"deleteBackward" : (self.key_deleteBackward, _("Section back")),
			"deleteForward"  : (self.key_deleteForward, _("Section forward"))
		}, -2)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"5"		: self.keyCancelThumbmode,
			"cancel": self.keyCancel,
			"ok": self.keyOK,
			"left": self.key_left,
			"right": self.key_right,
			"up": self.key_up,
			"down": self.key_down,
			"green" : self.keyPageNumber,
			"red" : self.keyCancel,
			"nextBouquet" : self.nextPage,
			"prevBouquet" : self.prevPage
		}, -1)

		# Skin Variablen zuweisen
		self['F1'] = Label(_("Exit"))
		self['F2'] = Label(_("Page"))
		self['F3'] = Label("")
		self['F4'] = Label("")
		self['Page'] = Label("")
		self['page'] = Label("1/X")
		self['Thumb'] = Label(_("Loaded:"))
		self['thumb'] = Label("1/X")

		self["frame"] = MovingPixmap()
		for x in range(self.thumbsC):
			self["label" + str(x)] = StaticText()
			self["thumb" + str(x)] = Pixmap()

		self.section = 0
		self.move = 0
		self.keyLocked = True
		self.dir()
		self.onLayoutFinish.append(self.screenFinish)
		self.keyLocked = False
		self.deferreds = []

	def screenFinish(self):
		poster_path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/%s" % self.coverframe
		self["frame"].instance.setPixmap(gPixmapPtr())
		pic = LoadPixmap(cached=True, path=poster_path)
		if pic != None:
			if mp_globals.fakeScale:
				try:
					self["frame"].instance.setScale(1)
				except:
					pass
			self["frame"].instance.setPixmap(pic)

		self.makeThumb(self.filmList, self.filmnamePos, self.filmurlPos, self.filmimageurlPos, self.filmnameaddPos, self.pageregex, self.filmpage, self.filmpages)

	def makeThumb(self, filmList, filmnamePos, filmurlPos, filmimageurlPos=None, filmnameaddPos=None, pageregex=None, filmpage=1, filmpages=999):
		self.filmList = filmList
		self.filmpage = filmpage
		self.thumbfilmliste = []
		thumbsFilmname = []
		if filmpages == 0:
			self.filmpages = 999
		else:
			self.filmpages = int(filmpages)
		for item in filmList:
			if not filmnameaddPos:
				thumbsFilmname = item[filmnamePos]
			else:
				if item[filmnameaddPos]:
					thumbsFilmname = item[filmnamePos]+" "+item[filmnameaddPos].replace(' ','')
			if filmimageurlPos:
				self.thumbfilmliste.append((thumbsFilmname, item[filmurlPos], item[filmimageurlPos],pageregex),)
			else:
				self.thumbfilmliste.append((thumbsFilmname, item[filmurlPos], item[filmurlPos], pageregex),)

		index = 0
		framePos = 0
		self.filelist = []
		for x in self.thumbfilmliste:
				self.filelist.append((index, framePos))
				index += 1
				framePos += 1
				if framePos > (self.thumbsC - 1):
					framePos = 0

		self.maxentry = len(self.filelist) - 1
		self.sections = int(self.maxentry / self.thumbsC) + 1
		self.lastThumb=((self.maxentry+1)%self.thumbsC)-1
		if self.lastThumb < 0:
			self.lastThumb = self.thumbsC -1
		if self.move == -1:
			self.index = (self.lastThumb/self.thumbsX)*self.thumbsX
			self.section = self.sections-1
		elif self.move == -2:
			self.index = self.lastThumb
			self.section = self.sections-1
			if self.section < 0:
				self.section = 0
		else:
			self.section = 0
			self.index = 0
		self.move = 0
		self.layoutThumBFinished()

	def keyOK(self):
		if self.keyLocked:
			return
		filmnummer = self.section * self.thumbsC + self.index
		self._callbacknewpage(filmnummer, None, self.makeThumb, self.pagefix)

	def keyCancel(self):
		self.close(None, -9, None)

	def keyCancelThumbmode(self):
		self.close(None, -5, None)

	def keyPageNumber(self):
		self.session.openWithCallback(self.callbackkeyPageNumber, VirtualKeyBoardExt, title = (_("Enter page number")), text = "", is_dialog=True)

	def callbackkeyPageNumber(self, answer):
		if (answer is not None) and (answer.isdigit()):
			self.newfilmpage = int(answer)-1
			self.getnewpage()

	def getnewpage(self):
		self.deferCanceler()
		self.waitfordata(self.newfilmpage)
		self._callbacknewpage(None,self.newfilmpage, self.makeThumb, self.pagefix)

	def nextPage(self):
		self["frame"].hide()
		if self.filmpage == self.filmpages:
			if self.filmpage > 1:
				self.section += 1
				self.newfilmpage = 0
				self.getnewpage()
			else:
				self["frame"].show()
		else:
			self.section += 1
			self.newfilmpage = self.filmpage
			self.deferCanceler()
			self.getnewpage()

	def prevPage(self):
		self["frame"].hide()
		if self.filmpage == 1:
			if self.filmpages > 1 and not self.filmpages == 999:
				self.newfilmpage = self.filmpages-1
				self.getnewpage()
			else:
				self["frame"].show()
		else:
			self.newfilmpage = self.filmpage-2
			self.getnewpage()

	def key_left(self):
		self["frame"].hide()
		self.index -= 1
		if self.index < 0:
			self.section -= 1
			if self.section < 0:
				if self.filmpages == 1:
					if self.sections > 1:
						self.section = self.sections-1
						self.index = self.lastThumb
						self.layoutThumBFinished()
					else:
						self.index = self.lastThumb
						self.section += 1
						self.paintFrame()
				else:
					if self.filmpage == 1:
						if not self.filmpages == 999:
							self.move = -2
							self.newfilmpage = self.filmpages-1
							self.getnewpage()
						elif self.sections > 1:
							self.section = self.sections-1
							self.index = self.lastThumb
							self.layoutThumBFinished()
						else:
							self.index = self.lastThumb
							self.section += 1
							self.paintFrame()
					else:
						self.move = -2
						self.newfilmpage = self.filmpage-2
						self.getnewpage()
			else:
				self.index = self.thumbsC -1
				self.layoutThumBFinished()
		else:
			self.paintFrame()

	def key_right(self):
		self["frame"].hide()
		self.index += 1
		if self.section * self.thumbsC + self.index > self.maxentry:
			if self.filmpage == self.filmpages:
				if self.filmpages > 1:
					self.newfilmpage = 0
					self.getnewpage()
				elif self.sections > 1:
					self.section = 0
					self.index = 0
					self.layoutThumBFinished()
				else:
					self.index -= 1
					self["frame"].show()
			else:
				self.newfilmpage = self.filmpage
				self.getnewpage()
		elif self.index > self.thumbsC - 1:
			self.section += 1
			self.layoutThumBFinished()
			self.index = 0
		else:
			if self.index >= self.thumbsC:
				self.index = 0
			self.paintFrame()

	def key_up(self):
		self["frame"].hide()
		self.index -= self.thumbsX
		if self.index < 0:
			if self.section > 0:
				self.section -= 1
				self.index = self.thumbsY * self.thumbsX - self.thumbsX
				self.layoutThumBFinished()
			elif self.filmpage == 1:
				if self.filmpages > 1:
					if not self.filmpages == 999:
						self.move = -1
						self.newfilmpage = self.filmpages-1
						self.getnewpage()
					else:
						self.index += self.thumbsX
						self.paintFrame()
				elif self.sections > 1:
					self.section = self.sections-1
					self.index = (self.lastThumb/self.thumbsX)*self.thumbsX
					self.layoutThumBFinished()
				else:
					self.index += self.thumbsX
					self["frame"].show()
			else:
				self.move = -1
				self.newfilmpage = self.filmpage-2
				self.getnewpage()
		else:
			self.paintFrame()

	def key_down(self):
		self["frame"].hide()
		self.index += self.thumbsX
		if self.section * self.thumbsC + self.index > self.maxentry:
			if self.filmpage == self.filmpages:
				if self.filmpage > 1:
					self.newfilmpage = 0
					self.getnewpage()
				elif self.sections > 1:
					self.section = 0
					self.index = 0
					self.layoutThumBFinished()
				else:
					self.index = 0
					self.paintFrame()
			else:
				self.newfilmpage = self.filmpage
				self.getnewpage()
		elif self.index > self.thumbsC - 1:
			self.section += 1
			self.index = 0
			self.layoutThumBFinished()
		else:
			self.paintFrame()

	def key_deleteBackward(self):
		self.index = 0
		self.key_left()

	def key_deleteForward(self):
		self.index = self.thumbsC - 1
		self.key_right()

	def waitfordata(self, newfilmpage):
		self['page'].setText(_("Please wait... new page %s is loading") % (newfilmpage+1))
		return

	def paintFrame(self):
		if self.maxentry < self.index or self.index < 0:
			return
		pos = self.positionlist[self.filelist[self.index][1]]
		self["frame"].addMovePoint(pos[0], pos[1], 1)
		self["frame"].startMoving()
		self["frame"].show()
		if self.filmpages == 999:
			showfilmpages = "?"
		else:
			showfilmpages = self.filmpages
		if self.section:
			self['page'].setText(_("Page: %(page)s of %(pages)s  |  Section: %(section)s of %(sections)s") % {'page':self.filmpage, 'pages':showfilmpages, 'section':self.section + 1 , 'sections':self.sections })
		else:
			self['page'].setText(_("Page: %(page)s of %(pages)s  |  Section: %(section)s of %(sections)s") % {'page':self.filmpage, 'pages':showfilmpages, 'section':1 , 'sections':int(self.maxentry / self.thumbsC) + 1})

	def dir(self):
		baseDir = "/tmp"
		logDir = baseDir + "/mediaportal"
		self.coverDir = logDir + "/cover"

		try:
			os.makedirs(baseDir)
		except OSError, e:
			pass

		try:
			os.makedirs(logDir)
		except OSError, e:
			pass

		try:
			os.makedirs(self.coverDir)
		except OSError, e:
			pass

	def layoutThumBFinished(self):
		self.deferCanceler()
		self.url_list = []
		self.filmnummer = 0
		for each in range(self.section * self.thumbsC, self.section * self.thumbsC + self.thumbsC):
			try:
				title, filmlink, jpglink, imageregex = self.thumbfilmliste[each]
				jpg_store = '%s/%s.jpg' % (self.coverDir, str(self.filmnummer))
				self.filmnummer += 1
				self.url_list.append((title,jpg_store,filmlink,jpglink,imageregex))
			except IndexError:
				print "ENDE der Liste"
		self.showCoversLine()

	def showCoversLine(self):
		self.lock = allocate_lock()
		self.loadnumcounter = 0
		self.scale = AVSwitch().getFramebufferScale()
		self.picload = ePicLoad()
		size = self['thumb0'].instance.size()
		if mp_globals.fakeScale:
			self.picload.setPara((size.width(), size.height(), self.scale[0], self.scale[1], False, 1, "#00000000"))
		else:
			self.picload.setPara((size.width(), size.height(), self.scale[0], self.scale[1], False, 1, "#FF000000"))

		self.deferreds = []
		ds = defer.DeferredSemaphore(tokens=self.maxtoken)
		if len(self.url_list) != 0:
			nr = 0
			for x in range(nr,self.thumbsC):
				self["label" + str(x)].setText("")
				self["thumb" + str(x)].hide()
			for x in self.url_list:
				self['label' + str(nr)].setText(self.url_list[nr][0])
				if not self.url_list[nr][4]:
					#print "[MediaPortal] ohne linkparser"
					d = ds.run(self.download, self.url_list[nr][3], self.url_list[nr][1]).addCallback(self.ShowCoverFile, self.url_list[nr][1], nr).addErrback(self.nocoverfound, self.url_list[nr], nr).addErrback(self.dataError, self.url_list[nr], nr)
				elif self.method == 'POST':
					#print "[MediaPortal] mit linkparser und POST Mode"
					values = {'mID': self.url_list[nr][2]}
					d = ds.run(getPage, self.posturl, method='POST', postdata=urlencode(values), agent=thumb_agent, cookies=thumb_ck, headers={'Content-Type':'application/x-www-form-urlencoded'}).addCallback(self.parseUrldata, self.url_list[nr][4], self.url_list[nr][3]).addCallback(self.download, self.url_list[nr][1]).addCallback(self.ShowCoverFile, self.url_list[nr][1], nr).addErrback(self.nocoverfound, self.url_list[nr], nr).addErrback(self.dataError, self.url_list[nr], nr)
				else:
					#print "[MediaPortal] mit linkparser"
					d = ds.run(getPage, self.url_list[nr][3], agent=thumb_agent, cookies=thumb_ck).addCallback(self.parseUrldata, self.url_list[nr][4], self.url_list[nr][3]).addCallback(self.download, self.url_list[nr][1]).addCallback(self.ShowCoverFile, self.url_list[nr][1], nr).addErrback(self.nocoverfound, self.url_list[nr], nr).addErrback(self.dataError, self.url_list[nr], nr)
				self.deferreds.append(d)
				nr += 1
		self.paintFrame()

	def deferCanceler(self):
		for items in self.deferreds:
			items.cancel()

	def parseUrldata(self, data, imageregex, url):
		filmimagelink = re.findall(imageregex, data, re.S)
		if filmimagelink:
			if self.coverlink is not None:
				filmimage="%s%s" % (self.coverlink, filmimagelink[0])
				return filmimage
			elif re.match('http[s]?://', filmimagelink[0]):
				return filmimagelink[0]
			else:
				path = re.findall('(http[s]?://.*?)/',url)
				if filmimagelink[0][0] == "/":
					filmimage = "%s%s" % (path[0], filmimagelink[0])
				else:
					filmimage = "%s/%s" % (path[0], filmimagelink[0])
				return filmimage

	def ShowCoverFile(self, data, coverfile, nr):
		if data == 'no_cover':
			picPath = self._no_picPath
		else:
			picPath = coverfile
		if fileExists(picPath):
			self['thumb' + str(nr)].instance.setPixmap(gPixmapPtr())

			if mp_globals.isDreamOS:
				if self.picload.startDecode(picPath, False) == 0:
					ptr = self.picload.getData()
					if ptr != None:
						self['thumb' + str(nr)].instance.setPixmap(ptr)
						self['thumb' + str(nr)].show()
						self.lock.acquire()
						self.loadnumcounter += 1
						self.lock.release()
						self['thumb'].setText("%d / %d" % (self.loadnumcounter , self.filmnummer))
			else:
				if self.picload.startDecode(picPath, 0, 0, False) == 0:
					ptr = self.picload.getData()
					if ptr != None:
						self['thumb' + str(nr)].instance.setPixmap(ptr)
						self['thumb' + str(nr)].show()
						self.lock.acquire()
						self.loadnumcounter += 1
						self.lock.release()
						self['thumb'].setText("%d / %d" % (self.loadnumcounter , self.filmnummer))

	def download(self, image, jpg_store):
		print image
		if not image:
			return ('no_cover')
		else:
			try:
				from twagenthelper import twDownloadPage
				import requests
				requests.cookies.cookiejar_from_dict(thumb_ck, cookiejar=thumb_cookies)
				return twDownloadPage(image.replace('\/','/'), jpg_store, agent=thumb_agent, cookieJar=thumb_cookies)
			except:
				return downloadPage(image.replace('\/','/'), jpg_store, agent=thumb_agent, cookies=thumb_ck)

	def nocoverfound(self, error, url_list, nr):
		myerror = error.getErrorMessage()
		if myerror:
			self.ShowCoverFile('no_cover', url_list[1], nr)
		else:
			#print "Thumbs get is canceled"
			pass
		raise error

	def dataError(self, error, url_list, nr):
		print "dataError: (%s)" % (error.getErrorMessage(),)