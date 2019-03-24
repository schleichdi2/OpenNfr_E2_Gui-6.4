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
from Plugins.Extensions.MediaPortal.resources.mtvdelink import MTVdeLink

config_mp.mediaportal.mtvquality = ConfigText(default="HD", fixed_size=False)

default_cover = "file://%s/mtvdecharts.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class MTVdeChartsGenreScreen(MPScreen):

	def __init__(self, session):

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"yellow": self.keyQuality
		}, -1)

		self.quality = config_mp.mediaportal.mtvquality.value

		self.keyLocked = True
		self['title'] = Label("MTV Charts")
		self['ContentTitle'] = Label("Charts:")
		self['F3'] = Label(self.quality)

		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self.genreliste = [('MTV.de\tHitlist Germany - Top100',"http://www.mtv.de/charts/c6mc86/single-top-100"),
				('MTV.de\tSingle Midweek Charts',"http://www.mtv.de/charts/n91ory/midweek-single-top-100"),
				('MTV.de\tSingle Top20',"http://www.mtv.de/charts/bcgxiq/single-top-20"),
				('MTV.de\tDance Charts',"http://www.mtv.de/charts/2ny5w9/dance-charts"),
				('MTV.de\tSingle Trending',"http://www.mtv.de/charts/9gtiy5/single-trending"),
				('MTV.de\tStreaming Charts',"http://www.mtv.de/charts/h4oi23/top100-music-streaming"),
				('MTV.de\tDeutschsprachige Single Charts Top15',"http://www.mtv.de/charts/jlyhaa/top-15-deutschsprachige-single-charts"),
				('MTV.de\tDownload Charts',"http://www.mtv.de/charts/pcbqpc/downloads-charts-single"),
				('MTV.de\tMost Watched Videos on MTV',"http://www.mtv.de/charts/n2aau3/most-watched-videos"),
				('MTV.de\tTop100 Jahrescharts 2018',"http://www.mtv.de/charts/yrk67s/top-100-jahrescharts-2016"),
				('MTV.de\tTop100 Jahrescharts 2017',"http://www.mtv.de/charts/czzmta/top-100-jahrescharts-2017"),
				('MTV.de\tTop100 Jahrescharts 2015',"http://www.mtv.de/charts/4z2jri/top-100-jahrescharts-2015"),
				('MTV.de\tTop100 Jahrescharts 2014',"http://www.mtv.de/charts/ns9mkd/top-100-jahrescharts-2014"),
				('MTV.co.uk\tSingle Top40','http://www.mtv.co.uk/music/charts/the-official-uk-top-40-singles-chart'),
				('MTV.co.uk\tUrban Charts','http://www.mtv.co.uk/music/charts/the-official-uk-urban-chart'),
				('MTV.co.uk\tThis Week\'s OMG','http://www.mtv.co.uk/music/charts/this-weeks-top-20'),
				('MTV.co.uk\tDownload Charts','http://www.mtv.co.uk/music/charts/the-official-uk-top-20-download-chart'),
				('MTV.co.uk\tOfficial Trending Charts','http://www.mtv.co.uk/music/charts/the-official-trending-chart'),
				('MTV.co.uk\tOfficial Charts Update','http://www.mtv.co.uk/music/charts/the-official-chart-update'),
				('MTV.co.uk\tOfficial UK Audio Streaming Charts','http://www.mtv.co.uk/music/charts/the-official-uk-audio-streaming-chart-top-20'),
				('MTV.it\tEuro Top20 Charts','http://classifiche.mtv.it/euro-top-20/c22lpa'),
				('MTV.it\tHitlist Italia - Single','http://classifiche.mtv.it/hitlist-italia-classifica-singoli/cgmo2j'),
				('MTV.it\tHitlist Italia - Album','http://classifiche.mtv.it/hitlist-italia-classifica-album/s8x0tp'),
				('MTV.it\tUK Charts','http://classifiche.mtv.it/classifica-musica-inglese/d901ei'),
				('MTV.it\tUSA Charts','http://classifiche.mtv.it/classifica-musica-americana/a6i0r1'),
				('MTV.it\tMost Viewed Video Ranking','http://classifiche.mtv.it/mtv-it-classifica-mtv-video/4cadoe'),
				('MTV.it\tMost Beautiful Songs To Download','http://classifiche.mtv.it/imtv-chart/xrbmn1'),
				('MTV.it\tDance Top10','http://classifiche.mtv.it/mtv-dance-top-ten-musica-dance/0w1hcj'),
				('MTV.it\tHits Top10','http://classifiche.mtv.it/mtv-hits-top-ten-video-canzoni-del-momento/kao1ot'),
				('MTV.it\tRock Top10','http://classifiche.mtv.it/mtv-rocks-classifica-rock-top-ten/5qu1no'),
				('MTV.it\tHip Hop R&B Top10','http://classifiche.mtv.it/mtv-dance-top-ten-musica-hip-hop-r-and-b/rou2ne'),
				('MTV.it\tTop30 Girl Power','http://classifiche.mtv.it/classifica-musica-pop-top-50-women-in-pop/yvxcp1'),
				('MTV.it\tTop30 Love Songs','http://classifiche.mtv.it/classifica-love-chart-canzoni-d-amore/y5qjc6'),
				('MTV.it\tTop10 2018','http://classifiche.mtv.it/hit-parade-2018/n1atw0'),
				('MTV.it\tTop50 2017','http://classifiche.mtv.it/hit-parade-2017/bb4i30'),
				('MTV.it\tTop50 2016','http://classifiche.mtv.it/hit-parade-2016/35zwc8'),
				('MTV.it\tTop50 2015','http://classifiche.mtv.it/hit-parade-2015/2wlkc9'),
				('MTV.it\tTop50 2014','http://classifiche.mtv.it/hit-parade-2014/0zervo'),
				('MTV.it\tTop50 2013','http://classifiche.mtv.it/hit-parade-2013/6who91'),
				('MTV.it\tTop50 2012','http://classifiche.mtv.it/hit-parade-2012/1mlhqb'),
				('MTV.it\tTop50 2011','http://classifiche.mtv.it/hit-parade-2011/ya6ref'),
				('MTV.it\tTop10 2010','http://classifiche.mtv.it/hit-parade-2010/2mt14y'),
				('MTV.it\tTop10 2009','http://classifiche.mtv.it/hit-parade-2009/4h7fxu'),
				('MTV.it\tTop10 2008','http://classifiche.mtv.it/hit-parade-2008/z1h4r0'),
				('MTV.it\tTop10 2007','http://classifiche.mtv.it/hit-parade-2007/n2v9fe'),
				('MTV.it\tTop10 2006','http://classifiche.mtv.it/hit-parade-2006/av2tzm'),
				('MTV.it\tTop10 2005','http://classifiche.mtv.it/hit-parade-2005/l2tki8'),
				('MTV.it\tTop10 2004','http://classifiche.mtv.it/hit-parade-2004/ndf2ek'),
				('MTV.it\tTop10 2003','http://classifiche.mtv.it/hit-parade-2003/i4bwnu'),
				('MTV.it\tTop10 2002','http://classifiche.mtv.it/hit-parade-2002/dad9pj'),
				('MTV.it\tTop10 2001','http://classifiche.mtv.it/hit-parade-2001/47uxjg'),
				('MTV.it\tTop10 2000','http://classifiche.mtv.it/hit-parade-2000/u8c07q'),
				('MTV.it\tTop10 1999','http://classifiche.mtv.it/hit-parade-1999/trb9pq'),
				('MTV.it\tTop10 1998','http://classifiche.mtv.it/hit-parade-1998/hdrshc'),
				('MTV.it\tTop10 1997','http://classifiche.mtv.it/hit-parade-1997/otnog5'),
				('MTV.it\tTop10 1996','http://classifiche.mtv.it/hit-parade-1996/ske1sc'),
				('MTV.it\tTop50 90s','http://classifiche.mtv.it/classifica-musica-anni-90-mtv-classic/njr5z7'),
				('MTV.it\tTop50 80s','http://classifiche.mtv.it/top-50-classifica-musica-anni-80-2012/p6stm9'),
				('MTV.pl\tPoland Club Charts',"http://www.mtv.pl/notowania/254-mtv-club-chart"),
				('MTV.no\tNorway Most Clicked',"http://www.mtv.no/charts/195-mtv-norway-most-clicked")]

		self.ml.setList(map(self._defaultlistleft, self.genreliste))
		self.keyLocked = False

	def keyOK(self):
		if self.keyLocked:
			return
		MTVName = self['liste'].getCurrent()[0][0]
		MTVUrl = self['liste'].getCurrent()[0][1]
		self.session.open(MTVdeChartsSongListeScreen, MTVName, MTVUrl)

	def keyQuality(self):
		if self.quality == "SD":
			self.quality = "HD"
			config_mp.mediaportal.mtvquality.value = "HD"
		elif self.quality == "HD":
			self.quality = "SD"
			config_mp.mediaportal.mtvquality.value = "SD"

		config_mp.mediaportal.mtvquality.save()
		configfile_mp.save()
		self['F3'].setText(self.quality)
		self.loadPage()

