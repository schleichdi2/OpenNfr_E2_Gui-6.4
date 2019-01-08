# -*- coding: utf-8 -*-

from Plugins.Extensions.MediaPortal.plugin import _
from debuglog import printlog as printl
from enigma import ePoint, eSize
from Components.Pixmap import MultiPixmap
import mp_globals
import uuid
import Queue
import random
from messageboxext import MessageBoxExt
from choiceboxext import ChoiceBoxExt
from configlistext import ConfigListScreenExt
from Components.ProgressBar import ProgressBar
from Screens.InfoBarGenerics import *
from imports import *
from youtubelink import YoutubeLink
from mtvdelink import MTVdeLink
from cannalink import CannaLink
from eightieslink import EightiesLink
from coverhelper import CoverHelper
from Components.Pixmap import MovingPixmap
from simpleevent import SimpleEvent
from enigma import iPlayableService

try:
	f = open("/proc/stb/info/model", "r")
	model = ''.join(f.readlines()).strip()
except:
	model = ''

if mp_globals.isDreamOS:
	try:
		import merlin_musicplayer._emerlinmusicplayer
		from Components.MerlinMusicPlayerWidget import MerlinMusicPlayerWidget, MerlinMusicPlayerRMS
		MerlinMusicPlayerPresent = True
	except:
		MerlinMusicPlayerPresent = False
else:
	MerlinMusicPlayerPresent = False

is_avSetupScreen = False
try:
	from Plugins.SystemPlugins.Videomode.plugin import VideoSetup
	from Plugins.SystemPlugins.Videomode.VideoHardware import video_hw
except:
	VideoSetupPresent = False
else:
	VideoSetupPresent = True

if not VideoSetupPresent:
	try:
		from Plugins.SystemPlugins.Videomode.plugin import avSetupScreen
	except:
		VideoSetupPresent = False
	else:
		VideoSetupPresent = True
		is_avSetupScreen = True

try:
	from Plugins.SystemPlugins.AdvancedAudioSettings.plugin import AudioSetup
except:
	AudioSetupPresent = False
else:
	AudioSetupPresent = True


try:
	from Plugins.Extensions.MediaInfo.plugin import MediaInfo
	MediaInfoPresent = True
except:
	MediaInfoPresent = False

seekbuttonpos = None
STREAM_BUFFERING_ENABLED = False

def clearTmpBuffer():
	from enigma import eBackgroundFileEraser
	BgFileEraser = eBackgroundFileEraser.getInstance()
	path = config_mp.mediaportal.storagepath.value
	if os.path.exists(path):
		for fn in next(os.walk(path))[2]:
			BgFileEraser.erase(os.path.join(path,fn))

class M3U8Player:

	def __init__(self):
		from mp_hlsp import start_hls_proxy
		self._bitrate = 0
		self._check_cache = True
		start_hls_proxy()
		try:
			self.onClose.append(self._m3u8Exit)
		except:
			pass

	def _setM3U8BufferSize(self):
		service = self.session.nav.getCurrentService()
		try:
			service.streamed().setBufferSize(long(config_mp.mediaportal.hls_buffersize.value) * 1024 ** 2)
		except:
			pass

	def _getM3U8Video(self, title, url, **kwargs):
		if self._check_cache:
			if not os.path.isdir(config_mp.mediaportal.storagepath.value):
				self.session.open(MessageBoxExt, _("You've to check Your HLS-PLayer Cachepath-Setting in MP-Setup:\n") + config_mp.mediaportal.storagepath.value, MessageBoxExt.TYPE_ERROR)
				self.close()
				return
			else:
				self._check_cache = False
		self._playM3U8(title, url, **kwargs)

	def _playM3U8(self, title, url, **kwargs):
		def getProxyConfig(url):
			is_proxy_set = config_mp.mediaportal.sp_use_hlsp_with_proxy.value == 'plset' and (url.rfind(' PROXY') > 0)
			useProxy = ((config_mp.mediaportal.sp_use_hlsp_with_proxy.value == 'always') or is_proxy_set) and (config_mp.mediaportal.hlsp_proxy_host.value != 'example_proxy.com!')
			if useProxy:
				if is_proxy_set:
					url = url.replace(' PROXY', '')
				proxyhost = config_mp.mediaportal.hlsp_proxy_host.value
				proxyport = config_mp.mediaportal.hlsp_proxy_port.value
				puser = config_mp.mediaportal.hlsp_proxy_username.value
				ppass = config_mp.mediaportal.hlsp_proxy_password.value

				if '/noconnect' in proxyhost:
					proxyhost, option = proxyhost.split('/')[-2:]
				else:
					option = ''

				if not proxyhost.startswith('http'):
					proxyhost = 'http://' + proxyhost

				proxycfg = '&puser=%s&ppass=%s&purl=%s:%s/%s' % (puser, ppass, proxyhost, proxyport, option)
			else:
				proxycfg = ''
			return url, proxycfg

		if ('.m3u8' in url) or ('m3u8-aapl' in url):
			self._bitrate = self._getBandwidth()
			path = config_mp.mediaportal.storagepath.value
			ip = "127.0.0.1"
			url, proxycfg = getProxyConfig(url)
			uid = uuid.uuid1()
			if ' headers=' in url:
				url, headers = url.rsplit(' headers=',1)
				headers = '&headers=%s' % headers
			else: headers = ""

			url = 'http://%s:%d/?url=%s&bitrate=%d&path=%s%s%s&uid=%s' % (ip, mp_globals.hls_proxy_port, urllib.quote(url), self._bitrate, path, headers, proxycfg, uid)
		self._initStream(title, url, **kwargs)

	def _getBandwidth(self):
		videoPrio = int(config_mp.mediaportal.videoquali_others.value)
		if videoPrio == 2:
			bw = 4000000
		elif videoPrio == 1:
			bw = 1000000
		else:
			bw = 250000

		return bw

	def _m3u8Exit(self):
		import mp_globals
		mp_globals.yt_tmp_storage_dirty = True

class CoverSearchHelper:

	def __init__(self, coverSupp):
		self.searchCoverSupp = coverSupp
		self.hasGoogleCoverArt = False
		self.url_prev = ""

	def cleanTitle(self, title, replace_ext=True):
		for ext in ('.flv','.mp3','.mp4', '.mpeg', '.mpg', '.mkv', '.avi', '.wmv', '.ts'):
			if title.endswith(ext):
				if replace_ext:
					title = title.replace(ext, ' movie cover')
				else:
					title = title.replace(ext, '')
				break

		title = re.sub(' - folge \d+|^hd_|dts_|ac3_|_premium|kinofassung|_full_|hd_plus|\(.*?\)', '', title, flags=re.I)
		return title.replace("_"," ")

	def searchCover(self, title, fallback='', retry=False):
		if not fallback:
			fallback = ''
		if not self.searchCoverSupp or not title: return
		if self.playerMode != 'RADIO':
			self.hideSPCover()
		if self.playerMode in ('MP3','VIDEO', 'RADIO'):
			if self.playerMode == 'RADIO':
				media = 'music'
			elif self.pl_status[2] or title.endswith('.mp3'):
				media = 'music'
			else:
				media = 'movie'
			if title != 'none':
				title = self.cleanTitle(title, False)
				url = "http://itunes.apple.com/search?term=%s&limit=1&media=%s" % (urllib.quote_plus(title), media)
				getPage(url, timeout=20).addCallback(self.cb_searchCover, fallback, retry, title).addErrback(self.searchDataError)
			else:
				self.cb_searchCover('', fallback)
		else:
			self.cb_searchCover(None)

	def cb_searchCover(self, jdata, fallback='', retry=False, title=''):
		CoverSize = config_mp.mediaportal.sp_radio_cover.value
		url = None
		fallbackurl = fallback
		import json
		try:
			jdata = json.loads(jdata)
			url = jdata['results'][0]['artworkUrl100'].encode('utf-8')
			url = url.replace('100x100', '450x450').replace('https', 'http')
			self.hasGoogleCoverArt = True
		except:
			if not retry:
				x = 0
				if re.search('.*?(feat\.{0,1}\s|ft\.{0,1}\s)', title, re.I) and not retry:
					x += 1
					title = re.sub('(.*?)(?:feat\.{0,1}\s|FEAT\.{0,1}\s|Feat.{0,1}\s|ft\.{0,1}\s|FT\.{0,1}\s).*?(?::|\s)(-{0,1}\s.*?)$', r'\1\2', title)
				if "," in title:
					x += 1
					title = title.replace(',',' ')

				if x>0:
					printl(title,self,"I")
					self.searchCover(title, fallback=fallback, retry=True)
					return
				else:
					if CoverSize == "large":
						fallbackurl = 'file://' + mp_globals.pluginPath + '/images/none.png'
						url = fallbackurl
					else:
						url = fallback
			else:
				if CoverSize == "large":
					fallbackurl = 'file://' + mp_globals.pluginPath + '/images/none.png'
					url = fallbackurl
				else:
					url = fallback

		if not self.hasEmbeddedCoverArt or self.ltype == 'canna':
			if self.url_prev != url:
				self.url_prev = url
				self.showCover(url, self.cb_coverDownloaded, CoverSize=CoverSize, fallback=fallback)
		else:
			self._evEmbeddedCoverArt()

	def cb_coverDownloaded(self, download_path):
		playIdx, title, artist, album, imgurl, plType = self.pl_status
		self.pl_status = (playIdx, title, artist, album, 'file://'+download_path, plType)
		if self.pl_open:
			self.playlistQ.put(self.pl_status)
			self.pl_event.genEvent()

	def searchDataError(self, result):
		url = ""
		playIdx, title, artist, album, imgurl, plType = self.pl_status
		self.pl_status = (playIdx, title, artist, album, url, plType)
		self.pl_entry[6] = url
		printl("[SP]: cover download failed: %s " % result,self,"E")
		self.cb_searchCover(None)

