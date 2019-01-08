# -*- coding: utf-8 -*-
#
#    Copyright (c) 2016 Billy2011, MediaPortal Team
#
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Queue
import threading
from Plugins.Extensions.MediaPortal.resources.youtubeplayer import YoutubePlayer
from Plugins.Extensions.MediaPortal.resources.menuhelper import MenuHelper
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
from Plugins.Extensions.MediaPortal.resources.keyboardext import VirtualKeyBoardExt
from Plugins.Extensions.MediaPortal.resources.choiceboxext import ChoiceBoxExt

JBTO_Version = "JUKEBOX.to"
JBTO_siteEncoding = 'utf-8'
cookies = CookieJar()
baseUrl = "http://jukebox.to"
json_headers = {
	'Accept':'application/json, text/plain, */*',
	'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
	}
agent="Mozilla/5.0 (Windows NT 6.1; rv:44.0) Gecko/20100101 Firefox/44.0"

default_cover = "file://%s/jukebox.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class show_JBTO_Genre(MenuHelper):

	def __init__(self, session, genre_url=None, genre_title="Genres"):
		self.genre_url = genre_url
		self.param_qr = ''
		self.moreButtonTxt = None
		self.limit = 0
		MenuHelper.__init__(self, session, 0, None, baseUrl, "", self._defaultlistcenter, cookieJar=cookies, default_cover=default_cover)

		self['title'] = Label(JBTO_Version)
		self['ContentTitle'] = Label(genre_title)
		self['F2'] = Label()
		self["jbto_actions"] = ActionMap(['MP_Actions'], {
			"green" :  self.moreButton,
		}, -1)

		self.onLayoutFinish.append(self.mh_initMenu)

	def mh_initMenu(self):
		self.mh_buildMenu(self.genre_url, agent=agent, headers=json_headers)

	def mh_parseCategorys(self, data):
		if not self.genre_url:
			menu = [
				(0, "/albums/top", "Popular Albums"),
				(0, "/albums/latest-releases", "Latest Releases"),
				(0, "/tracks/top", "Top 50"),
				(0, "/genres?names=Rock,%20Hip%20Hop,%20Pop,%20Country", "Popular Genres"),
				(0, "/get-search-results/%s?limit=3", "Suche..."),
				]
		elif type(data) in (str, buffer):
			menu = []
			max_len = 0
			self.moreButtonTxt = None
			self.data = json.loads(data)
			if '/genres?names' in self.genre_url:
				for item in self.data:
					genre = item['name']
					data = item['artists']
					menu.append((0, ("/genre/",data), str(genre).title()))
			else:
				if self.data.has_key('albums') and len(self.data['albums']):
					max_len = len(self.data['albums'])
					menu.append((0, "/albums/", "Albums"))
				if self.data.has_key('artists') and len(self.data['artists']):
					max_len = len(self.data['artists'])
					menu.append((0, "/artists/", "Artists"))
				if self.data.has_key('tracks') and len(self.data['tracks']):
					max_len = max(max_len,len(self.data['tracks']))
					menu.append((0, "/tracks/", "Songs"))

			if self.genre_url and ('limit=3' in self.genre_url) and max_len:
				#self.limit = 12 if max_len <= 12 else 20
				self.limit = 20
				self.moreButtonTxt = _("Get All Results")
				self['F2'].setText(self.moreButtonTxt)
			else:
				self['F2'].setText('')
		else:
			menu = None
		self.mh_genMenu2(menu)

	def mh_callGenreListScreen(self):
		if re.search('Suche...', self.mh_genreTitle):
			self.paraQuery()
		else:
			genreurl = self.mh_genreUrl[self.mh_menuLevel]
			if genreurl == '/albums/':
				self.session.open(JBTO_ListScreen, '/albums/', self.mh_genreTitle, data=(None, None, self.data, None))
			elif genreurl == '/artists/':
				self.session.open(JBTO_ListScreen, genreurl, self.mh_genreTitle, data=(None, None, self.data['artists'], None))
			elif '/genre/' in genreurl:
				self.session.open(JBTO_ListScreen, '/artists/', self.mh_genreTitle, data=(None, None, genreurl[1], None))
			elif '/genres?names' in genreurl:
				genreurl = self.mh_baseUrl + self.mh_genreUrl[0]
				self.session.open(show_JBTO_Genre, genreurl, self.mh_genreTitle)
			elif genreurl == '/tracks/':
				self.session.open(JBTO_ListScreen, genreurl, self.mh_genreTitle, data=(None, None, self.data['tracks'], None))
			else:
				genreurl = self.mh_baseUrl + genreurl
				self.session.open(JBTO_ListScreen, genreurl, self.mh_genreTitle)

	def paraQuery(self):
		#self.param_qr = ''
		self.session.openWithCallback(self.cb_paraQuery, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.param_qr, is_dialog=True, suggest_func=self.getSuggestions)

	def cb_paraQuery(self, callback = None, entry = None):
		if callback != None:
			self.param_qr = callback.strip()
			if len(self.param_qr) > 0:
				qr = quote(self.param_qr)
				genreurl = self.mh_baseUrl + self.mh_genreUrl[0] % qr
				self.session.open(show_JBTO_Genre, genreurl, _('Search Results: ')+self.param_qr)

	def moreButton(self):
		if self.moreButtonTxt:
			self.mh_genreMenu = None
			self.mh_menuLevel = 0
			self.mh_menuMaxLevel = 0
			self.mh_menuIdx = [0,0,0,0]
			self.mh_genreSelected = False
			self.mh_genreName = ["","","",""]
			self.mh_genreUrl = ["","","",""]
			self.genre_url = self.genre_url.replace('limit=3', 'limit=%d' % self.limit)
			self.mh_buildMenu(self.genre_url)

	def getSuggestions(self, text, max_res):
		url = "http://jukebox.to/get-search-results/%s?limit=3" % urllib.quote(text)
		d = twAgentGetPage(url, agent=agent, headers=json_headers, timeout=5, cookieJar=cookies)
		d.addCallback(self.gotSuggestions, max_res)
		d.addErrback(self.gotSuggestions, max_res, True)
		return d

	def gotSuggestions(self, suggestions, max_res, err=False):
		artists = ['--- Artists ---']; songs = ['--- Songs ---']; albums = ['--- Albums ---'];
		if not err and type(suggestions) in (str, buffer):
			suggestions = json.loads(suggestions)
			for item in suggestions.iteritems():
				if item[0] == 'artists':
					for x in item[1]:
						artists.append(str(x['name']))
				elif item[0] == 'tracks':
					for x in item[1]:
						songs.append("%s - %s" % (str(x['name']), str(", ".join(x['artists']))))
				elif item[0] == 'albums':
					for x in item[1]:
						albums.append("%s - %s" % (str(x['name']), str(x['artist']['name'])))
		elif err:
			printl(str(suggestions),self,'E')
		return artists+songs+albums

