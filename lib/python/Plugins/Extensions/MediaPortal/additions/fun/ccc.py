# -*- coding: utf-8 -*-
import os.path as os_path

from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

default_cover = "file://%s/ccc.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class CccOverviewScreen(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"	: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"right" : self.keyRight,
			"left"  : self.keyLeft
		}, -1)

		self['title'] = Label("Chaos Computer Club")
		self['ContentTitle'] = Label(_("Conference:"))
		self['name'] = Label(_("Selection:"))

		self.keyLocked = True
		self.watchdb = CccWatchDb('ccc-conferences')
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.loadConferences)

	def loadConferences(self):
		getPage('https://api.media.ccc.de/public/conferences', agent=std_headers, headers={'Content-Type': 'application/json'}).addCallback(self.parseConferences).addErrback(self.dataError)

	def parseConferences(self, data):
		watcheduids = self.watchdb.getWatched(3)

		recent = []
		alls   = []
		try:
			conferences = json.loads(data)
			if conferences.has_key('conferences'):
				for conference in conferences['conferences']:
					title = conference.get('title').encode('utf-8')
					url = conference.get('url').encode('utf-8')
					image_url = conference.get('logo_url').encode('utf-8')
					acronym = conference.get('acronym').encode('utf-8')
					if acronym in watcheduids:
						recent.append((title.strip(), url, True, False, image_url, acronym))
					else:
						alls.append((title, url, self.watchdb.hasBeenWatched(acronym), False, image_url, acronym))
		except:
			pass

		if len(recent + alls) == 0:
			alls.append((_('No conferences found!'), '', False, False, '', ''))

		alls.sort(key=lambda t : t[0].lower())

		self.filmliste = recent + alls

		self.ml.setList(map(self._defaultlistleftmarked, self.filmliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		current = self['liste'].getCurrent()[0]
		title    = current[0]
		imageUrl = current[4]
		self['name'].setText(title)
		CoverHelper(self['coverArt']).getCover(imageUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		current = self['liste'].getCurrent()[0]
		title   = current[0]
		url     = current[1]
		acronym = current[5]
		if url != '':
			self.session.open(CccConferenceScreen, url, title, acronym)

class CccConferenceScreen(MPScreen):

	def __init__(self, session, url, title, acronym):
		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"	: self.closeAll,
			"ok"	: self.keyOK,
			"cancel": self.keyCancel,
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"right" : self.keyRight,
			"left"  : self.keyLeft
		}, -1)

		self['title'] = Label("Chaos Computer Club")
		self['ContentTitle'] = Label(_("Events in %s") % title)
		self['name'] = Label(_("Selection:"))

		self.acronym = acronym
		self.watchdb = CccWatchDb('ccc-videos')
		self.keyLocked = True
		self.filmliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.url = url
		self.onLayoutFinish.append(self.loadEvents)

	def loadEvents(self):
		self.filmliste = []
		getPage(self.url, agent=std_headers, headers={'Content-Type': 'application/json'}).addCallback(self.parseEvents).addErrback(self.dataError)

	def parseEvents(self, data):
		try:
			events = json.loads(data)
			if events.has_key('events'):
				for event in events['events']:
					title = event.get('title').encode('utf-8')
					url = event.get('url').encode('utf-8')
					image_url = event.get('poster_url').encode('utf-8')
					description = ""
					if event.get('subtitle') != None:
						description += event.get('subtitle').encode('utf-8') + "\n"
					description += str(int(event.get('duration') / 60)) + ' min'
					description += ", Veröffentlichung: " + event.get('release_date').encode('utf-8')
					description += ", " + str(event.get('view_count')) + " Abrufe\n"
					if event.get('description') != None:
						description += decodeHtml(stripAllTags(event.get('description').encode('utf-8')))
					self.filmliste.append((title.strip(), url, self.watchdb.hasBeenWatched(event.get('guid').encode('utf-8')), False, image_url, description));
		except:
			pass

		if len(self.filmliste) == 0:
			self.filmliste.append((_('No events found!'), '',''))

		self.filmliste.sort(key=lambda t : t[0].lower())

		self.ml.setList(map(self._defaultlistleftmarked, self.filmliste))
		self.keyLocked = False
		self.showInfos()

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return

		title       = self['liste'].getCurrent()[0][0]
		imageUrl    = self['liste'].getCurrent()[0][4]
		description = self['liste'].getCurrent()[0][5]

		self['name'].setText(title)
		self['handlung'].setText(description)
		CoverHelper(self['coverArt']).getCover(imageUrl)

	def keyOK(self):
		if self.keyLocked:
			return
		url = self['liste'].getCurrent()[0][1]
		if url == '':
			return
		getPage(url, headers={'Content-Type': 'application/json', }).addCallback(self.parseAndPlayEvent).addErrback(self.dataError)

	def parseAndPlayEvent(self, data):
		url = None
		hq_url = None
		hqmp4_url = None
		try:
			event = json.loads(data)
			title     = event.get('title').encode('utf-8')
			image_url = event.get('poster_url').encode('utf-8')
			title     = event.get('title').encode('utf-8')
			guid      = event.get('guid').encode('utf-8')

			if event.has_key('recordings'):
				for recording in event['recordings']:
					mimetype = recording.get('mime_type').encode('utf-8')
					url = recording.get('recording_url').encode('utf-8')
					if recording.get('high_quality') and mimetype == 'video/webm':
						hq_url = url
					if recording.get('high_quality') and mimetype == 'video/mp4':
						hqmp4_url = url
					if not recording.get('high_quality') and mimetype == 'video/mp4':
						mp4_url = url
		except:
			pass

		if hqmp4_url != None:
			url = hqmp4_url
		elif mp4_url != None:
			url = mp4_url
		elif hq_url != None:
			url = hq_url

		if url == None:
			return

		self.watchdb.addWatched(guid)
		confwatchdb = CccWatchDb('ccc-conferences')
		confwatchdb.addWatched(self.acronym)
		self.session.open(SimplePlayer, [(title, url, image_url)], showPlaylist=False, ltype='ccc')
		self.loadEvents()

class CccWatchDb:

	def __init__(self, group):
		self.__dbfile = config_mp.mediaportal.watchlistpath.value + "mp_" + group
		self.watched = []
		if os_path.exists(self.__dbfile):
			rawData = open(self.__dbfile, 'r')
			for line in rawData:
				self.watched.append(line.strip())

	def addWatched(self, uid):
		if uid in self.watched:
			self.watched.remove(uid)
		self.watched.insert(0, uid)

		file = open(self.__dbfile, 'w')
		for uid in self.watched:
			file.write('%s\n' % uid)

	def hasBeenWatched(self, uid):
		return uid in self.watched

	def getWatched(self, limit = 10, offset = 0):
		return self.watched[offset:limit]