class SimpleSeekHelper:

	def __init__(self):
		self["seekbarcursor"] = MovingPixmap()
		self["seekbarcursor"].hide()
		self["seekbartime"] = Label()
		self["seekbartime"].hide()
		self.cursorTimer = eTimer()
		self.BgCoverShow = eTimer()
		self.BgCoverHide = eTimer()
		if mp_globals.isDreamOS:
			self.cursorTimer_conn = self.cursorTimer.timeout.connect(self.__updateCursor)
			self.BgCoverShow_conn = self.BgCoverShow.timeout.connect(self.__BgCoverShow)
			self.BgCoverHide_conn = self.BgCoverHide.timeout.connect(self.__BgCoverHide)
		else:
			self.cursorTimer.callback.append(self.__updateCursor)
			self.BgCoverShow.callback.append(self.__BgCoverShow)
			self.BgCoverHide.callback.append(self.__BgCoverHide)
		self.cursorShown = False
		self.seekBarShown = False
		self.seekBarLocked = False
		self.isNumberSeek = False
		self.counter = 0
		self.onHide.append(self.__seekBarHide)
		self.onShow.append(self.__seekBarShown)
		self.resetMySpass()

	def initSeek(self):
		global seekbuttonpos
		#if not seekbuttonpos:
		seekbuttonpos = self["seekbarcursor"].instance.position()
		self.percent = 0.0
		self.length = None
		self.cursorShown = False
		self.counter = 1
		service = self.session.nav.getCurrentService()
		if service:
			self.seek = service.seek()
			if self.seek:
				self.length = self.seek.getLength()
				position = self.seek.getPlayPosition()
				if self.length[1] and position[1]:
					if self.myspass_len:
						self.length[1] = self.myspass_len
						position[1] += self.myspass_ofs
					else:
						self.myspass_len = self.length[1]
						self.mySpassPath = self.session.nav.getCurrentlyPlayingServiceReference().getPath()
						if '/myspass' in self.mySpassPath:
							self.isMySpass = True
						elif 'file=retro-tv' in self.mySpassPath:
							#self.isRetroTv = True
							#self.isMySpass = True
							pass
						elif 'eroprofile.com' in self.mySpassPath:
							#self.isEroprofile = True
							#self.isMySpass = True
							pass
						elif 'media.hdporn.net' in self.mySpassPath:
							self.isMySpass = True

					self.percent = float(position[1]) * 100.0 / float(self.length[1])
					if not self.isNumberSeek:
						InfoBarShowHide.lockShow(self)
						self.seekBarLocked = True
						self["seekbartime"].show()
						self.cursorTimer.start(200, False)

	def __BgCoverShow(self):
		self.RadioBg['BgCover'].show()
		self.RadioBg['BgTitle'].hide()
		self.RadioBg['cover'].hide()
		if MerlinMusicPlayerPresent:
				self.RadioBg['rms0'].hide()
				self.RadioBg['rms1'].hide()
		if self.ltype != 'canna':
			InfoBarShowHide.lockShow(self)

	def __BgCoverHide(self):
		self.RadioBg['BgCover'].hide()
		self.RadioBg['BgTitle'].show()
		self.RadioBg['cover'].show()
		if MerlinMusicPlayerPresent:
				self.RadioBg['rms0'].show()
				self.RadioBg['rms1'].show()
		if self.ltype != 'canna':
			InfoBarShowHide.unlockShow(self)

	def __seekBarShown(self):
		self.seekBarShown = True
		if self.playerMode == "RADIO":
			self.BgCoverShow.start(200, 1)

	def __seekBarHide(self):
		self.seekBarShown = False
		if self.playerMode == "RADIO":
			self.BgCoverHide.start(200, 1)

	def toggleShow(self):
		if self.seekBarLocked:
			self.seekOK()
		else:
			InfoBarShowHide.toggleShow(self)

	def showInfoBar(self):
		if not self.seekBarShown:
			InfoBarShowHide.toggleShow(self)

	def __updateCursor(self):
		if self.length:
			x = seekbuttonpos.x() + int(mp_globals.sp_seekbar_factor * self.percent)
			self["seekbarcursor"].moveTo(x, seekbuttonpos.y(), 1)
			self["seekbarcursor"].startMoving()
			pts = int(float(self.length[1]) / 100.0 * self.percent)
			self["seekbartime"].setText("%d:%02d" % ((pts/60/90000), ((pts/90000)%60)))
			if not self.cursorShown:
				if not self.counter:
					self.cursorShown = True
					self["seekbarcursor"].show()
				else:
					self.counter -= 1

	def seekExit(self):
		if not self.isNumberSeek:
			self.seekBarLocked = False
			self.cursorTimer.stop()
			self.unlockShow()
			self["seekbarcursor"].hide()
			self["seekbarcursor"].moveTo(seekbuttonpos.x(), seekbuttonpos.y(), 1)
			self["seekbarcursor"].startMoving()
			self["seekbartime"].hide()
		else:
			self.isNumberSeek = False

	def seekOK(self):
		if self.length:
			seekpos = float(self.length[1]) / 100.0 * self.percent
			if self.isMySpass:
				self.myspass_ofs = seekpos
				self.doMySpassSeekTo(seekpos)
			else:
				self.seek.seekTo(int(seekpos))
				self.seekExit()
		else:
			self.seekExit()

	def seekLeft(self):
		self.percent -= float(config_mp.mediaportal.sp_seekbar_sensibility.value) / 10.0
		if self.percent < 0.0:
			self.percent = 0.0

	def seekRight(self):
		self.percent += float(config_mp.mediaportal.sp_seekbar_sensibility.value) / 10.0
		if self.percent > 100.0:
			self.percent = 100.0

	def numberKeySeek(self, val):
		if self.dash:
			return
		if self.length:
			length = float(self.length[1])
			if length > 0.0:
				pts = int(length / 100.0 * self.percent) + val * 90000
				self.percent = pts * 100 / length
				if self.percent < 0.0:
					self.percent = 0.0
				elif self.percent > 100.0:
					self.percent = 100.0

				self.seekOK()
				if config.usage.show_infobar_on_skip.value:
					self.doShow()
			else:
				return

	def doMySpassSeekTo(self, seekpos):
		service = self.session.nav.getCurrentService()
		title = service.info().getName()
		path = self.mySpassPath
		seeksecs = seekpos / 90000
		if self.isRetroTv:
			url = "%s&start=%ld" % (path.split('&')[0], int(seeksecs*145000))
		elif self.isEroprofile:
			url = "%s&start=%f" % (path.split('&start')[0], seeksecs)
		else:
			url = "%s?start=%f" % (path.split('?start')[0], seeksecs)
		sref = eServiceReference(0x1001, 0, url)
		sref.setName(title)
		self.seekExit()
		self.session.nav.stopService()
		self.session.nav.playService(sref)

	def restartMySpass(self):
		self.resetMySpass()
		self.doMySpassSeekTo(0L)

	def resetMySpass(self):
		self.myspass_ofs = 0L
		self.myspass_len = 0L
		self.mySpassPath = None
		self.isMySpass = False
		self.isEroprofile = False
		self.isRetroTv = False
		self.isNumberSeek = False

	def cancelSeek(self):
		if self.seekBarLocked:
			self.seekExit()

	def Key1(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(-int(config.seek.selfdefined_13.value))

	def Key3(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(int(config.seek.selfdefined_13.value))

	def Key4(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(-int(config.seek.selfdefined_46.value))

	def Key6(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(int(config.seek.selfdefined_46.value))

	def Key7(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(-int(config.seek.selfdefined_79.value))

	def Key9(self):
		self.isNumberSeek = True
		self.initSeek()
		self.numberKeySeek(int(config.seek.selfdefined_79.value))

	def moveSkinUp(self):
		if self.seekBarShown and self.playerMode != "RADIO":
			orgpos = self.instance.position()
			orgheight = self.instance.size().height()
			self.skinYPos = orgpos.y()
			if self.skinYPos >= 0 - orgheight:
				self.skinYPos -= 50
				self.instance.move(ePoint(orgpos.x(), self.skinYPos))

	def moveSkinDown(self):
		if self.seekBarShown and self.playerMode != "RADIO":
			orgpos = self.instance.position()
			desktopSize = getDesktop(0).size()
			self.skinYPos = orgpos.y()
			if self.skinYPos <= desktopSize.height():
				self.skinYPos += 50
				self.instance.move(ePoint(orgpos.x(), self.skinYPos))

class SimplePlayerResume:

	def __init__(self):
		self.posTrackerActive = False
		self.currService = None
		self.eof_resume = False
		self.use_sp_resume = config_mp.mediaportal.sp_on_movie_start.value != "start"
		self.posTrackerTimer = eTimer()
		self.eofResumeTimer = eTimer()
		if mp_globals.isDreamOS:
			self.posTrackerTimer_conn = self.posTrackerTimer.timeout.connect(self.savePlayPosition)
			self.eofResumeTimer_conn = self.eofResumeTimer.timeout.connect(self.resetEOFResumeFlag)
		else:
			self.posTrackerTimer.callback.append(self.savePlayPosition)
			self.eofResumeTimer.callback.append(self.resetEOFResumeFlag)
		self.eofResumeFlag = False
		self.lruKey = ""

		self.onClose.append(self.stopPlayPositionTracker)

	def initPlayPositionTracker(self, lru_key):
		if self.use_sp_resume and lru_key and not self.posTrackerActive and not self.playerMode in ('MP3',):
			self.currService = None
			self.eofResumeFlag = False
			self.posTrackerActive = True
			self.lruKey = lru_key
			self.posTrackerTimer.start(1000*3, True)

	def stopPlayPositionTracker(self):
		if self.posTrackerActive:
			self.posTrackerTimer.stop()
			self.posTrackerActive = False
		self.eofResumeTimer.stop()

	def savePlayPosition(self, is_eof=False):
		if self.posTrackerActive:
			if is_eof and not self.lruKey in mp_globals.lruCache:
				return

			if not self.currService:
				service = self.session.nav.getCurrentService()
				if service:
					seek = service.seek()
					if seek:
						length = seek.getLength()
						position = seek.getPlayPosition()
						if length[1] > 0 and position[1] > 0:
							if self.lruKey in mp_globals.lruCache:
								lru_value = mp_globals.lruCache[self.lruKey]
								if length[1]+5*90000 > lru_value[0]:
									self.resumePlayback(lru_value[0], lru_value[1])
							self.currService = service
						else:
							return self.posTrackerTimer.start(1000*3, True)
				self.posTrackerTimer.start(1000*15, True)
			else:
				seek = self.currService.seek()
				if seek:
					length = seek.getLength()[1]
					position = seek.getPlayPosition()[1]
					mp_globals.lruCache[self.lruKey] = (length, position)

	def resumePlayback(self, length, last):
		self.resume_point = last
		if (length > 0) and abs(length - last) < 5*90000:
			return
		l = last / 90000
		if self.eof_resume or (config_mp.mediaportal.sp_on_movie_start.value == "resume" and not mp_globals.yt_download_runs):
			self.eof_resume = False
			self.session.openWithCallback(self.playLastCB, MessageBoxExt, _("Resuming playback"), timeout=2, type=MessageBoxExt.TYPE_INFO)
		elif config_mp.mediaportal.sp_on_movie_start.value == "ask" and not mp_globals.yt_download_runs:
			self.session.openWithCallback(self.playLastCB, MessageBoxExt, _("Do you want to resume this playback?") + "\n" + (_("Resume position at %s") % ("%d:%02d:%02d" % (l/3600, l%3600/60, l%60))), timeout=10)

	def resetEOFResumeFlag(self):
		self.eofResumeFlag = False

	def resumeEOF(self):
		if self.use_sp_resume and self.posTrackerActive and self.lruKey in mp_globals.lruCache:
			self.savePlayPosition(is_eof=True)
			lru_value = mp_globals.lruCache[self.lruKey]
			if (lru_value[1]+90000*120) < lru_value[0]:
				if self.eofResumeFlag:
					return True
				self.eofResumeFlag = True
				self.eofResumeTimer.start(1000*15, True)
				self.doSeek(0)
				self.setSeekState(self.SEEK_STATE_PLAY)
				self.eof_resume = True
				self.resumePlayback(lru_value[0], lru_value[1])
				return True
			else:
				self.stopPlayPositionTracker()
				mp_globals.lruCache.cache.pop()

		return False

	def playLastCB(self, answer):
		if answer == True:
			self.doSeek(self.resume_point)
		elif self.lruKey in mp_globals.lruCache:
			del mp_globals.lruCache[self.lruKey]

		self.hideAfterResume()

	def hideAfterResume(self):
		if isinstance(self, InfoBarShowHide):
			self.hide()

class SimplePlaylist(MPScreen):

	def __init__(self, session, playList, playIdx, playMode, listTitle=None, plType='local', title_inr=0, queue=None, mp_event=None, listEntryPar=None, playFunc=None, playerMode=None):

		MPScreen.__init__(self, session, skin='MP_Playlist')

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)

		self["actions"] = ActionMap(["OkCancelActions",'MediaPlayerSeekActions',"EPGSelectActions",'ColorActions','InfobarActions'],
		{
			'cancel':	self.exit,
			'red':		self.exit,
			'green':	self.toPlayer,
			'yellow':	self.changePlaymode,
			'blue':		self.deleteEntry,
			'ok': 		self.ok
		}, -2)

		self.playList = playList
		self.playIdx = playIdx
		self.listTitle = listTitle
		self.plType = plType
		self.title_inr = title_inr
		self.playlistQ = queue
		self.event = mp_event
		self.listEntryPar = listEntryPar
		self.playMode = playMode
		self.playFunc = playFunc
		self.playerMode = playerMode

		self["title"] = Label("")
		self["coverArt"] = Pixmap()
		self._Cover = CoverHelper(self['coverArt'])
		self["songtitle"] = Label ("")
		self["artist"] = Label ("")
		self["album"] = Label ("")
		if self.plType == 'global':
			self['F4'] = Label(_("Delete"))
		else:
			self['F4'] = Label("")
		if playerMode in ('MP3',):
			self['F2'] = Label(_("to Player"))
		else:
			self['F2'] = Label("")
		self['F3'] = Label(_("Playmode"))
		self['F1'] = Label(_("Exit"))
		self['playmode'] = Label(_(self.playMode[0].capitalize()))

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onClose.append(self.resetEvent)

		self.onLayoutFinish.append(self.showPlaylist)

	def updateStatus(self):
		if self.playlistQ and not self.playlistQ.empty():
			t = self.playlistQ.get_nowait()
			self["songtitle"].setText(t[1])
			self["artist"].setText(t[2])
			self["album"].setText(t[3])
			self.getCover(t[4])
			if t[5] == self.plType:
				self.playIdx = t[0]
				if self.playIdx >= len(self.playList):
					self.playIdx = 0
				self['liste'].moveToIndex(self.playIdx)

	def playListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		if self.plType != 'global' and self.listEntryPar:
			self.ml.l.setItemHeight(self.listEntryPar[3])
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM + self.listEntryPar[0], self.listEntryPar[1], self.listEntryPar[2] - 2 * self.DEFAULT_LM, self.listEntryPar[3], self.listEntryPar[4], RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[self.listEntryPar[6]]+self.listEntryPar[5]+entry[self.listEntryPar[7]]))
			return res
		else:
			if self.title_inr == 1 and entry[0]:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]+entry[1]))
				return res
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[self.title_inr]))
				return res

	def showPlaylist(self):
		if self.listTitle:
			self['title'].setText(self.listTitle.replace('\t',' '))
		else:
			self['title'].setText("%s Playlist-%02d" % (self.plType, config_mp.mediaportal.sp_pl_number.value))

		from sepg.mp_epg import mpepg
		if self.playerMode == 'IPTV' and not mpepg.isImporting:
			self.ml.setList(map(self.simpleListTVGListEntry, self.playList))
		else:
			self.ml.setList(map(self.playListEntry, self.playList))

		if self.event:
			self.event.addCallback(self.updateStatus)
		else:
			self['liste'].moveToIndex(self.playIdx)

	def getCover(self, url):
		if url != '--download--':
			self._Cover.getCover(url)

	def deleteEntry(self):
		if self.plType == 'global':
			idx = self['liste'].getSelectedIndex()
			self.close([idx,'del',self.playList])

	def toPlayer(self):
		if self.playerMode in ('MP3',):
			self.close([-2,'',self.playList])

	def exit(self):
		self.close([-1,'',self.playList])

	def ok(self):
		if len(self.playList) == 0:
			self.exit()
		idx = self['liste'].getSelectedIndex()
		if self.playFunc:
			self.playFunc(idx)
		else:
			self.close([idx,'',self.playList])

	def resetEvent(self):
		if self.event:
			self.event.reset()

	def createSummary(self):
		return SimplePlayerSummary

	def changePlaymode(self):
		if self.playMode[0] == "forward":
			self.playMode[0] = "backward"
		elif self.playMode[0] == "backward":
			self.playMode[0] = "random"
		elif self.playMode[0] == "random":
			self.playMode[0] = "endless"
		else:
			self.playMode[0] = "forward"

		self["playmode"].setText(_(self.playMode[0].capitalize()))

