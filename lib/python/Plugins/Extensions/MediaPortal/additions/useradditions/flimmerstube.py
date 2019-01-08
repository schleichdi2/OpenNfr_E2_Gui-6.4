# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer

BASE_URL="http://flimmerstube.com"

default_cover = "file://%s/flimmerstube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class flimmerstubeGenreScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self['title'] = Label("FlimmerStube.com")
		self['ContentTitle'] = Label("Genre:")

		self.keyLocked = True
		self.suchString = ''
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyLocked = True
		getPage(BASE_URL).addCallback(self.genreData).addErrback(self.dataError)

	def genreData(self, data):
		parse = re.search('<section class="sidebox">(.*)</section>',data, re.S)
		cats = re.findall('<a class=\'.*?\' href="(.*?)" >(.*?)</a>', parse.group(1), re.S)
		for (url, title) in cats:
			if title != "Horror Serien":
				self.genreliste.append((title, url))
		self.genreliste.sort()
		self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		Name = self['liste'].getCurrent()[0][0]
		Link = self['liste'].getCurrent()[0][1]
		self.session.open(flimmerstubeFilmScreen, Link, Name)

class flimmerstubeFilmScreen(MPScreen):

	def __init__(self, session, Link, Name):
		self.Link = Link
		self.Name = Name
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok" : self.keyOK,
			"0" : self.closeAll,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"green" : self.keyPageNumber
		}, -1)

		self['title'] = Label("FlimmerStube.com")
		self['ContentTitle'] = Label("Genre: %s" % self.Name)
		self['F2'] = Label(_("Page"))

		self['Page'] = Label(_("Page:"))
		self.keyLocked = True
		self.lastKat = ''
		self.page = 1

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.keyLocked = True
		self['name'].setText(_('Please wait...'))
		self.filmliste = []
		url = "%s%s/*%s" % (BASE_URL, self.Link, str(self.page))
		getPage(url).addCallback(self.loadData).addErrback(self.dataError)

	def loadData(self, data):
		lastp = re.search('id="num_entries">(.*?)</span>', data, re.S)
		if lastp:
			lastp = lastp.group(1)
			cat = self.Link
			if float(float(lastp)/15).is_integer():
				lastp = float(lastp) / 15
			else:
				lastp = round((float(lastp) / 15) + 0.5)
			self.lastpage = int(lastp)
		else:
			self.lastpage = 1
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))
		vSearch = re.search('<section class="content">(.*?)<aside class="sidebar">',data,re.S)
		titles = re.findall('<h4 class="ve-title">.*?<a href="(.*?)">.*?</a>.*?</h4>.*?<div class="ve-screen" title="(.*?)".*?style="background-image: url\((.*?)\);',vSearch.group(1), re.S)
		if titles:
			for (url, title, img) in titles:
				title = title.replace(' - Stream - Deutsch','').replace(' - Stream','').replace(' - DDR Scifi','').replace(' - Giallo','').replace(' - Scifi','').replace(' - Komödie','').replace(' - Exploitation','').replace(' - Horror Komödie','').replace(' - Horror Doku','').replace(' - Horror','').replace(' - Endzeit','').replace(' - Fantasy','').replace(' - Doku','').replace(' - Deutsch','').replace(' - Western','').replace(' - Krimi','').replace(' - Biografie','').replace(' - HD','').replace(' - Tormented','').replace(' - Asia Horror','').replace(' - STream','').replace(' - Stream','').replace(' German/Deutsch','')
				if not ('TV Serie' or 'Mehrteiler') in title:
					self.filmliste.append((decodeHtml(title), url, img))
		self.ml.setList(map(self._defaultlistleft, self.filmliste))
		self.ml.moveToIndex(0)
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		Title = self['liste'].getCurrent()[0][0]
		Image = self['liste'].getCurrent()[0][2]
		self['name'].setText(Title)
		CoverHelper(self['coverArt']).getCover(Image)
		Link = "%s%s" % (BASE_URL, self['liste'].getCurrent()[0][1])
		getPage(Link).addCallback(self.showInfos2).addErrback(self.dataError)

	def showInfos2(self, data):
		descr = re.findall('class="vep-descr">.*?</span>(.*?)</div>', data, re.S)
		if descr:
			descr = stripAllTags(descr[0].replace('<br /> ','<br />').replace('<br />','###NEWLINE###')).replace('###NEWLINE###','\n').strip()
			self['handlung'].setText(descr)

	def keyOK(self):
		if self.keyLocked:
			return
		Link = "%s%s" % (BASE_URL, self['liste'].getCurrent()[0][1])
		self.keyLocked = True
		getPage(Link).addCallback(self.getVideoData).addErrback(self.dataError)

	def getVideoData(self, data):
		ytUrl = re.findall('"http[s]?://www.youtube.com/(v|embed)/(.*?)\?.*?"', data, re.S)
		if ytUrl:
			Title = self['liste'].getCurrent()[0][0]
			id = ytUrl[0][1]
			if id != "MBMuPKLye_Q":
				self.session.open(YoutubePlayer,[(Title, id, None)],playAll= False,showPlaylist=False,showCover=False)
				self.keyLocked = False
			else:
				vidUrl = re.findall('Link zum Film:.*?(http://flimmerstube.com/index/.*?)<br', data, re.S)
				if vidUrl:
					getPage(vidUrl[0].strip()).addCallback(self.getVideoData).addErrback(self.dataError)
		else:
			data = data.replace('\\"', '"').replace("\\'", "'")
			dmUrl = re.findall('<iframe.*?src="(http[s]?://www.dailymotion.com/embed/video/.*?)"', data, re.S)
			if dmUrl:
				getPage(dmUrl[0]).addCallback(self.getDailymotionStream).addErrback(self.dataError)
				return
			mailruUrl = re.findall("<iframe src='(https://my.mail.ru/video/embed/\d+)", data, re.S)
			if mailruUrl:
				get_stream_link(self.session).check_link(mailruUrl[0], self.got_link)
			elif "veohFlashPlayer" in data:
				veohId = re.search('.*permalinkId=(.*?)\s{0,1}&player', data, re.S)
				if veohId:
					url = "http://www.veoh.com/api/findByPermalink?permalink=" + veohId.group(1)
					getPage(url).addCallback(self.getVeohStream).addErrback(self.dataError)
				else:
					self.session.open(MessageBoxExt, _('No supported streams found!'), MessageBoxExt.TYPE_INFO, timeout=5)
					self.keyLocked = False
			else:
				driveUrl = re.findall('<iframe.*?src="(http[s]?://drive.google.com/file/.*?/)preview"', data, re.S)
				if driveUrl:
					get_stream_link(self.session).check_link(driveUrl[0]+"edit", self.got_link)
					self.keyLocked = False
				else:
					self.session.open(MessageBoxExt, _('No supported streams found!'), MessageBoxExt.TYPE_INFO, timeout=5)
					self.keyLocked = False

	def got_link(self, stream_url):
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Title, stream_url)], showPlaylist=False, ltype='flimmerstube')

	def getDailymotionStream(self, data):
		data = data.replace("\\/", "/")
		Title = self['liste'].getCurrent()[0][0]
		stream_url = re.findall('"(240|380|480|720)".*?url":"(http[s]?://www.dailymotion.com/cdn/.*?)"', data, re.S)
		if stream_url:
			self.session.open(SimplePlayer, [(Title, stream_url[-1][1])], showPlaylist=False, ltype='flimmerstube')
		self.keyLocked = False

	def getVeohStream(self, data):
		Title = self['liste'].getCurrent()[0][0]
		stream_url = re.findall('fullPreviewHash.*?="(.*?)"', data, re.S)
		if stream_url:
			self.session.open(SimplePlayer, [(Title, stream_url[-1])], showPlaylist=False, ltype='flimmerstube')
		self.keyLocked = False

	def got_link(self, stream_url):
		self.keyLocked = False
		Title = self['liste'].getCurrent()[0][0]
		self.session.open(SimplePlayer, [(Title, stream_url)], showPlaylist=False, ltype='flimmerstube')