class JBTO_ListScreen(MPScreen, ThumbsHelper):

	def __init__(self, session, genreLink, genreName, data=None):
		self.genreLink = genreLink
		self.genreName = genreName
		self.genreData = data
		self.genreImg = data[3] if data else None
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions2", "MP_Actions"], {
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
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
			"leftRepeated" : self.keyLeftRepeated,
			"nextBouquet" : self.keyPageUp,
			"prevBouquet" : self.keyPageDown,
			"1" : self.key_1,
			"3" : self.key_3,
			"4" : self.key_4,
			"6" : self.key_6,
			"7" : self.key_7,
			"9" : self.key_9,
			"0"	: self.closeAll,
			"green" :  self.moreButton,
		}, -1)

		self.genreTitle = ""
		self['title'] = Label(JBTO_Version)
		self['Page'] = Label(_("Page:"))

		self.filmQ = Queue.Queue(0)
		self.eventL = threading.Event()
		self.keyLocked = True
		self.liste = []
		self.page = 0
		self.pages = 0
		self.pageplus = ''
		self.moreButtonTxt = None
		self.moreButtonList = None
		self.data = None
		self.setGenreStrTitle()
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.onLayoutFinish.append(self.loadPage)

	def setGenreStrTitle(self):
		genreName = "%s%s" % (self.genreTitle,self.genreName)
		self['ContentTitle'].setText(genreName)

	def loadPage(self):
		url = self.genreLink
		if self.page:
			self['page'].setText("%d / %d%s" % (self.page,self.pages,self.pageplus))

		if self.genreData != None:
			self['name'].setText(_('Please wait...'))
			self.loadPageData(self.genreData)
		else:
			self.filmQ.put(url)
			if not self.eventL.is_set():
				self.eventL.set()
				self.loadPageQueued()

	def loadPageQueued(self):
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		twAgentGetPage(url, timeout=30, cookieJar=cookies).addCallback(self.loadPageData).addErrback(self.dataError)

	def dataError(self, error):
		self.eventL.clear()
		printl(error,self,"E")
		if not 'TimeoutError' in str(error):
			message = self.session.open(MessageBoxExt, _("No results found!"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			message = self.session.open(MessageBoxExt, str(error), MessageBoxExt.TYPE_INFO)

	def loadPageData(self, content):
		self.liste = []
		self.moreButtonList = []
		dartist = ''
		if type(content) in (str, buffer):
			self.data = json.loads(content)
		elif type(content) == tuple:
			self.data = content[2]
			dartist = content[1]
		else:
			self.data = content
		if '/tracks/' in self.genreLink:
			for track in self.data:
				artist = dartist
				artists = track.get('artists')
				if not artist:
					if artists and len(artists) == 1:
						artist = str(artists[0])
					elif track.has_key('album'):
						artist = str(track['album']['artist']['name'])
				if not artists or not artist: continue
				artists = str(", ".join(artists))
				name = str(track.get('name'))
				album_name = str(track.get('album_name'))
				if track.has_key('album'):
					img = str(track['album'].get('image'))
				else:
					img = str(self.genreImg)
				url = 'http://jukebox.to/search-audio/' + urllib.quote(artist+'/'+name)
				self.liste.append((name, url, img, artists, album_name))
		elif '/albums/' in self.genreLink:
			if type(self.data) == dict:
				entrys = self.data['albums']
				dartist = self.data.get('name')
				if self.data.has_key('topTracks'):
					self.moreButtonList.append(( _('Show Popular Songs'), '/tracks/'))
				if self.data.has_key('similar'):
					self.moreButtonList.append(( _('Show Similar Artists'), '/artists/'))
			else:
				entrys = self.data
				dartist = None
			for entry in entrys:
				if not dartist:
					artist = entry.get('artist')
					if artist:
						artist = str(artist.get('name',''))
					if not artist:
						continue
				else:
					artist = str(dartist) if dartist else ''
				tracks = entry.get('tracks')
				album_name = str(entry.get('name'))
				img = str(entry.get('image'))
				self.liste.append((album_name, tracks, img, artist, album_name))
			self.liste.sort()
		elif '/artists/' in self.genreLink:
			for entry in self.data:
				artist = str(entry.get('name',''))
				tracks = None
				album_name = ''
				if entry.has_key('image_large'):
					img = str(entry.get('image_large'))
				else:
					img = str(entry.get('image_small'))
				self.liste.append((artist, tracks, img, '', album_name))
			self.liste.sort()
		if self.liste:
			if not self.page:
				self.page = 1
			if self.page > self.pages: self.pages = self.page
			self['page'].setText("%d / %d%s" % (self.page,self.pages,self.pageplus))

			self.ml.setList(map(self._defaultlistleft, self.liste))
			self['liste'].moveToIndex(0)
			self.th_ThumbsQuery(self.liste,0,1,2,None,None, self.page, self.pages)
			self.loadPic()
		else:
			self.liste.append((_("No results found!"),"","",""))
			self.ml.setList(map(self._defaultlistleft, self.liste))
			self['liste'].moveToIndex(0)
			if self.filmQ.empty():
				self.eventL.clear()
			else:
				self.loadPageQueued()

	def loadPic(self):
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)
		desc = self['liste'].getCurrent()[0][3]
		self['handlung'].setText(desc)
		if self.moreButtonList:
			self['F2'].setText(_("More"))
		else:
			self['F2'].setText('')

	def ShowCoverFileExit(self):
		self.keyLocked	= False
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()

	def keyOK(self):
		if (self.keyLocked|self.eventL.is_set()):
			return
		if '/albums/' in self.genreLink:
			tracks = self['liste'].getCurrent()[0][1]
			img = self['liste'].getCurrent()[0][2]
			album = self['liste'].getCurrent()[0][0]
			artist = self['liste'].getCurrent()[0][3]
			if tracks:
				self.session.open(JBTO_ListScreen, '/tracks/', album, data=(album, artist, tracks, img))
			else:
				artist = self['liste'].getCurrent()[0][3]
				self.getAlbum(artist, album)
		elif '/artists/' in self.genreLink:
			artist = self['liste'].getCurrent()[0][0]
			self.getArtist(artist)
		elif '/tracks/' in self.genreLink:
			self.session.open(
				JukeboxPlayer,
				self.liste,
				self['liste'].getSelectedIndex(),
				playAll = True,
				listTitle = 'JUKEBOX: ' + self.genreName,
				plType='local',
				title_inr=0,
				showCover=True,
				useResume=False
				)

	def getAlbum(self, artist, album):
		headers = json_headers
		headers.update({
			'Content-Type':'application/json;charset=utf-8',
			'Referer':'http://jukebox.to/search/%s' % quote(artist.lower())})
		content = '{"artistName":"%s","albumName":"%s"}' % (artist, album)
		url = baseUrl + '/get-album'
		twAgentGetPage(url, method='POST', agent=agent, timeout=30, cookieJar=cookies, headers=headers, postdata=content).addCallback(self.gotAlbum, artist).addErrback(self.dataError)

	def gotAlbum(self, data, artist):
		data = json.loads(data)
		tracks = data['tracks']
		img = str(data['image'])
		album = str(data['name'])
		del data
		self.session.open(JBTO_ListScreen, '/tracks/', album, data=(album, artist, tracks, img))

	def getArtist(self, artist):
		headers = json_headers
		headers.update({
			'Content-Type':'application/json;charset=utf-8',
			'Referer':'http://jukebox.to/search/%s' % quote(artist.lower())})
		content = '{"name":"%s"}' % (artist,)
		url = baseUrl + '/get-artist?top-tracks=true'
		twAgentGetPage(url, method='POST', agent=agent, timeout=30, cookieJar=cookies, headers=headers, postdata=content).addCallback(self.gotArtist).addErrback(self.dataError)

	def gotArtist(self, data):
		data = json.loads(data)
		img = str(data['image_small'])
		artist = str(data['name'])
		self.session.open(JBTO_ListScreen, '/albums/', artist, data=(None, artist, data, img))

	def moreButton(self):
		if self.keyLocked: return
		self.session.openWithCallback(self.cb_handleListSel, ChoiceBoxExt, title=_("List Selection"), list = self.moreButtonList)

	def cb_handleListSel(self, answer):
		ltype = answer and answer[1]
		if ltype == '/tracks/':
			self.session.open(JBTO_ListScreen, ltype, _('Popular Songs'), data=(None, None, self.data['topTracks'], None))
		elif  ltype == '/artists/':
			self.session.open(JBTO_ListScreen, ltype, _('Similar Artists'), data=(None, None, self.data['similar'], None))

	def keyUpRepeated(self):
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		if self.keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		if self.keyLocked:
			return
		self.loadPic()

	def keyLeftRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def keyPageDown(self):
		self.keyPageDownFast(1)

	def keyPageUp(self):
		self.keyPageUpFast(1)

	def keyPageUpFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page + step) <= self.pages:
			self.page += step
		elif self.pageplus:
			self.page += 1
			self.pages += 1
			self.pageplus = ''
		else:
			self.page = 1
		if oldpage != self.page:
			self.loadPage()

	def keyPageDownFast(self,step):
		if self.keyLocked:
			return
		oldpage = self.page
		if (self.page - step) >= 1:
			self.page -= step
		else:
			self.page = self.pages
		if oldpage != self.page:
			self.loadPage()

	def key_1(self):
		self.keyPageDownFast(2)

	def key_4(self):
		self.keyPageDownFast(5)

	def key_7(self):
		self.keyPageDownFast(10)

	def key_3(self):
		self.keyPageUpFast(2)

	def key_6(self):
		self.keyPageUpFast(5)

	def key_9(self):
		self.keyPageUpFast(10)

class JukeboxPlayer(YoutubePlayer):
	VIDEO_FMT_PRIORITY_MAP = {
		'38' : 5,
		'37' : 5,
		'22' : 4,
		'139' : 3,
		'140' : 2,
		'141' : 1,
	}
	def getVideo(self):
		streamLink = self.playList[self.playIdx][self.title_inr+1]
		twAgentGetPage(streamLink, timeout=30).addCallback(self.parseYTStream).addErrback(self.ytError)

	def parseYTStream(self, data):
		m2 = re.search('"id":"(.*?)"', data)
		if m2:
			dhVideoId = m2.group(1)
			dhTitle = self.playList[self.playIdx][self.title_inr]
			imgurl = self.playList[self.playIdx][self.title_inr+2]
			artist = self.playList[self.playIdx][self.title_inr+3]
			album = self.playList[self.playIdx][self.title_inr+4]
			fmt_map = None
			dash = False
			self._YoutubeLink(self.session).getLink(self.playStream, self.ytError, dhTitle, dhVideoId, imgurl, album=album, artist=artist, dash=dash, fmt_map=fmt_map)
		else:
			self.ytError(_('No streamlink found.'))