class RadioBackground(Screen):
	def __init__(self, session, playerMode):
		Screen.__init__(self, session)

		self['BgCover'] = Pixmap()
		self['BgTitle'] = Label()
		self["cover"] = Pixmap()
		self['screenSaver'] = Pixmap()
		self['screenSaverBg'] = Label()
		self.playerMode = playerMode
		self.audioMode = ''
		if MerlinMusicPlayerPresent:
			self["coverGL"] = MerlinMusicPlayerWidget()
			self["visu"] = MerlinMusicPlayerWidget()
			self["rms0"] = MerlinMusicPlayerRMS()
			self["rms1"] = MerlinMusicPlayerRMS()
			if config_mp.mediaportal.sp_radio_visualization.value == "0":
				self["visu"].hide()
				self["rms0"].hide()
				self["rms1"].hide()
		if config_mp.mediaportal.sp_radio_visualization.value == "0":
			self["cover"].hide()
			self['BgTitle'].hide()

		# internalSize 0 = original, 1 = 1440, 2 = 2160, 3 = 2880, 4 = 800
		if mp_globals.videomode == 2:
			self.skin = '''<screen backgroundColor="transparent" flags="wfNoBorder" name="RadioBackground" position="0,0" size="1920,1080" zPosition="-1">
					<widget name="screenSaverBg" position="0,0" size="1920,1080" transparent="0" backgroundColor="#00000000" zPosition="1" />
					<widget name="screenSaver" position="0,0" size="1920,1080" zPosition="2" />
					<widget alphatest="blend" name="BgCover" position="648,10" size="800,800" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png" zPosition="15" />
					<widget name="BgTitle" position="center,110" size="1600,50" halign="center" valign="center" font="mediaportal_clean;38" foregroundColor="#00ffffff" backgroundColor="#00000000" transparent="1" shadowColor="#00000000" shadowOffset="-2,-2" zPosition="11" />'''

			if MerlinMusicPlayerPresent:
				if config_mp.mediaportal.sp_radio_visualization.value == "3":
					self.skin += '''<widget name="coverGL" position="0,0" size="1920,1080" transparent="0" backgroundColor="#00000000" mode="visGLRandom" noCoverAvailablePic="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png"/>'''
				else:
					self.skin += '''<widget name="cover" position="735,270" size="450,450" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png" zPosition="13" />
					<widget name="rms0" channel="0" backgroundColor="#404040" zPosition="13" position="650,251" size="70,495" pixmap1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/led_90x60_h9.png" transparent="1" mode="imagesOrientationUp" pixmapBackground1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/colorgradient.png" drawBackground="0" pixmapBackgroundColor1="#080808" distance="15" maxValue="40" fadeOutTime="500" smoothing="0.9" />
					<widget name="rms1" channel="1" backgroundColor="#404040" zPosition="13" position="1200,251" size="70,495" pixmap1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/led_90x60_h9.png" transparent="1" mode="imagesOrientationUp" pixmapBackground1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/colorgradient.png" drawBackground="0" pixmapBackgroundColor1="#080808" distance="15" maxValue="40" fadeOutTime="500" smoothing="0.9" />'''

				if config_mp.mediaportal.sp_radio_visualization.value == "1":
					if model in ["dm900","dm920"]:
						self.skin += '''<widget name="visu" position="0,741" size="1920,339" transparent="1" zPosition="11" pixmap1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/bar_88_226.png" distance1="12" threshold1="24" mode="visUp" internalSize="2" blendColor="#fcc000" smoothing="0.4" />'''
					else:
						self.skin += '''<widget name="visu" position="0,741" size="1920,339" transparent="1" zPosition="11" pixmap1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/bar_88_226.png" distance1="12" threshold1="24" mode="visUp" internalSize="0" blendColor="#fcc000" smoothing="0.4" />'''
				if config_mp.mediaportal.sp_radio_visualization.value == "2":
					if model in ["dm900","dm920"]:
						self.skin += '''<widget name="visu" position="0,930" size="1920,150" transparent="1" zPosition="11" pixmapBackground2="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/colorgradient.png" pixmap2="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/led_30x20_h8.png" distance1="18" distance2="8" mode="visImagesUp" maxValue="20" fadeOutTime="0" internalSize="2" pixmapBackgroundColor1="#080808" drawBackground="0" smoothing="0.6" />'''
					else:
						self.skin += '''<widget name="visu" position="0,930" size="1920,150" transparent="1" zPosition="11" pixmapBackground2="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/colorgradient.png" pixmap2="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/led_30x20_h8.png" distance1="18" distance2="8" mode="visImagesUp" maxValue="15" fadeOutTime="0" internalSize="1" pixmapBackgroundColor1="#080808" drawBackground="0" smoothing="0.6" />'''

			self.skin += '''</screen>'''
		else:
			self.skin = '''<screen backgroundColor="transparent" flags="wfNoBorder" name="RadioBackground" position="0,0" size="1280,720" zPosition="-1">
					<widget name="screenSaverBg" position="0,0" size="1280,720" transparent="0" backgroundColor="#00000000" zPosition="1" />
					<widget name="screenSaver" position="0,0" size="1280,720" zPosition="2" />
					<widget alphatest="blend" name="BgCover" position="430,6" size="534,534" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png" zPosition="15" />
					<widget name="BgTitle" position="center,75" size="1070,35" halign="center" valign="center" font="mediaportal_clean;24" foregroundColor="#00ffffff" backgroundColor="#00000000" transparent="1" shadowColor="#00000000" shadowOffset="-2,-2" zPosition="11" />'''

			if MerlinMusicPlayerPresent:
				if config_mp.mediaportal.sp_radio_visualization.value == "3":
					self.skin += '''<widget name="coverGL" position="0,0" size="1280,720" transparent="0" backgroundColor="#00000000" mode="visGLRandom" noCoverAvailablePic="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png"/>'''
				else:
					self.skin += '''<widget name="cover" position="490,180" size="300,300" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png" zPosition="13" />
					<widget name="rms0" channel="0" backgroundColor="#404040" zPosition="13" position="420,167" size="60,330" pixmap1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/led_60x40_h6.png" transparent="1" mode="imagesOrientationUp" pixmapBackground1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/colorgradient.png" drawBackground="0" pixmapBackgroundColor1="#080808" distance="10" maxValue="40" fadeOutTime="500" smoothing="0.9" />
					<widget name="rms1" channel="1" backgroundColor="#404040" zPosition="13" position="800,167" size="60,330" pixmap1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/led_60x40_h6.png" transparent="1" mode="imagesOrientationUp" pixmapBackground1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/colorgradient.png" drawBackground="0" pixmapBackgroundColor1="#080808" distance="10" maxValue="40" fadeOutTime="500" smoothing="0.9" />'''

				if config_mp.mediaportal.sp_radio_visualization.value == "1":
					if model in ["dm900","dm920"]:
						self.skin += '''<widget name="visu" position="0,494" size="1280,226" transparent="1" zPosition="11" pixmap1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/bar_88_226.png" distance1="12" threshold1="24" mode="visUp" internalSize="2" blendColor="#fcc000" smoothing="0.4" />'''
					else:
						self.skin += '''<widget name="visu" position="0,494" size="1280,226" transparent="1" zPosition="11" pixmap1="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/bar_88_226.png" distance1="12" threshold1="24" mode="visUp" internalSize="1" blendColor="#fcc000" smoothing="0.4" />'''
				if config_mp.mediaportal.sp_radio_visualization.value == "2":
					if model in ["dm900","dm920"]:
						self.skin += '''<widget name="visu" position="0,620" size="1280,100" transparent="1" zPosition="11" pixmapBackground2="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/colorgradient.png" pixmap2="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/led_20x13_h5.png" distance1="12" distance2="5" mode="visImagesUp" maxValue="20" fadeOutTime="0" internalSize="2" pixmapBackgroundColor1="#080808" drawBackground="0" smoothing="0.6" />'''
					else:
						self.skin += '''<widget name="visu" position="0,570" size="1280,150" transparent="1" zPosition="11" pixmapBackground2="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/colorgradient.png" pixmap2="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/led_20x13_h5.png" distance1="12" distance2="5" mode="visImagesUp" maxValue="15" fadeOutTime="0" internalSize="1" pixmapBackgroundColor1="#080808" drawBackground="0" smoothing="0.6" />'''

			self.skin += '''</screen>'''

		self.fadeouttimer = eTimer()
		self.changetimer = eTimer()
		if mp_globals.isDreamOS:
			self.fadeouttimer_conn = self.fadeouttimer.timeout.connect(self.initCallNewPicture)
			self.changetimer_conn = self.changetimer.timeout.connect(self.changetimerAppend)
		else:
			self.fadeouttimer.callback.append(self.initCallNewPicture)
			self.changetimer.callback.append(self.changetimerAppend)
		self.onLayoutFinish.append(self.startRun)
		self.onClose.append(self.resetFrameTime)

	def resetFrameTime(self):
		try:
			from enigma import TIME_PER_FRAME
			getDesktop(0).setFrameTime(TIME_PER_FRAME)
			printl('[SP]: FrameTime set to %sms' % str(TIME_PER_FRAME),self,"I")
		except:
			pass
		try:
			from Plugins.SystemPlugins.Screensaver.plugin import screenSaverHandler
			screenSaverHandler.enable()
		except:
			pass
		if mp_globals.isDreamOS and MerlinMusicPlayerPresent and self.playerMode == "RADIO":
			try:
				if self.audioMode == "multichannel":
					open("/proc/stb/audio/ac3", "w").write("multichannel")
			except:
				pass

	def startRun(self):
		try:
			from Plugins.SystemPlugins.Screensaver.plugin import screenSaverHandler
			screenSaverHandler.disable()
		except:
			pass
		if mp_globals.isDreamOS and MerlinMusicPlayerPresent and self.playerMode == "RADIO" and config_mp.mediaportal.sp_radio_visualization.value in ["1", "2", "3"]:
			try:
				self.audioMode = open("/proc/stb/audio/ac3", "r").read().strip()
				if self.audioMode == "multichannel":
					open("/proc/stb/audio/ac3", "w").write("downmix")
			except:
				pass
		self['screenSaverBg'].hide()
		self['screenSaver'].hide()

		if self.playerMode == "RADIO":
			try:
				frametime = 20
				getDesktop(0).setFrameTime(frametime)
				printl('[SP]: FrameTime set to %sms' % str(frametime),self,"I")
			except:
				pass

			if MerlinMusicPlayerPresent and config_mp.mediaportal.sp_radio_visualization.value == "3":
				return

			try:
				if model in ["dm900","dm920"]:
					self['screenSaver'].instance.setShowHideAnimation("mp_screensaver")
				elif config_mp.mediaportal.sp_radio_visualization.value not in ["1", "2"]:
					self['screenSaver'].instance.setShowHideAnimation("mp_screensaver")
				self['BgCover'].instance.setShowHideAnimation("mp_quick_fade")
				self['cover'].instance.setShowHideAnimation("mp_quick_fade")
			except:
				pass

			self.mode = config_mp.mediaportal.sp_radio_bgsaver.value
			self['screenSaverBg'].show()
			if self.mode != "0":
				if mp_globals.videomode == 2:
					self.res_x = 1920
					self.res_y = 1080
					self.offset = 400
				else:
					self.res_x = 1280
					self.res_y = 720
					self.offset = 266
				if self.mode != "3":
					self.initCallNewPicture()

	def getTimestamp(self):
		return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

	def changetimerAppend(self):
		timetest = self.getTimestamp() - self.timestamp
		if timetest >= 40:
			self.val += 1
			self.timestamp = self.getTimestamp()
		if self.val == self.offset:
			if model in ["dm900","dm920"]:
				self['screenSaver'].hide()
			elif config_mp.mediaportal.sp_radio_visualization.value not in ["1", "2"]:
				self['screenSaver'].hide()
			self.fadeouttimer.start(500, 1)
		else:
			self.changetimer.start(5, 1)
			if self.mode == "1":
				self.function()

	def getAnimationStyle(self):
		if mp_globals.isDreamOS:
			return random.choice(('zoom_in', 'zoom_out', 'move_from_left_top_to_right_bottom', 'move_zoomed_left_to_right', 'move_zoomed_right_to_left', 'move_from_right_top_to_left_bottom', 'move_from_left_bottom_to_right_top', 'move_from_right_bottom_to_left_top'))
		else:
			return random.choice(('move_from_left_top_to_right_bottom', 'move_zoomed_left_to_right', 'move_zoomed_right_to_left', 'move_from_right_top_to_left_bottom', 'move_from_left_bottom_to_right_top', 'move_from_right_bottom_to_left_top'))

	def initCallNewPicture(self):
		self.timestamp = self.getTimestamp()
		if len(config_mp.mediaportal.sp_radio_bgsaver_keywords.value)>0:
			keywords = "/?" + urllib.quote_plus(config_mp.mediaportal.sp_radio_bgsaver_keywords.value)
		else:
			keywords = ""
		CoverHelper(self['screenSaver']).getCover("https://source.unsplash.com/1920x1080%s" % keywords, screensaver=True)
		self.val = 0

		if self.mode == "1":
			self.ken_burns = self.getAnimationStyle()

			if self.ken_burns == 'zoom_in':
				size_x, size_Y = self.res_x, self.res_y
				pos_x, pos_y = 0, 0
				self.function = self.zoom_in

			elif self.ken_burns == 'zoom_out':
				size_x, size_Y = self.res_x+int(self.offset*1.7778), self.res_y+self.offset
				pos_x, pos_y = 0, 0
				self.function = self.zoom_out

			elif self.ken_burns == 'move_from_left_top_to_right_bottom':
				size_x, size_Y = self.res_x+int(self.offset*1.7778), self.res_y+self.offset
				pos_x, pos_y = 0, 0
				self.function = self.move_from_left_top_to_right_bottom

			elif self.ken_burns == 'move_from_right_top_to_left_bottom':
				size_x, size_Y = self.res_x+int(self.offset*1.7778), self.res_y+self.offset
				pos_x, pos_y = -int(self.offset*1.7778), 0
				self.function = self.move_from_right_top_to_left_bottom

			elif self.ken_burns == 'move_from_left_bottom_to_right_top':
				size_x, size_Y = self.res_x+int(self.offset*1.7778), self.res_y+self.offset
				pos_x, pos_y = 0, -self.offset
				self.function = self.move_from_left_bottom_to_right_top

			elif self.ken_burns == 'move_from_right_bottom_to_left_top':
				size_x, size_Y = self.res_x+int(self.offset*1.7778), self.res_y+self.offset
				pos_x, pos_y = -int(self.offset*1.7778), -self.offset
				self.function = self.move_from_right_bottom_to_left_top

			elif self.ken_burns == 'move_zoomed_left_to_right':
				self.offset_y = -(random.randrange(int(self.offset/1.7778)))
				size_x, size_Y = self.res_x+self.offset, self.res_y+int(self.offset/1.7778)
				pos_x, pos_y = 0, self.offset_y
				self.function = self.move_zoomed_left_to_right

			elif self.ken_burns == 'move_zoomed_right_to_left':
				self.offset_y = -(random.randrange(int(self.offset/1.7778)))
				size_x, size_Y = self.res_x+self.offset, self.res_y+int(self.offset/1.7778)
				pos_x, pos_y = -self.offset, self.offset_y
				self.function = self.move_zoomed_right_to_left

			self['screenSaver'].instance.resize(eSize(size_x, size_Y))
			self['screenSaver'].instance.move(ePoint(pos_x, pos_y))

		self.changetimerAppend()

	def zoom_in(self):
		self['screenSaver'].instance.resize(eSize(self.res_x+int(self.val*1.7778), self.res_y+self.val))

	def zoom_out(self):
		self['screenSaver'].instance.resize(eSize(self.res_x+int((self.offset-self.val)*1.7778), self.res_y+self.offset-self.val))

	def move_from_left_top_to_right_bottom(self):
		self['screenSaver'].instance.move(ePoint(-int(self.val*1.7778), -self.val))

	def move_from_left_bottom_to_right_top(self):
		self['screenSaver'].instance.move(ePoint(-int(self.val*1.7778), -self.offset+self.val))

	def move_from_right_bottom_to_left_top(self):
		self['screenSaver'].instance.move(ePoint(-int(self.offset*1.7778)+int(self.val*1.7778), -self.offset+self.val))

	def move_from_right_top_to_left_bottom(self):
		self['screenSaver'].instance.move(ePoint(-int(self.offset*1.7778)+int(self.val*1.7778), -self.val))

	def move_zoomed_left_to_right(self):
		self['screenSaver'].instance.move(ePoint(-self.val, self.offset_y))

	def move_zoomed_right_to_left(self):
		self['screenSaver'].instance.move(ePoint(-self.offset+self.val, self.offset_y))