class MTVdeChartsSongListeScreen(MPScreen):

	def __init__(self, session, genreName, genreLink):
		self.genreLink = genreLink
		self.genreName = genreName
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0" : self.closeAll,
			"ok" : self.keyOK,
			"cancel" : self.keyCancel,
			"up" : self.keyUp,
			"down" : self.keyDown,
			"right" : self.keyRight,
			"left" : self.keyLeft
		}, -1)

		self.keyLocked = True
		self['title'] = Label("MTV Charts")
		self['ContentTitle'] = Label("Charts: %s" % self.genreName.replace('\t',' '))

		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml
		self.json_url = None
		self.page = 0

		self.onLayoutFinish.append(self.loadPage)

	def loadPage(self):
		self['name'].setText(_('Please wait...'))
		self.keyLocked = True
		if self.page > 0:
			url = self.json_url + "/" + str(self.page)
		else:
			url = self.genreLink
		headers = {
			'Accept':'*/*',
			'Accept-Encoding':'deflate',
			'Accept-Language':'de,en-US;q=0.7,en;q=0.3',
			}
		twAgentGetPage(url, headers=headers).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPageData(self, data):
		if "MTV.de" in self.genreName:
			if not self.json_url:
				jsonurl = re.findall('class="module intl_m327" data-tfstatic="true" data-tffeed="(.*?)"', data, re.S)
				if jsonurl:
					self.json_url = jsonurl[0]
				self.page += 1
				self.loadPage()
			else:
				json_data = json.loads(data)
				for item in json_data["result"]["data"]["items"]:
					if item.has_key('videoUrl'):
						videourl = str(item["videoUrl"])
						pos = str(item["chartPosition"]["current"])
						title = str(item["title"])
						try:
							artist = str(item["artists"][0]["name"])
						except:
							artist = str(item["shortTitle"])
						try:
							image = str(item["images"][0]["url"])
						except:
							image = None

						if "MTV.de" in self.genreName:
							vidtitle = pos + ". " + artist + " - " + title
						else:
							vidtitle = pos + ". " + title
						self.filmliste.append((vidtitle,videourl,image))
				if "nextPageURL" in data:
					self.page += 1
					self.loadPage()
				else:
					self.ml.setList(map(self._defaultlistleft, self.filmliste))
					self.showInfos()
					self.keyLocked = False
		elif "MTV.co.uk" in self.genreName:
			entity = re.findall('entity_uuid" content="(.*?)"', data, re.S)
			parse = re.findall('jQuery.extend\(Drupal.settings,\s(.*?)\);', data, re.S)
			if parse and entity:
				import requests
				try:
					s = requests.session()
					url = "http://media.mtvnservices.com/pmt/e1/access/index.html?uri=mgid:noah:video:mtv.co.uk:%s&configtype=edge" % entity[0]
					page = s.get(url, timeout=15)
					playlist = page.content
					json_pl = json.loads(playlist)
					json_data = json.loads(parse[0], "utf-8")
					items = json_data[u"vimn_videoplayer"].keys()[0]
					from collections import OrderedDict
					for key, value in json_data[u"vimn_videoplayer"][items][u"playlist_items"].iteritems():
						if value.has_key('playlist_item_index'):
							index = int(value["playlist_item_index"])
							pos = str(int(key)+1)
							title = str(value["title"])
							artist = str(value["subtitle"])
							image = str(value["parsely_data"]["metadata"]["image_url"])
							videourl = str(json_pl["feed"]["items"][index]["guid"].split(':')[-1])
							vidtitle = pos + ". " + artist + " - " + title
							self.filmliste.append((vidtitle,videourl,image,int(pos)))
							self.filmliste.sort(key=lambda t : t[3])
					self.ml.setList(map(self._defaultlistleft, self.filmliste))
					self.showInfos()
					self.keyLocked = False
				except:
					pass
		elif "MTV.it" in self.genreName:
			preparse = re.findall('class="inner-charts">(.*?)</html>', data, re.S)[0]
			parse = re.findall('<li\s{0,1}>.*?href="(.*?)".*?<em>#(\d+)</em>.*?img\ssrc="(.*?mtv.it\:(.*?)\?.*?)(?:\&amp;width|\").*?alt="(.*?)"(.*?</div)', preparse, re.S)
			if parse:
				for (videourl,pos,image,token,title,artistdata) in parse:
					image = image.replace('&amp;','&')
					videourl = "http://classifiche.mtv.it" + videourl + "&token=" + token
					artist = re.findall('<span>(.*?)</span>', artistdata, re.S)
					if artist:
						artist = artist[0]
						title = pos + ". " + artist + " - " + title
					else:
						title = pos + ". " + title
					self.filmliste.append((decodeHtml(title).replace('\\"','"').replace('\\\\','\\'),videourl,image))
				self.ml.setList(map(self._defaultlistleft, self.filmliste))
				self.showInfos()
				self.keyLocked = False
		else:
			charts = re.findall('<div\sclass="chart-position">(.*?)</div>.*?data-object-id="(.*?)">', data, re.S)
			if charts:
				part = re.search('pagePlaylist(.*?)trackingParams', data, re.S)
				if part:
					for (pos, id) in charts:
						track = re.findall('"id":%s,"title":"(.*?)","subtitle":"(.*?)","video_type":"(.*?)","video_token":"(.*?)","riptide_image_id":(".*?"|null),' % id, part.group(1), re.S)
						if track:
							for (artist,title,type,token,image_id) in track:
								image = "http://images.mtvnn.com/%s/306x172" % image_id.replace('"','')
								title = str(pos) + ". " + artist + " - " + title
								if len(token)>6:
									self.filmliste.append((decodeHtml(title).replace('\\"','"').replace('\\\\','\\'),token,image))
			self.ml.setList(map(self._defaultlistleft, self.filmliste))
			self.showInfos()
			self.keyLocked = False

	def showInfos(self):
		title = self['liste'].getCurrent()[0][0]
		coverUrl = self['liste'].getCurrent()[0][2]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(coverUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		idx = self['liste'].getSelectedIndex()
		self.session.open(MTVdeChartsPlayer, self.filmliste, int(idx) , True, self.genreName)

class MTVdeChartsPlayer(SimplePlayer):

	def __init__(self, session, playList, playIdx=0, playAll=True, listTitle=None):
		SimplePlayer.__init__(self, session, playList, playIdx=playIdx, playAll=playAll, listTitle=listTitle, ltype='mtv', forceGST=False)

	def getVideo(self):
		title = self.playList[self.playIdx][self.title_inr]
		token = self.playList[self.playIdx][1]
		imgurl = self.playList[self.playIdx][2]

		artist = ''
		p = title.find(' - ')
		if p > 0:
			artist = title[:p].strip()
			title = title[p+3:].strip()

		MTVdeLink(self.session).getLink(self.playStream, self.dataError, title, artist, token, imgurl)