class SimplePlayerPVRState(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/simpleplayer/SimplePlayerPVRState.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/simpleplayer/SimplePlayerPVRState.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["state"] = Label(text="")
		self["eventname"] = Label()
		self["speed"] = Label()
		self["statusicon"] = MultiPixmap()

class SimplePlayerInfoBarStateInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/simpleplayer/SimplePlayerInfoBarStateInfo.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/simpleplayer/SimplePlayerInfoBarStateInfo.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["state"] = Label()
		self["message"] = Label()
		self.onFirstExecBegin.append(self.__onFirstExecBegin)
		self._stateSizeDefault = eSize(590,40)
		self._stateSizeFull = eSize(590,130)
		self._stateOnly = False

	def __onFirstExecBegin(self):
		self._stateSizeDefault = self["state"].getSize()
		self._stateSizeFull = eSize( self._stateSizeDefault.width(), self.instance.size().height() - (2 * self["state"].position.x()) )
		self._resizeBoxes()

	def _resizeBoxes(self):
		if self._stateOnly:
			self["state"].resize(self._stateSizeFull)
			self["message"].hide();
		else:
			self["state"].resize(self._stateSizeDefault)
			self["message"].show();

	def setPlaybackState(self, state, message=""):
		self["state"].text = state
		self["message"].text = message
		self._stateOnly = False if message else True

	def current(self):
		return (self["state"].text, self["message"].text)

class SimplePlayer(Screen, M3U8Player, CoverSearchHelper, SimpleSeekHelper, SimplePlayerResume, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState, InfoBarShowHide, InfoBarAudioSelection, InfoBarSubtitleSupport, InfoBarSimpleEventView, InfoBarServiceErrorPopupSupport, InfoBarGstreamerErrorPopupSupport):

	ALLOW_SUSPEND = True
	ctr = 0

	def __init__(self, session, playList, playIdx=0, playAll=False, listTitle=None, plType='local', title_inr=0, cover=False, ltype='', showPlaylist=True, listEntryPar=None, playList2=[], playerMode='VIDEO', useResume=True, bufferingOpt='None', googleCoverSupp=False, embeddedCoverArt=False, forceGST=True):

		if playerMode == 'RADIO':
			googleCoverSupp = True

		if (self.__class__.ctr + 1) > 1:
			printl('[SP]: only 1 instance allowed',self,"E")
		else:
			self.__class__.ctr += 1

		try:
			from enigma import eServiceMP3
		except:
			is_eServiceMP3 = False
		else:
			is_eServiceMP3 = True

		Screen.__init__(self, session)
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/simpleplayer/SimplePlayer.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/simpleplayer/SimplePlayer.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		if not mp_globals.isDreamOS:
			self.skin = re.sub(r'progress_pointer="(.*?):\d+,\d+" render="PositionGauge"', r'pixmap="\1" render="Progress"', self.skin)
			self.skin = re.sub(r'type="MPServicePosition">Gauge</convert>', r'type="MPServicePosition">Position</convert>', self.skin)

		self["actions"] = ActionMap(["WizardActions",'MediaPlayerSeekActions','InfobarInstantRecord',"EPGSelectActions",'MoviePlayerActions','ColorActions','InfobarActions',"MenuActions","HelpActions","MP_SP_Move","MP_Actions"],
		{
			"leavePlayer": self.leavePlayer,
			"mediaInfo": self.openMediainfo,
			"info":	self.openMovieinfo,
			"menu":	self.openMenu,
			"up": self.openPlaylist,
			"down":	self.randomNow,
			"back":	self.leavePlayer,
			"left":	self.seekBack,
			"right": self.seekFwd,
			"SPMoveDown": self.moveSkinDown,
			"SPMoveUp": self.moveSkinUp
		}, -1)

		if config_mp.mediaportal.sp_use_number_seek.value:
			self["actions2"] = ActionMap(["WizardActions",'MediaPlayerSeekActions','InfobarInstantRecord',"EPGSelectActions",'MoviePlayerActions','ColorActions','InfobarActions',"MenuActions","HelpActions"],
			{
				"seekdef:1": self.Key1,
				"seekdef:3": self.Key3,
				"seekdef:4": self.Key4,
				"seekdef:6": self.Key6,
				"seekdef:7": self.Key7,
				"seekdef:9": self.Key9,
			}, -2)

		M3U8Player.__init__(self)
		CoverSearchHelper.__init__(self, googleCoverSupp)
		SimpleSeekHelper.__init__(self)
		SimplePlayerResume.__init__(self)
		InfoBarMenu.__init__(self)
		InfoBarNotifications.__init__(self)
		InfoBarServiceNotifications.__init__(self)
		InfoBarBase.__init__(self)
		InfoBarShowHide.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarSubtitleSupport.__init__(self)
		InfoBarSimpleEventView.__init__(self)
		try:
			InfoBarServiceErrorPopupSupport.__init__(self)
			InfoBarGstreamerErrorPopupSupport.__init__(self)
			if mp_globals.isDreamOS and mp_globals.stateinfo:
				InfoBarServiceErrorPopupSupport._stateInfo = self.session.instantiateDialog(SimplePlayerInfoBarStateInfo,zPosition=-5)
				InfoBarServiceErrorPopupSupport._stateInfo.neverAnimate()
		except:
			pass

		if mp_globals.isDreamOS:
			self.RadioBg = self.session.instantiateDialog(RadioBackground,playerMode,zPosition=-10)
		else:
			self.RadioBg = self.session.instantiateDialog(RadioBackground,playerMode)
		if playerMode == 'RADIO':
			self.RadioBg.show()
			if mp_globals.isDreamOS:
				self.RadioBg['BgCover'].hide()
			self._BgCover = CoverHelper(self.RadioBg['BgCover'])

		self.allowPiP = False
		InfoBarSeek.__init__(self)
		if not playerMode == 'RADIO':
			InfoBarPVRState.__init__(self, screen=SimplePlayerPVRState, force_show=True)

		self.skinName = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
		if config_mp.mediaportal.restorelastservice.value == "1" and not config_mp.mediaportal.backgroundtv.value:
			self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
		else:
			self.lastservice = None

		self.bufferingOpt = bufferingOpt
		self.use_sp_resume = useResume
		self.playerMode = playerMode
		self.keyPlayNextLocked = False
		self.isTSVideo = False
		self.showGlobalPlaylist = True
		self.showPlaylist = showPlaylist
		self.pl_open = False
		self.playMode = [str(config_mp.mediaportal.sp_playmode.value)]
		self.listTitle = listTitle
		self.playAll = playAll
		self.playList = playList
		self.playIdx = playIdx
		if plType == 'local':
			self.playLen = len(playList)
		else:
			self.playLen = len(playList2)

		self.listEntryPar=listEntryPar
		self.returning = False
		self.pl_entry = ['', '', '', '', '', '', '', '', '']
		self.plType = plType
		self.playList2 = playList2
		self.pl_name = 'mp_global_pl_%02d' % config_mp.mediaportal.sp_pl_number.value
		self.title_inr = title_inr
		self.cover = cover
		self.ltype = ltype
		self.playlistQ = Queue.Queue(0)
		self.pl_status = (0, '', '', '', '', '')
		self.pl_event = SimpleEvent()
		self['spcoverframe'] = Pixmap()
		self['spcoverfg'] = Pixmap()
		self['Icon'] = Pixmap()
		self._Icon = CoverHelper(self['Icon'])
		self['premiumoff'] = Pixmap()
		self['premiumizemeon'] = Pixmap()
		self['premiumizemeon'].hide()
		self['realdebridon'] = Pixmap()
		self['realdebridon'].hide()
		self.progrObj = ProgressBar()
		self['dwnld_progressbar'] = self.progrObj
		# load default cover
		self['Cover'] = Pixmap()
		self['noCover'] = Pixmap()

		self._Cover = CoverHelper(self['Cover'], nc_callback=self.hideSPCover)
		self.coverBGisHidden = False
		self.cover2 = False
		self.searchTitle = None
		self.forceGST = forceGST
		self.embeddedCoverArt = embeddedCoverArt
		self.hasEmbeddedCoverArt = False
		self.lru_key = None
		self.dwnld_lastnum = 0
		self.downloader = None
		self.last_progress = 0
		self.last_path = None
		self.youtubelive = False
		self.dash = False

		self.EmbeddedCoverTimer = eTimer()
		if mp_globals.isDreamOS:
			self.EmbeddedCoverTimer_conn = self.EmbeddedCoverTimer.timeout.connect(self.checkEmbeddedCover)
		else:
			self.EmbeddedCoverTimer.callback.append(self.checkEmbeddedCover)

		self.hideSPCover()
		self.onClose.append(self.playExit)

		self.setPlayerAgent()

		if mp_globals.isDreamOS:
			self.onLayoutFinish.append(self._animation)

		self.onFirstExecBegin.append(self.showIcon)
		self.onFirstExecBegin.append(self.playVideo)

		if self.playerMode in ('MP3',):
			self.onFirstExecBegin.append(self.openPlaylist)

		if is_eServiceMP3:
			self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
				{
					eServiceMP3.evAudioDecodeError: self.__evAudioDecodeError,
					eServiceMP3.evVideoDecodeError: self.__evVideoDecodeError,
					eServiceMP3.evPluginError: self.__evPluginError,
					eServiceMP3.evStreamingSrcError: self.__evStreamingSrcError,
					eServiceMP3.evEmbeddedCoverArt: self._evEmbeddedCoverArt,
					iPlayableService.evStart: self.__serviceStarted,
					iPlayableService.evUpdatedInfo: self.__evUpdatedInfo
				})
		else:
			self.embeddedCoverArt = False
			self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
				{
					iPlayableService.evStart: self.__serviceStarted,
					iPlayableService.evUpdatedInfo: self.__evUpdatedInfo
				})

	def cleanTitleRadio(self, sTitle):
		if self.ltype == 'canna':
			printl(sTitle,self,"I")
			try:
				self.searchCover(sTitle, fallback=self.playList[self.playIdx][2])
			except:
				self.searchCover(sTitle, fallback='')
			return
		if " - " in sTitle:
			if " | " in sTitle:
				sTitle = sTitle.split(' | ')[0]
		if "www." in sTitle:
			sTitle = ''
		if re.match("Jetzt l.{2}uft \"", sTitle):
			sTitle = re.sub('Jetzt\sl.{2}uft\s\"(.*?)\s{0,1}"\svon(\s.*?)', r'\1\2', sTitle)
		if "jetzt bei MDR" in sTitle:
			sTitle = re.sub('(.*?)\svon(\s.*?)jetzt bei MDR.*?$', r'\1\2', sTitle)
		if len(sTitle)>5 and not self.playList[self.playIdx][0].lower() in sTitle.lower():
			printl(sTitle,self,"I")
			try:
				self.searchCover(sTitle, fallback=self.playList[self.playIdx][2])
			except:
				self.searchCover(sTitle, fallback='')
		else:
			try:
				self.searchCover('none', fallback=self.playList[self.playIdx][2])
			except:
				self.searchCover('none', fallback='')

	def __evUpdatedInfo(self):
		if self.playerMode == 'RADIO':
			currPlay=self.session.nav.getCurrentService()
			if currPlay is not None:
				if self.ltype == 'canna':
					sTitle = self.searchTitle
				else:
					sTitle = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
				self.RadioBg['BgTitle'].setText(sTitle)
				self.cleanTitleRadio(sTitle)

	def __evAudioDecodeError(self):
		from enigma import iServiceInformation
		currPlay = self.session.nav.getCurrentService()
		sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
		try:
			from Screens.InfoBarGenerics import InfoBarGstreamerErrorPopupSupport
		except:
			self.session.open(MessageBoxExt, _("This STB can't decode %s streams!") % sTagAudioCodec, MessageBoxExt.TYPE_INFO, timeout=10)

	def __evVideoDecodeError(self):
		from enigma import iServiceInformation
		currPlay = self.session.nav.getCurrentService()
		sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
		try:
			from Screens.InfoBarGenerics import InfoBarGstreamerErrorPopupSupport
		except:
			self.session.open(MessageBoxExt, _("This STB can't decode %s streams!") % sTagVideoCodec, MessageBoxExt.TYPE_INFO, timeout=10)

	def __evPluginError(self):
		from enigma import iServiceInformation
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
		try:
			from Screens.InfoBarGenerics import InfoBarGstreamerErrorPopupSupport
		except:
			self.session.open(MessageBoxExt, message, MessageBoxExt.TYPE_INFO, timeout=10)

	def __evStreamingSrcError(self):
		if isinstance(self, SimplePlayerResume):
			self.eofResumeFlag = True
		from enigma import iServiceInformation
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
		try:
			from Screens.InfoBarGenerics import InfoBarGstreamerErrorPopupSupport
		except:
			self.session.open(MessageBoxExt, _("Streaming error: %s") % message, MessageBoxExt.TYPE_INFO, timeout=10)

	def _evEmbeddedCoverArt(self):
		self.hasEmbeddedCoverArt = True
		if not self.cover and not self.cover2 and self.embeddedCoverArt:
			url = 'file:///tmp/.id3coverart'
			playIdx, title, artist, album, imgurl, plType = self.pl_status
			self.pl_status = (playIdx, title, artist, album, url, plType)
			if self.pl_open:
				self.playlistQ.put(self.pl_status)
				self.pl_event.genEvent()
			self.showCover(url)

	def checkEmbeddedCover(self):
		if not self.hasEmbeddedCoverArt:
			if self.searchCoverSupp:
				self.searchCover(self.searchTitle)
			else:
				self.showCover(None, self.cb_coverDownloaded)

	def __serviceStarted(self):
		self._setM3U8BufferSize()
		if self.embeddedCoverArt and not self.hasEmbeddedCoverArt:
			self.EmbeddedCoverTimer.start(1000*5, True)
		self.initPlayPositionTracker(self.lru_key)

	def playVideo(self):
		if self.seekBarLocked:
			self.cancelSeek()
		self.resetMySpass()
		if self.plType == 'global':
			self.getVideo2()
		else:
			self.cover2 = False
			self.getVideo()

	def playSelectedVideo(self, idx):
		self.playIdx = idx
		self.playVideo()

	def dataError(self, error):
		if self.playIdx != self.pl_status[0]:
			self.pl_status = (self.playIdx,) + self.pl_status[1:]
			if self.pl_open:
				self.playlistQ.put(self.pl_status)
				self.pl_event.genEvent()

		printl(str(error),self,"E")
		self.session.openWithCallback(self.dataError2, MessageBoxExt, str(error), MessageBoxExt.TYPE_INFO, timeout=2)

	def dataError2(self, res):
		self.keyPlayNextLocked = False
		reactor.callLater(2, self.playNextStream, config_mp.mediaportal.sp_on_movie_eof.value)

	def playStream(self, title, url, **kwargs):
		#if self.ltype == 'youtube' and ".m3u8" in url and mp_globals.isDreamOS:
		#	self.youtubelive = False
		#elif self.ltype == 'chaturbate' and ".m3u8" in url and mp_globals.isDreamOS:
		#	self.youtubelive = False
		#elif self.ltype == 'cam4' and ".m3u8" in url and mp_globals.isDreamOS:
		#	self.youtubelive = False
		#elif self.ltype == 'zdf' and ".m3u8" in url and mp_globals.isDreamOS:
		#	self.youtubelive = False
		if not url:
			printl(_('No URL found!'),self,"E")
		elif url.startswith('#SERVICE'):
			self._initStream(title, url, **kwargs)
		elif self.youtubelive:
			self._initStream(title, url, **kwargs)
		elif not self.forceGST and ('.m3u8' in url or 'm3u8-aapl' in url):
			self._getM3U8Video(title, url, **kwargs)
		else:
			self._initStream(title, url, **kwargs)

	def downloadStream(self, url, outputfile, callback, proxy=None, supportPartial=False, resume=False, *args, **kwargs):
		if STREAM_BUFFERING_ENABLED:
			if self.downloader != None:
				self.downloader.stop()

			def updateProgressbar(sz_current, sz_total):
				if sz_current > 0 and sz_total >= sz_current:
					progress = int(100 * round(sz_current / sz_total, 2))
					if progress > 100:
						progress = 100
					if progress != self.last_progress:
						self.progrObj.setValue(progress)
						self.last_progress = progress

			if not resume:
				if proxy == None: proxy = (None, None, None)
				from twagenthelper import TwDownloadWithProgress
				self.downloader = TwDownloadWithProgress(url, outputfile, timeout=(10,None), agent="Enigma Mediaplayer", proxy_url=proxy[0], p_user=proxy[1], p_pass=proxy[2], use_pipe=False, supportPartial=supportPartial)
				self.downloader.addProgress(updateProgressbar)

			d = self.downloader.start()
			d.addCallback(callback, *args, **kwargs)
			if not self._playing and self.last_path:
				try:
					os.remove(self.last_path)
				except:
					pass

			self.last_path = outputfile
			if not self.downloader.requestedPartial:
				self.downloader.addThreshold('10').addCallback(callback, *args, **kwargs).addErrback(self.dataError)

			return d
		else:
			callback(url, *args, **kwargs)

	def _initStream(self, title, url, suburi=None, album='', artist='', imgurl='', buffering=False, proxy=None, epg_id=None):
		self.hasGoogleCoverArt = self.hasEmbeddedCoverArt = False

		if not mp_globals.yt_download_runs:
			self['dwnld_progressbar'].setValue(0)

		if mp_globals.premiumize:
			self['premiumoff'].hide()
			self['realdebridon'].hide()
			self['premiumizemeon'].show()
			mp_globals.premiumize = False
		elif mp_globals.realdebrid:
			self['premiumoff'].hide()
			self['premiumizemeon'].hide()
			self['realdebridon'].show()
			mp_globals.realdebrid = False
		else:
			self['premiumizemeon'].hide()
			self['realdebridon'].hide()
			self['premiumoff'].show()

		if artist != '':
			video_title = artist + ' - ' + title
		else:
			video_title = title

		if self.cover:
			cflag = '1'
		else:
			cflag = '0'

		self.pl_entry = [title, None, artist, album, self.ltype, '', imgurl, cflag]
		if self.cover or self.cover2 or self.searchCoverSupp or self.embeddedCoverArt:
			imgurl = '--download--'
		self.pl_status = (self.playIdx, title, artist, album, imgurl, self.plType)
		if self.cover or self.cover2:
			self.showCover(self.pl_entry[6], self.cb_coverDownloaded)
		elif self.embeddedCoverArt:
			self.searchTitle = video_title
		else:
			self.searchCover(video_title)

		if len(video_title) > 0:
			self.lru_key = video_title
		else:
			self.lru_key = url

		self.stopPlayPositionTracker()

		if epg_id and not url.startswith('#SERVICE'):
			url = "#SERVICE 4097:0:0:%s:1955:0:0:0:0:0:%s:%s" % (epg_id, url.replace(':','%3a'), video_title)
		self._playing = False
		self.isTSVideo = False
		def playService(url):
			self.dash = False
			if url == 'cancelled': return
			if not self._playing:
				self._playing = True
				if url.startswith('#SERVICE'):
					url = url[8:].strip()
					sref = eServiceReference(url)
				else:
					if url.endswith('.ts'):
						sref = eServiceReference(0x0001, 0, unquote(url))
						self.isTSVideo = True
					else:
						if not '/?url=' in url:
							url = unquote(url)
						if self.youtubelive:
							sref = eServiceReference(0x0001, 0, url)
						else:
							if mp_globals.isDreamOS:
								if self.playerMode == 'RADIO' and config_mp.mediaportal.sp_radio_visualization.value != "0" and MerlinMusicPlayerPresent:
									sref = eServiceReference(0x1019, 0, url)
								else:
									sref = eServiceReference(0x1001, 0, url)
								if suburi:
									try:
										sref.setSuburi(suburi)
										self.dash = True
									except:
										pass
							else:
								if suburi:
									url = url + "&suburi=" + suburi
									self.dash = True
								sref = eServiceReference(0x1001, 0, url)
					sref.setName(video_title)
					self.searchTitle = video_title

				self.session.nav.playService(sref)
				if mp_globals.isDreamOS:
					from DelayedFunction import DelayedFunction
					DelayedFunction(1000, self.fixSeek)

				if self.pl_open:
					self.playlistQ.put(self.pl_status)
					self.pl_event.genEvent()

				#self.initPlayPositionTracker(self.lru_key)

		self.keyPlayNextLocked = False
		if buffering:
			if not self._playing:
				clearTmpBuffer()
				self.dwnld_lastnum = (self.dwnld_lastnum + 1) % 2
				path = config_mp.mediaportal.storagepath.value + 'downloaded_file_%d.mp4' % self.dwnld_lastnum
				self.downloadStream(url, path, playService, proxy)
		else:
			self.progrObj.setValue(0)
			if self.downloader != None:
				self.downloader.stop()
				clearTmpBuffer()
			playService(url)

	def fixSeek(self):
		service = self.session.nav.getCurrentService()
		if service:
			self.seek = service.seek()
			if self.seek:
				self.length = self.seek.getLength()
				if int(float(self.length[1])) < 15000000:
					self.isNumberSeek = True
					self.initSeek()
					self.numberKeySeek(-60)
					self.doSeek(0)
					self.setSeekState(self.SEEK_STATE_PLAY)

	def playPrevStream(self, value):
		if self.keyPlayNextLocked:
			return

		if not self.playAll or self.playLen <= 1:
			self.handleLeave(value)
		else:
			if self.playIdx > 0:
				self.playIdx -= 1
			else:
				self.playIdx = self.playLen - 1

			self.keyPlayNextLocked = True
			if mp_globals.yt_dwnld_agent:
				mp_globals.yt_dwnld_agent.cancelDownload()

			self.playVideo()

	def playNextStream(self, value):
		if self.keyPlayNextLocked:
			return

		if not self.playAll or self.playLen <= 1:
			self.handleLeave(value)
		else:
			if self.playIdx in range(0, self.playLen-1):
				self.playIdx += 1
			else:
				self.playIdx = 0
			self.keyPlayNextLocked = True

			if mp_globals.yt_dwnld_agent:
				mp_globals.yt_dwnld_agent.cancelDownload()

			self.playVideo()

	def playRandom(self, value):
		if self.keyPlayNextLocked:
			return

		if self.playLen > 1 and self.playAll:
			self.playIdx = random.randint(0, self.playLen-1)
			self.keyPlayNextLocked = True

			if mp_globals.yt_dwnld_agent:
				mp_globals.yt_dwnld_agent.cancelDownload()

			self.playVideo()
		else:
			self.handleLeave(value)

	def playEndlessStream(self):
		if self.keyPlayNextLocked:
			return
		self.keyPlayNextLocked = True

		if mp_globals.yt_dwnld_agent:
			mp_globals.yt_dwnld_agent.cancelDownload()

		self.playVideo()

	def randomNow(self):
		if self.playAll:
			self.playRandom(config_mp.mediaportal.sp_on_movie_stop.value)

	def seekFwd(self):
		if self.isTSVideo:
			InfoBarSeek.seekFwd(self)
		elif self.seekBarShown and not self.seekBarLocked and not self.dash:
			self.initSeek()
		elif self.seekBarLocked:
			self.seekRight()
		elif self.playAll:
			self.playNextStream(config_mp.mediaportal.sp_on_movie_stop.value)

	def seekBack(self):
		if self.isTSVideo:
			InfoBarSeek.seekBack(self)
		elif self.seekBarShown and not self.seekBarLocked and not self.dash:
			self.initSeek()
		elif self.seekBarLocked:
			self.seekLeft()
		elif self.playAll:
			self.playPrevStream(config_mp.mediaportal.sp_on_movie_stop.value)

	def handleLeave(self, how):
		if self.playerMode in ('MP3',):
			self.openPlaylist()
			return
		self.is_closing = True
		if how == "ask":
			if self.plType == 'local':
				list = (
					(_("Yes"), "quit"),
					(_("Yes & Add Service to global Playlist-%02d") % config_mp.mediaportal.sp_pl_number.value, "add"),
					(_("No"), "continue"),
					(_("No, but start over from the beginning"), "restart")
				)
			else:
				list = (
					(_("Yes"), "quit"),
					(_("No"), "continue"),
					(_("No, but start over from the beginning"), "restart")
				)

			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBoxExt, title=_("Stop playing this movie?"), list = list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]

		self.savePlayPosition(is_eof=True)

		if answer in ("quit", "movielist"):
			self.close()
		elif answer == "restart":
			if self.isMySpass:
				self.restartMySpass()
			else:
				self.doSeek(0)
				self.setSeekState(self.SEEK_STATE_PLAY)
		elif answer == "add":
			self.addToPlaylist()
			self.close()
		try:
			if mp_globals.isDreamOS and mp_globals.stateinfo:
				InfoBarServiceErrorPopupSupport._stateInfo.hide()
				InfoBarServiceErrorPopupSupport._stateInfo = self.session.instantiateDialog(InfoBarStateInfo,zPosition=-5)
				InfoBarServiceErrorPopupSupport._stateInfo.neverAnimate()
		except:
			pass

	def leavePlayer(self):
		if self.seekBarLocked:
			self.cancelSeek()
		else:
			try:
				InfoBarShowHide.doWriteAlpha(self,config.av.osd_alpha.value)
			except:
				pass
			self.handleLeave(config_mp.mediaportal.sp_on_movie_stop.value)

	def doEofInternal(self, playing):
		if not self.youtubelive:
			if playing:
				if not self.resumeEOF():
					if self.playMode[0] == 'random':
						self.playRandom(config_mp.mediaportal.sp_on_movie_eof.value)
					elif self.playMode[0] == 'forward':
						self.playNextStream(config_mp.mediaportal.sp_on_movie_eof.value)
					elif self.playMode[0] == 'backward':
						self.playPrevStream(config_mp.mediaportal.sp_on_movie_eof.value)
					elif self.playMode[0] == 'endless':
						#self.playEndlessStream()
						self.doSeek(0)
						self.setSeekState(self.SEEK_STATE_PLAY)

	def playExit(self):
		if self.playerMode == 'RADIO':
			self.session.deleteDialog(self.RadioBg)
			self.RadioBg = None

		self.__class__.ctr -= 1
		self.EmbeddedCoverTimer.stop()
		del self.EmbeddedCoverTimer
		if mp_globals.yt_dwnld_agent:
			mp_globals.yt_dwnld_agent.cancelDownload()

		mp_globals.yt_download_progress_widget = None
		if isinstance(self, SimpleSeekHelper):
			del self.cursorTimer
		if isinstance(self, SimplePlayerResume):
			del self.posTrackerTimer
			del self.eofResumeTimer

		if not self.playerMode in ('MP3',):
			self.restoreLastService()

		if self.downloader != None:
			self.downloader.stop()
		reactor.callLater(1, clearTmpBuffer)

	def restoreLastService(self):
		if config_mp.mediaportal.restorelastservice.value == "1" and not config_mp.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)
		else:
			self.session.nav.stopService()

	def getVideo(self):
		entry = self.playList[self.playIdx]
		title = entry[0]
		url = entry[1]
		epg_id = None
		l = len(entry)
		if l >= 3:
			iurl = entry[2]
			if (l > 3):
				epg_id = entry[3][2] if entry[3] and ('tvg-id' in entry[3]) and entry[3][2] and not entry[3][2].endswith('.ink') else None
		else:
			iurl = ''
		self.playStream(title, url, imgurl=iurl, epg_id=epg_id)

	def getVideo2(self):
		if self.playLen > 0:
			titel = self.playList2[self.playIdx][1]
			url = self.playList2[self.playIdx][2]
			album = self.playList2[self.playIdx][3]
			artist = self.playList2[self.playIdx][4]
			imgurl = self.playList2[self.playIdx][7]
			self.cover2 = self.playList2[self.playIdx][8] == '1' and self.plType == 'global'

			if len(self.playList2[self.playIdx]) < 6:
				ltype = ''
			else:
				ltype = self.playList2[self.playIdx][5]

			if ltype == 'youtube':
				YoutubeLink(self.session).getLink(self.playStream, self.dataError, titel, url, imgurl)
			elif ltype == 'canna':
				CannaLink(self.session).getLink(self.playStream, self.dataError, titel, artist, album, url, imgurl)
			elif ltype == 'eighties':
				token = self.playList2[self.playIdx][6]
				EightiesLink(self.session).getLink(self.playStream, self.dataError, titel, artist, album, url, token, imgurl)
			elif ltype == 'mtv':
				MTVdeLink(self.session).getLink(self.playStream, self.dataError, titel, artist, url, imgurl)
			elif url:
				self.playStream(titel, url, album=album, artist=artist, imgurl=imgurl)
		else:
			self.close()

	def openPlaylist(self, pl_class=SimplePlaylist):
		if ((self.showGlobalPlaylist and self.plType == 'global') or self.showPlaylist) and self.playLen > 0:
			if self.playlistQ.empty():
				self.playlistQ.put(self.pl_status)
			self.pl_open = True
			self.pl_event.genEvent()

			if self.plType == 'local':
				self.session.openWithCallback(self.cb_Playlist, pl_class, self.playList, self.playIdx, self.playMode, listTitle=self.listTitle, plType=self.plType, title_inr=self.title_inr, queue=self.playlistQ, mp_event=self.pl_event, listEntryPar=self.listEntryPar, playFunc=self.playSelectedVideo,playerMode=self.playerMode)
			else:
				self.session.openWithCallback(self.cb_Playlist, pl_class, self.playList2, self.playIdx, self.playMode, listTitle=None, plType=self.plType, title_inr=0, queue=self.playlistQ, mp_event=self.pl_event, listEntryPar=self.listEntryPar,playFunc=self.playSelectedVideo,playerMode=self.playerMode)
		elif not self.playLen:
			self.session.open(MessageBoxExt, _("No entries in the playlist available!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def cb_Playlist(self, data):
		self.pl_open = False

		while not self.playlistQ.empty():
			t = self.playlistQ.get_nowait()

		if data[0] >= 0:
			self.playIdx = data[0]
			if self.plType == 'global':
				if data[1] == 'del':
					self.session.nav.stopService()
					SimplePlaylistIO.delEntry(self.pl_name, self.playList2, self.playIdx)
					self.playLen = len(self.playList2)
					if self.playIdx >= self.playLen:
						self.playIdx -= 1
					if self.playIdx < 0:
						self.close()
					else:
						self.openPlaylist()
			if not self.keyPlayNextLocked:
				self.keyPlayNextLocked = True
				self.playVideo()
		elif data[0] == -1 and self.playerMode in ('MP3',):
				self.close()
		elif self.playerMode in ('MP3',) and isinstance(self, SimplePlayerResume):
			self.showInfoBar()

	def openMediainfo(self):
		if MediaInfoPresent:
			self.session.open(MediaInfo)

	def openMovieinfo(self):
		service = self.session.nav.getCurrentService()
		if service:
			title = service.info().getName()
			title = title.translate(None,"[].;:!&?,")
			title = title.replace(' ','_')
			title = self.cleanTitle(title, False)
			from tmdb import MediaPortalTmdbScreen
			self.session.open(MediaPortalTmdbScreen, title)

	def openMenu(self):
		self.session.openWithCallback(self.cb_Menu, SimplePlayerMenu, self.plType, self.showPlaylist or self.showGlobalPlaylist)

	def cb_Menu(self, data):
		if data != []:
			if data[0] == 1:
				self.playMode[0] = config_mp.mediaportal.sp_playmode.value
				if self.cover or self.cover2 or self.searchCoverSupp:
					self.showCover(self.pl_status[4])
				self.pl_name = 'mp_global_pl_%02d' % config_mp.mediaportal.sp_pl_number.value
			elif data[0] == 2:
				self.addToPlaylist()

			elif data[0] == 3:
				nm = self.pl_name
				pl_list = SimplePlaylistIO.getPL(nm)
				self.playList2 = pl_list
				playLen = len(self.playList2)
				if playLen > 0:
					self.playIdx = 0
					self.playLen = playLen
					self.plType = 'global'
				self.openPlaylist()

			elif data[0] == 4:
				if self.plType != 'local':
					playLen = len(self.playList)
					if playLen > 0:
						self.playIdx = 0
						self.playLen = playLen
						self.plType = 'local'
						self.playList2 = []
					self.openPlaylist()

			elif data[0] == 7:
				self.mainMenu()

	def addToPlaylist(self):
		if self.plType != 'local':
			self.session.open(MessageBoxExt, _("Error: Service may be added only from the local playlist"), MessageBoxExt.TYPE_INFO, timeout=5)
			return

		if self.pl_entry[4] == 'youtube':
			url = self.playList[self.playIdx][self.title_inr+1]
		elif self.pl_entry[4] == 'mtv':
			url = self.playList[self.playIdx][1]
		else:
			if '.m3u8' in self.playList[self.playIdx][1]:
				url = self.playList[self.playIdx][1]
			else:
				url = self.session.nav.getCurrentlyPlayingServiceReference().getPath()

			if re.search('(/myspass)', url, re.I):
				self.session.open(MessageBoxExt, _("Error: URL is not persistent!"), MessageBoxExt.TYPE_INFO, timeout=5)
				return

		self.pl_entry[1] = url
		res = SimplePlaylistIO.addEntry(self.pl_name, self.pl_entry)
		if res == 1:
			self.session.open(MessageBoxExt, _("Added entry"), MessageBoxExt.TYPE_INFO, timeout=5)
		elif res == 0:
			self.session.open(MessageBoxExt, _("Entry already exists"), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			self.session.open(MessageBoxExt, _("Error!"), MessageBoxExt.TYPE_INFO, timeout=5)

	def showCover(self, cover, download_cb=None, CoverSize="small", fallback=''):
		from coverhelper import downloadPage
		if config_mp.mediaportal.sp_infobar_cover_off.value:
			self.hideSPCover()
			self['Cover'].hide()
			self['noCover'].show()
			return
		if self.coverBGisHidden and cover != "file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png" and CoverSize != "large":
			if config_mp.mediaportal.sp_radio_cover.value != "off" or fallback != "file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png":
				self.showSPCover()
		if CoverSize == "large" and self.playerMode == 'RADIO':
			if mp_globals.isDreamOS:
				self.RadioBg['BgCover'].hide()
			if self.seekBarShown:
				self._BgCover.getCover(cover.replace('450x450','800x800'))
			else:
				self._BgCover.getCover(cover.replace('450x450','800x800'), bgcover=True)
			if mp_globals.isDreamOS:
				if "static.rad.io" in cover or "static.radio" in cover:
					cover = "file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png"
				if cover.startswith('file://'):
					shutil.copyfile(cover[7:], '/tmp/.RadioCover.jpg')
					self.showCover2('', cover)
				else:
					downloadPage(cover, '/tmp/.RadioCover.jpg').addCallback(self.showCover2, cover)
		elif CoverSize == "small" and self.playerMode == 'RADIO':
			if mp_globals.isDreamOS:
				self['Cover'].hide()
			self._Cover.getCover(cover, download_cb=download_cb)
			if mp_globals.isDreamOS:
				if "static.rad.io" in cover or "static.radio" in cover:
					cover = "file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png"
				if cover.startswith('file://'):
					shutil.copyfile(cover[7:], '/tmp/.RadioCover.jpg')
					self.showCover2('', cover)
				else:
					downloadPage(cover, '/tmp/.RadioCover.jpg').addCallback(self.showCover2, cover)
		elif self.playerMode != 'RADIO':
			if mp_globals.isDreamOS:
				self['Cover'].hide()
			self._Cover.getCover(cover, download_cb=download_cb)

	def showCover2(self, ret, cover=None):
		if model in ["dm7080","dm900","dm920"]:
			self.summaries.updateCover('file:///tmp/.RadioCover.jpg')
		if config_mp.mediaportal.sp_radio_visualization.value == "3":
			self.RadioBg['coverGL'].setCover('/tmp/.RadioCover.jpg')
		else:
			self.RadioBg['cover'].hide()
			if self.seekBarShown:
				CoverHelper(self.RadioBg['cover']).getCover(cover, bgcover=True)
			else:
				CoverHelper(self.RadioBg['cover']).getCover(cover)

	def showIcon(self):
		self['dwnld_progressbar'].setValue(0)
		mp_globals.yt_download_progress_widget = self.progrObj
		if mp_globals.activeIcon == "simplelist":
			pm_file = mp_globals.pluginPath + "/images/simplelist.png"
		else:
			logo_path = config_mp.mediaportal.iconcachepath.value + "logos/"
			pm_file = logo_path + mp_globals.activeIcon + ".png"
		if not fileExists(pm_file):
			icon_path = config_mp.mediaportal.iconcachepath.value + "icons/"
			pm_file = icon_path + mp_globals.activeIcon + ".png"
		if not fileExists(pm_file):
			pm_file = mp_globals.pluginPath + "/images/comingsoon.png"
		pm_file = "file://" + pm_file
		self._Icon.getCover(pm_file)
		CoverHelper(self['noCover']).getCover('file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/default_cover.png')

	def _animation(self):
		try:
			self.setShowHideAnimation("mp_quick_fade")
			self['Cover'].instance.setShowHideAnimation("mp_quick_fade")
		except:
			pass

	def hideSPCover(self):
		if not self.coverBGisHidden:
			self['spcoverframe'].hide()
			self['spcoverfg'].hide()
			self['noCover'].show()
			self.coverBGisHidden = True

	def showSPCover(self):
		if self.coverBGisHidden:
			self['spcoverframe'].show()
			self['spcoverfg'].show()
			self['noCover'].hide()
			self.coverBGisHidden = False

	def createSummary(self):
		if self.playerMode == "RADIO" and model in ["dm7080","dm900","dm920"]:
			return SimplePlayerLCDScreen
		else:
			return SimplePlayerSummary

	def runPlugin(self, plugin):
		plugin(session=self.session)

	def setPlayerAgent(self):
		if not mp_globals.player_agent:
			return

		self.playListTmp = []
		j = 0
		for i in self.playList:
			entry = self.playList[j]
			tmpTitle = entry[0]
			if not "#User-Agent=" in entry[1]:
				tmpUrl = entry[1] + "#User-Agent=" + mp_globals.player_agent
			else:
				tmpUrl = entry[1]
			l = len(entry)
			if l == 3:
				tmpPic = entry[2]
				self.playListTmp.append((tmpTitle, tmpUrl, tmpPic))
			else:
				self.playListTmp.append((tmpTitle, tmpUrl))
			j += 1
		self.playList = self.playListTmp

		try:
			config.mediaplayer.useAlternateUserAgent.value = True
			config.mediaplayer.alternateUserAgent.value = mp_globals.player_agent
		except Exception, errormsg:
			if not hasattr(config, "mediaplayer"):
				config.mediaplayer = ConfigSubsection()
				config.mediaplayer.useAlternateUserAgent = ConfigYesNo(default=True)
				config.mediaplayer.alternateUserAgent = ConfigText(default=mp_globals.player_agent)
			else:
				pass
		self.onClose.append(self.clearPlayerAgent)

	def clearPlayerAgent(self):
		mp_globals.player_agent = None

		try:
			config.mediaplayer.useAlternateUserAgent.value = False
			config.mediaplayer.alternateUserAgent.value = ""
		except:
			pass

class SimpleConfig(Screen, ConfigListScreenExt):

	def __init__(self, session):

		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/simpleplayer/SimplePlayerConfig.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/simpleplayer/SimplePlayerConfig.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)

		self.configlist = []

		ConfigListScreenExt.__init__(self, self.configlist, enableWrapAround=True)

		self['title'] = Label(_("SimplePlayer Configuration"))
		self.setTitle(_("SimplePlayer Configuration"))
		self.configlist.append(getConfigListEntry(_('Global playlist number:'), config_mp.mediaportal.sp_pl_number))
		self.configlist.append(getConfigListEntry(_('Playmode:'), config_mp.mediaportal.sp_playmode))
		self.configlist.append(getConfigListEntry(_('Highest resolution for playback (only YouTube):'), config_mp.mediaportal.youtubeprio))
		self.configlist.append(getConfigListEntry(_('Videoquality:'), config_mp.mediaportal.videoquali_others))
		self.configlist.append(getConfigListEntry(_('Save resume cache in flash memory:'), config_mp.mediaportal.sp_save_resumecache))
		self.configlist.append(getConfigListEntry(_('Behavior on movie start:'), config_mp.mediaportal.sp_on_movie_start))
		self.configlist.append(getConfigListEntry(_('Behavior on movie stop:'), config_mp.mediaportal.sp_on_movie_stop))
		self.configlist.append(getConfigListEntry(_('Behavior on movie end:'), config_mp.mediaportal.sp_on_movie_eof))
		self.configlist.append(getConfigListEntry(_('Seekbar sensibility:'), config_mp.mediaportal.sp_seekbar_sensibility))
		self.configlist.append(getConfigListEntry(_('Infobar cover always off:'), config_mp.mediaportal.sp_infobar_cover_off))
		self.configlist.append(getConfigListEntry(_('Use SP number seek:'), config_mp.mediaportal.sp_use_number_seek))
		self.configlist.append(getConfigListEntry(_('Radio cover:'), config_mp.mediaportal.sp_radio_cover))
		self.configlist.append(getConfigListEntry(_('Radio visualization:'), config_mp.mediaportal.sp_radio_visualization))
		self.configlist.append(getConfigListEntry(_('Radio screensaver:'), config_mp.mediaportal.sp_radio_bgsaver))
		self.configlist.append(getConfigListEntry(_('Radio screensaver keywords:'), config_mp.mediaportal.sp_radio_bgsaver_keywords))

		self["actions"] = ActionMap(["MP_Actions2", "MP_Actions"], {
			'ok':		self.keySave,
			'cancel':	self.keyCancel,
			"up":		self.keyUp,
			"down":		self.keyDown
		},-1)

		self["config"].list = self.configlist
		self["config"].setList(self.configlist)

	def keyOK(self):
		self.keySave()

class SimplePlayerMenu(Screen):

	def __init__(self, session, pltype, showPlaylist=True):

		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/simpleplayer/SimplePlayerMenu.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/simpleplayer/SimplePlayerMenu.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)
		self['title'] = Label(_("SimplePlayer Menu"))
		self.setTitle(_("SimplePlayer Menu"))
		self.pltype = pltype

		self['Actions'] = ActionMap(['MP_Actions'],
		{
			'ok': 		self.keyOk,
			'cancel':	self.keyCancel
		}, -1)

		self.liste = []
		if pltype != 'extern':
			self.liste.append((_('Configuration'), 1))
		if pltype in ('local', 'extern') :
			self.pl_name = 'mp_global_pl_%02d' % config_mp.mediaportal.sp_pl_number.value
			self.liste.append((_('Add service to global playlist-%02d') % config_mp.mediaportal.sp_pl_number.value, 2))
			if showPlaylist and pltype == 'local':
				self.liste.append((_('Open global playlist-%02d') % config_mp.mediaportal.sp_pl_number.value, 3))
		elif showPlaylist:
			self.liste.append((_('Open local playlist'), 4))
		if VideoSetupPresent:
			self.liste.append((_('A/V Settings'), 5))
		if AudioSetupPresent:
			self.liste.append((_('Advanced Audio Settings'), 6))
		self.liste.append((_('Mainmenu'), 7))
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['menu'] = self.ml

		self.onLayoutFinish.append(self.setmenu)

	def setmenu(self):
		self.width = self['menu'].instance.size().width()
		self.height = self['menu'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, self.height - 2 * mp_globals.sizefactor))
		self.ml.setList(map(self.menulistentry, self.liste))

	def menulistentry(self, entry):
		return [entry,
			(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, self.width, self.height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0])
			]

	def openConfig(self):
		self.session.open(SimpleConfig)
		self.close([1, ''])

	def addToPlaylist(self, id, name):
		self.close([id, name])

	def openPlaylist(self, id, name):
		self.close([id, name])

	def openSetup(self):
		if VideoSetupPresent:
			if is_avSetupScreen:
				self.session.open(avSetupScreen)
			else:
				self.session.open(VideoSetup, video_hw)
		self.close([5, ''])

	def openAudioSetup(self):
		if AudioSetupPresent:
			self.session.open(AudioSetup)
		self.close([6, ''])

	def openMainmenu(self, id, name):
		self.close([id, name])

	def keyOk(self):
		choice = self['menu'].getCurrent()[0][1]
		if choice == 1:
			self.openConfig()
		elif choice == 2:
			self.addToPlaylist(2, self.pl_name)
		elif choice == 3:
			self.openPlaylist(3, '')
		elif choice == 4:
			self.openPlaylist(4, '')
		elif choice == 5:
			self.openSetup()
		elif choice == 6:
			self.openAudioSetup()
		elif choice == 7:
			self.openMainmenu(7, '')

	def keyCancel(self):
		self.close([])

class SimplePlaylistIO:

	Msgs = [_("The directory path does not end with '/':\n%s"),
		_("File with the same name exists in the directory path:\n%s"),
		_("The missing directory:\n%s could not be created!"),
		_("The directory path:\n%s does not exist!"),
		_("There exists already a directory with this name:\n%s"),
		_("The path is OK, the file name was not specified:\n%s"),
		_("The directory path and file name is OK:\n%s"),
		_("The directory path is not specified!"),
		_("Symbolic link with the same name in the directory path:\n%s available!"),
		_("The directory path does not begin with '/':\n%s")]

	@staticmethod
	def checkPath(path, pl_name, createPath=False):
		if not path:
			return (0, SimplePlaylistIO.Msgs[7])
		if path[-1] != '/':
			return (0, SimplePlaylistIO.Msgs[0] % path)
		if path[0] != '/':
			return (0, SimplePlaylistIO.Msgs[9] % path)
		if not os.path.isdir(path):
			if os.path.isfile(path[:-1]):
				return (0, SimplePlaylistIO.Msgs[1] % path)
			if os.path.islink(path[:-1]):
				return (0, SimplePlaylistIO.Msgs[8] % path)
			if createPath:
				if createDir(path, True) == 0:
					return (0, SimplePlaylistIO.Msgs[2] % path)
			else:
				return (0, SimplePlaylistIO.Msgs[3] % path)
		if not pl_name:
			return (1, SimplePlaylistIO.Msgs[5] % path)
		if os.path.isdir(path+pl_name):
			return (0, SimplePlaylistIO.Msgs[4] % (path, pl_name))

		return (1, SimplePlaylistIO.Msgs[6] % (path, pl_name))

	@staticmethod
	def delEntry(pl_name, list, idx):
		assert pl_name != None
		assert list != []

		pl_path = config_mp.mediaportal.watchlistpath.value + pl_name

		l = len(list)
		if idx in range(0, l):
			del list[idx]
			l = len(list)

		j = 0
		try:
			f1 = open(pl_path, 'w')
			while j < l:
				wdat = '<title>%s</<url>%s</<album>%s</<artist>%s</<ltype %s/><token %s/><img %s/><cflag %s/>\n' % (list[j][1], list[j][2], list[j][3], list[j][4], list[j][5], list[j][6], list[j][7], list[j][8])
				f1.write(wdat)
				j += 1

			f1.close()

		except IOError, e:
			f1.close()

	@staticmethod
	def addEntry(pl_name, entry):
		cflag = entry[7]
		imgurl = entry[6]
		if imgurl and not imgurl.startswith('http'):
			imgurl = ""
		token = entry[5]
		ltype = entry[4]
		album = entry[3]
		artist = entry[2]
		url = entry[1]
		title = entry[0].replace('\n\t', ' - ')
		title = title.replace('\n', ' - ')

		if token == None:
			token = ''

		if url == None:
			url = ''

		if imgurl == None:
			imgurl = ''

		cmptup = (url, artist, title)

		assert pl_name != None

		pl_path = config_mp.mediaportal.watchlistpath.value + pl_name
		try:
			if fileExists(pl_path):
				f1 = open(pl_path, 'a+')

				data = f1.read()
				m = re.findall('<title>(.*?)</<url>(.*?)</.*?<artist>(.*?)</', data)
				if m:
					found = False
					for (t,u,a) in m:
						if (u,a,t)  == cmptup:
							found = True
							break

					if found:
						f1.close()
						return 0
			else:
				f1 = open(pl_path, 'w')

			wdat = '<title>%s</<url>%s</<album>%s</<artist>%s</<ltype %s/><token %s/><img %s/><cflag %s/>\n' % (title, url, album, artist, ltype, token, imgurl, cflag)
			f1.write(wdat)
			f1.close()
			return 1

		except IOError, e:
			f1.close()
			return -1

	@staticmethod
	def getPL(pl_name):
		list = []

		assert pl_name != None

		pl_path = config_mp.mediaportal.watchlistpath.value + pl_name
		try:
			if not fileExists(pl_path):
				f_new = True
			else:
				f_new = False
				f1 = open(pl_path, 'r')

			if not f_new:
				while True:
					entry = f1.readline().strip()
					if entry == "":
						break
					m = re.search('<title>(.*?)</<url>(.*?)</<album>(.*?)</<artist>(.*?)</<ltype (.*?)/><token (.*?)/><img (.*?)/><cflag (.*?)/>', entry)
					if m:
						titel = m.group(1)
						url = m.group(2)
						album = m.group(3)
						artist = m.group(4)
						ltype = m.group(5)
						token = m.group(6)
						imgurl = m.group(7)
						cflag = m.group(8)

						if artist != '':
							name = "%s - %s" % (artist, titel)
						else:
							name = titel

						list.append((name, titel, url, album, artist, ltype, token, imgurl, cflag))

				f1.close()

			return list

		except IOError, e:
			f1.close()
			return list

class SimplePlayerSummary(Screen):

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self.skinName = "InfoBarMoviePlayerSummary"

	def updateCover(self, filename):
		pass

class SimplePlayerLCDScreen(Screen):

	def __init__(self, session, parent):
		self["cover"] = Pixmap()

		self.skin = '''<screen name="SimplePlayerLCDScreen" backgroundColor="#00000000" position="0,0" size="400,240" id="3">
				<widget position="10,0" render="Label" size="390,60" source="session.CurrentService" halign="center" valign="center" font="mediaportal_clean;22" foregroundColor="#fcc000" transparent="1">
					<convert type="MPServiceName">NameLCD</convert>
				</widget>
				<widget name="cover" position="142,63" size="126,126" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png" transparent="1" alphatest="blend" />
				<widget source="session.CurrentService" render="Label" position="10,192" size="390,30" font="mediaportal_clean;22" halign="center" valign="center" foregroundColor="#f0f0f0" transparent="1" >
				<convert type="MPServicePosition">Position,ShowHours</convert>
				</widget>
				</screen>'''

		self.skinName = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
		Screen.__init__(self, session)

	def updateCover(self, filename):
		CoverHelper(self['cover']).getCover(filename)