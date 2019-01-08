# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from imports import *
from keyboardext import VirtualKeyBoardExt
from Tools.BoundFunction import boundFunction
import Queue
import threading
from coverhelper import CoverHelper
from messageboxext import MessageBoxExt

screenList = []

try:
	f = open("/proc/stb/info/model", "r")
	model = ''.join(f.readlines()).strip()
except:
	model = ''

class SearchHelper:

	def __init__(self):
		self.lastSearchNum = -1
		self.searchKey = None
		self["suchtitel"] = Label(_("Search char."))
		self["suchhinweis"] = Label(_("A-Z search"))
		self["suche"] = Label("")
		self["bg_search"] = Label("")
		self["suche"].hide()
		self["suchtitel"].hide()
		self["suchhinweis"].hide()
		self["bg_search"].hide()

		self.numericalTextInput = NumericalTextInput()
		self.numericalTextInput.setUseableChars(u'1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ')
		if mp_globals.isDreamOS:
			self.numericalTextInput.timer_conn = self.numericalTextInput.timer.timeout.connect(self.doSearch)
		else:
			self.numericalTextInput.timer.callback.append(self.doSearch)

		self["search_numberactions"] = NumberActionMap(["MP_NumberActions"], {
			"1": self.goToNumber,
			"2": self.goToNumber,
			"3": self.goToNumber,
			"4": self.goToNumber,
			"5": self.goToNumber,
			"6": self.goToNumber,
			"7": self.goToNumber,
			"8": self.goToNumber,
			"9": self.goToNumber
		}, -2)

		self["search_keyactions"] = ActionMap(["MP_KeyActions"], {
			"0": boundFunction(self.goToLetter, "0"),
			"1": boundFunction(self.goToLetter, "1"),
			"2": boundFunction(self.goToLetter, "2"),
			"3": boundFunction(self.goToLetter, "3"),
			"4": boundFunction(self.goToLetter, "4"),
			"5": boundFunction(self.goToLetter, "5"),
			"6": boundFunction(self.goToLetter, "6"),
			"7": boundFunction(self.goToLetter, "7"),
			"8": boundFunction(self.goToLetter, "8"),
			"9": boundFunction(self.goToLetter, "9"),
			"a": boundFunction(self.goToLetter, "a"),
			"b": boundFunction(self.goToLetter, "b"),
			"c": boundFunction(self.goToLetter, "c"),
			"d": boundFunction(self.goToLetter, "d"),
			"e": boundFunction(self.goToLetter, "e"),
			"f": boundFunction(self.goToLetter, "f"),
			"g": boundFunction(self.goToLetter, "g"),
			"h": boundFunction(self.goToLetter, "h"),
			"i": boundFunction(self.goToLetter, "i"),
			"j": boundFunction(self.goToLetter, "j"),
			"k": boundFunction(self.goToLetter, "k"),
			"l": boundFunction(self.goToLetter, "l"),
			"m": boundFunction(self.goToLetter, "m"),
			"n": boundFunction(self.goToLetter, "n"),
			"o": boundFunction(self.goToLetter, "o"),
			"p": boundFunction(self.goToLetter, "p"),
			"q": boundFunction(self.goToLetter, "q"),
			"r": boundFunction(self.goToLetter, "r"),
			"s": boundFunction(self.goToLetter, "s"),
			"t": boundFunction(self.goToLetter, "t"),
			"u": boundFunction(self.goToLetter, "u"),
			"v": boundFunction(self.goToLetter, "v"),
			"w": boundFunction(self.goToLetter, "w"),
			"x": boundFunction(self.goToLetter, "x"),
			"y": boundFunction(self.goToLetter, "y"),
			"z": boundFunction(self.goToLetter, "z"),
			"space": boundFunction(self.goToLetter, " "),
			"back": boundFunction(self.goToLetter, "")
		}, -3)

	def goToNumber(self, num):
		pass

	def goToLetter(self, key):
		pass

	def showSearchkey(self, num):
		self.searchKey = self.numericalTextInput.mapping[num][self.numericalTextInput.pos]
		self['suche'].setText(str(self.searchKey))
		if self.lastSearchNum == -1:
			self['suche'].show()
			self["suchtitel"].show()
			self["bg_search"].show()
		self.lastSearchNum = num

	def showSearchWord(self):
		self['suche'].setText(str(self.keyword))
		self['suche'].show()
		self["suchtitel"].show()
		self["bg_search"].show()

	def doSearch(self):
		self.lastSearchNum = -1
		self['suche'].hide()
		self["suchtitel"].hide()
		self["bg_search"].hide()
		self.showInfos()

class MPSetupScreen(Screen):

	def __init__(self, session, parent=None, skin=None, default_cover='file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/default_cover.png', *ret_args):
		self.default_cover = default_cover
		self.skinmsg = ''
		if skin:
			self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
			path = "%s/%s/%s.xml" % (self.skin_path, mp_globals.currentskin, skin)
			if not fileExists(path):
				path = self.skin_path + mp_globals.skinFallback + "/%s.xml" % skin
				self.skinmsg = skin
			with open(path, "r") as f:
				self.skin = f.read()
				f.close()

		self.skinName = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])

		Screen.__init__(self, session, parent)
		screenList.append((self, ret_args))

		self.onFirstExecBegin.append(self.skinMessage)
		self.onFirstExecBegin.append(self.loadDisplayCover)
		self.onFirstExecBegin.append(self.skinMessage)

	def loadDisplayCover(self):
		self.summaries.updateCover(self.default_cover)

	def skinMessage(self):
		if self.skinmsg != '':
			self.session.open(MessageBoxExt, _("Mandatory skin file %s is missing!" % self.skinmsg), MessageBoxExt.TYPE_ERROR)

	def createSummary(self):
		return MPScreenSummary

class MPScreen(Screen, HelpableScreen):

	DEFAULT_LM = 0

	def __init__(self, session, parent=None, skin=None, widgets=None, default_cover='file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/default_cover.png', *ret_args):
		self.default_cover = default_cover
		self.skinmsg = ''
		if skin:
			self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
			path = "%s/%s/%s.xml" % (self.skin_path, mp_globals.currentskin, skin)
			if not fileExists(path):
				path = self.skin_path + mp_globals.skinFallback + "/%s.xml" % skin
				self.skinmsg = skin
			with open(path, "r") as f:
				self.skin = f.read()
				f.close()

			if skin == 'MP_Playlist':
				if not mp_globals.isDreamOS:
					self.skin = re.sub(r'progress_pointer="(.*?):\d+,\d+" render="PositionGauge"', r'pixmap="\1" render="Progress"', self.skin)
					self.skin = re.sub(r'type="MPServicePosition">Gauge</convert>', r'type="MPServicePosition">Position</convert>', self.skin)

			if widgets:
				self.skin = self.skin.replace('</screen>', '')
				for wf in widgets:
					path = "%s/%s/%s.xml" % (self.skin_path, mp_globals.currentskin, wf)
					if not fileExists(path):
						path = self.skin_path + mp_globals.skinFallback + "/%s.xml" % wf
						self.skinmsg = wf
					f = open(path, "r")
					for widget in f:
						self.skin += widget
					f.close()
				self.skin += '</screen>'

		self.skinName = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])

		self.DEFAULT_LM = 0

		Screen.__init__(self, session, parent)
		screenList.append((self, ret_args))
		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)
		self.mp_hide = False
		self["mp_specActions"]  = ActionMap(["MP_SpecialActions"], {
			"specTv": self.mp_showHide
		}, -2)

		self["mp_specActions2"] = HelpableActionMap(self, "MP_SpecialActions", {
			"specTmdb" : (self.mp_tmdb, _("Show TMDb info"))
		}, -1)

		self["MP_Actions"] = HelpableActionMap(self, "MP_Actions", {
			"deleteBackward" : (self.keyTxtPageUp, _("Scroll description backward")),
			"deleteForward"  : (self.keyTxtPageDown, _("Scroll description forward"))
		}, -1)

		HelpableScreen.__init__(self)

		self['title'] = Label("")
		self['ContentTitle'] = Label("")
		self['name'] = Label("")
		self['F1'] = Label("")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label("")
		self['coverArt'] = Pixmap()
		self['Page'] = Label("")
		self['page'] = Label("")
		self['handlung'] = ScrollLabel("")

		self.filmQ = Queue.Queue(0)
		self.hanQ = Queue.Queue(0)
		self.picQ = Queue.Queue(0)
		self.updateP = 0
		self.eventL = threading.Event()
		self.eventP = threading.Event()

		self.langoffset = 0
		self.keyword = ''
		self.keyLocked = False

		self.keytimer = eTimer()
		if mp_globals.isDreamOS:
			self.keytimer_conn = self.keytimer.timeout.connect(self.cleankeyword)
		else:
			self.keytimer.callback.append(self.cleankeyword)

		if mp_globals.isDreamOS:
			self.onLayoutFinish.append(self._animation)

		self.onLayoutFinish.append(self.loadDefaultCover)
		self.onFirstExecBegin.append(self.loadDisplayCover)
		self.onFirstExecBegin.append(self.skinMessage)

	def skinMessage(self):
		if self.skinmsg != '':
			self.session.open(MessageBoxExt, _("Mandatory skin file %s is missing!" % self.skinmsg), MessageBoxExt.TYPE_ERROR)

	def loadDisplayCover(self):
		self.summaries.updateCover(self.default_cover)

	def loadDefaultCover(self):
		CoverHelper(self['coverArt']).getCover(self.default_cover)

	def _animation(self):
		#try:
			#self['title'].instance.setShowHideAnimation(config_mp.mediaportal.animation_label.value)
			#self['ContentTitle'].instance.setShowHideAnimation(config_mp.mediaportal.animation_label.value)
			#self['name'].instance.setShowHideAnimation(config_mp.mediaportal.animation_label.value)
			#self['coverArt'].instance.setShowHideAnimation(config_mp.mediaportal.animation_coverart.value)
		#except:
			pass

	def mp_showHide(self):
		if not self.mp_hide:
			self.mp_hide = True
			self.hide()
			self.session.nav.playService(mp_globals.lastservice)
			self.summaries.updateCover(None)
		else:
			self.mp_hide = False
			self.show()
			if config_mp.mediaportal.restorelastservice.value == "1" and not config_mp.mediaportal.backgroundtv.value:
				self.session.nav.playService(mp_globals.lastservice)
			else:
				self.session.nav.stopService()
			self.summaries.updateCover(self.default_cover)

	def close(self, *args):
		if self.mp_hide:
			return
		Screen.close(self, *args)
		if len(screenList):
			screenList.pop()

	def mp_close(self, *args):
		Screen.close(self, *args)

	def showInfos(self):
		exist = self['liste'].getCurrent()
		if self.keyLocked or exist == None:
			return
		title = self['liste'].getCurrent()[0][0]
		if not re.match('.*?---------------', title):
			if not re.match('.*?———————————————', title):
				self['name'].setText(title)
			else:
				self['name'].setText('')
		else:
			self['name'].setText('')

	def mp_tmdb(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		from tmdb import MediaPortalTmdbScreen
		try:
			movie_title = self['liste'].getCurrent()[0][0]
			self.session.open(MediaPortalTmdbScreen, movie_title)
		except:
			try:
				movie_title = self.thumbfilmliste[self.section * self.thumbsC + self.index][0]
				self.session.open(MediaPortalTmdbScreen, movie_title)
			except:
				pass

	def loadPageQueued(self, headers={}):
		self['name'].setText(_('Please wait...'))
		while not self.filmQ.empty():
			url = self.filmQ.get_nowait()
		getPage(url, headers=headers).addCallback(self.loadPageData).addErrback(self.dataError)

	def loadPic(self):
		if self.picQ.empty():
			self.eventP.clear()
			return
		while not self.picQ.empty():
			self.picQ.get_nowait()
		streamName = self['liste'].getCurrent()[0][0]
		self['name'].setText(streamName)
		streamPic = self['liste'].getCurrent()[0][2]
		self.showInfos()
		self.updateP = 1
		CoverHelper(self['coverArt'], self.ShowCoverFileExit).getCover(streamPic)

	def ShowCoverFileExit(self):
		self.updateP = 0;
		self.keyLocked	= False
		if not self.filmQ.empty():
			self.loadPageQueued()
		else:
			self.eventL.clear()
			self.loadPic()

	def loadPicQueued(self):
		self.picQ.put(None)
		if not self.eventP.is_set():
			self.eventP.set()
		self.loadPic()

	def getLastPage(self, data, paginationregex, pageregex='.*>(\d+)<'):
		if paginationregex == '':
			lastp = re.search(pageregex, data, re.S)
			if lastp:
				lastp = lastp.group(1).replace(",","").replace('.','').replace(' ','').strip()
				self.lastpage = int(lastp)
			else:
				self.lastpage = 1
		else:
			lastpparse = re.search(paginationregex, data, re.S)
			if lastpparse:
				lastp = re.search(pageregex, lastpparse.group(1), re.S)
				if lastp:
					lastp = lastp.group(1).replace(",","").replace('.','').replace(' ','').strip()
					self.lastpage = int(lastp)
				else:
					self.lastpage = 1
			else:
				self.lastpage = 1
		self['page'].setText(str(self.page) + ' / ' + str(self.lastpage))

	def keyPageNumber(self):
		if self.mp_hide:
			return
		self.session.openWithCallback(self.callbackkeyPageNumber, VirtualKeyBoardExt, title = (_("Enter page number")), text = str(self.page), is_dialog=True)

	def callbackkeyPageNumber(self, answer):
		if answer is not None:
			answer = re.findall('\d+', answer)
		else:
			return
		if answer:
			if int(answer[0]) < self.lastpage + 1:
				self.page = int(answer[0])
				self.loadPage()
			else:
				self.page = self.lastpage
				self.loadPage()

	def suchen(self, auto_text_init=False, suggest_func=None):
		if self.mp_hide:
			return
		self.session.openWithCallback(self.SuchenCallback, VirtualKeyBoardExt, title = (_("Enter search criteria")), text = self.suchString, is_dialog=True, auto_text_init=auto_text_init, suggest_func=suggest_func)

	def keyUpRepeated(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		self['liste'].down()

	def keyLeftRepeated(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		self['liste'].pageDown()

	def key_repeatedUp(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		self.loadPicQueued()

	def keyPageDown(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		if not self.page < 2:
			self.page -= 1
			self.loadPage()

	def keyPageUp(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		if self.page < self.lastpage:
			self.page += 1
			self.loadPage()

	def keyLeft(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		self['liste'].pageUp()
		self.showInfos()

	def keyRight(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		self['liste'].pageDown()
		self.showInfos()

	def keyUp(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		self['liste'].up()
		self.showInfos()

	def keyDown(self):
		if self.mp_hide:
			return
		if self.keyLocked:
			return
		self['liste'].down()
		self.showInfos()

	def keyTxtPageUp(self):
		if self.mp_hide:
			return
		self['handlung'].pageUp()

	def keyTxtPageDown(self):
		if self.mp_hide:
			return
		self['handlung'].pageDown()

	def keyCancel(self):
		if self.mp_hide:
			return
		self.close()

	def keyLetterGlobal(self, key, list):
		if key == "":
			self.keyword = self.keyword[:-1]
		else:
			self.keyword = self.keyword + key

		self.showSearchWord()
		self.getListIndex(self.keyword, list)
		self.keytimer.start(1500, 1)

	def cleankeyword(self):
		self.keyword = ''
		self.doSearch()

	def keyNumberGlobal(self, key, list):
		unichar = self.numericalTextInput.getKey(key)
		charstr = unichar.encode("utf-8")
		if len(charstr) == 1:
			print "keyNumberGlobal:", charstr[0]
			self.getListIndex(charstr[0], list)

	def getListIndex(self, letter, list):
		if len(list) > 0:
			countIndex = -1
			found = False
			for x in list:
				countIndex += 1
				f = len(letter)
				if f == 1:
					if x[0][0].lower() == letter.lower():
						found = True
						break
				elif f > 1:
					if x[0][:f].lower() == letter.lower():
						found = True
						break
					elif letter.lower() in x[0].lower():
						found = True
						break
			print "index:", countIndex
			if found:
				self['liste'].moveToIndex(countIndex)

	def dataError(self, error):
		from debuglog import printlog as printl
		printl(error,self,"E")

	@staticmethod
	def closeAll():
		i = len(screenList)
		while i > 0:
			screen, args = screenList.pop()
			if screen.mp_hide:
				return
			screen.mp_close(*args)
			i -= 1

	def createSummary(self):
		return MPScreenSummary

####### defaults

	def _defaultlistleft(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res

	def _defaultlistcenter(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0]))
		return res

	def _defaultlistleftmarked(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]

		skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/images/watched.png" % (skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = "%s/%s/images/watched.png" % (skin_path, mp_globals.skinFallback)
			if not fileExists(path):
				path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/watched.png"

		watched = LoadPixmap(path)
		pwidth = watched.size().width()
		pheight = watched.size().height()
		vpos = round(float((height-pheight)/2))
		if entry[2]:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, vpos, pwidth, pheight, watched))

		try:
			if entry[3]:
				if entry[3] == '1':
					iconlng = 'DE'
				elif entry[3] == '2':
					iconlng = 'EN'
				elif entry[3] == '5':
					iconlng = 'ES'
				elif entry[3] == '6':
					iconlng = 'FR'
				elif entry[3] == '7':
					iconlng = 'TR'
				elif entry[3] == '8':
					iconlng = 'JP'
				elif entry[3] == '11':
					iconlng = 'IT'
				elif entry[3] == '15':
					iconlng = 'DEUS'
				elif entry[3] == '24':
					iconlng = 'GR'
				elif entry[3] == '25':
					iconlng = 'RU'
				elif entry[3] == '26':
					iconlng = 'IN'
				else:
					iconlng = entry[3]

				path = "%s/%s/images/%s.png" % (skin_path, mp_globals.currentskin, iconlng)
				if not fileExists(path):
					path = "%s/%s/images/%s.png" % (skin_path, mp_globals.skinFallback, iconlng)
					if not fileExists(path):
						path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/%s.png" % iconlng

				lang = LoadPixmap(path)
				lwidth = lang.size().width()
				lheight = lang.size().height()
				vpos = round(float((height-lheight)/2))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, pwidth+50, vpos, lwidth, lheight, lang))
				self.langoffset = lwidth+25
		except:
			pass

		if (config_mp.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters_prz, entry[0], re.S|re.I)) or (config_mp.mediaportal.realdebrid_use.value and re.search(mp_globals.premium_hosters_rdb, entry[0], re.S|re.I)):
			premiumFarbe = int(config_mp.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, pwidth+50+self.langoffset, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, pwidth+50+self.langoffset, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))

		return res

	def _defaultlisthoster(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		if (config_mp.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters_prz, entry[0], re.S|re.I)) or (config_mp.mediaportal.realdebrid_use.value and re.search(mp_globals.premium_hosters_rdb, entry[0], re.S|re.I)):
			premiumFarbe = int(config_mp.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0]))
		return res

	def MPLog(self, entry):
		width = self['mplog'].instance.size().width()
		height = self['mplog'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res

	def MPSort(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]

		skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/images/select.png" % (skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = "%s/%s/images/select.png" % (skin_path, mp_globals.skinFallback)
			if not fileExists(path):
				path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/select.png"

		select = LoadPixmap(path)
		pwidth = select.size().width()
		pheight = select.size().height()
		vpos = round(float((height-pheight)/2))
		if self.selected and entry[0] == self.last_plugin_name:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, vpos, pwidth, pheight, select))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, pwidth+50+self.langoffset, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))

		return res
##################

####### simplelist
	@staticmethod
	def getIconPath(icon_name):
		skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/images/%s" % (skin_path, mp_globals.currentskin, icon_name)
		if not fileExists(path):
			path = "%s/%s/images/%s" % (skin_path, mp_globals.skinFallback, icon_name)
			if not fileExists(path):
				path = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/%s" % icon_name
		return path

	def simplelistListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]

		if entry[0] in ('1', '4', '5', '6', '7', '8', '9'):
			icon_name = "directory.png"
		else:
			icon_name = "playlist.png"

		path = self.getIconPath(icon_name)
		icon = LoadPixmap(path)
		pwidth = icon.size().width()
		pheight = icon.size().height()
		vpos = round(float((height-pheight)/2))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, vpos, pwidth, pheight, icon))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, pwidth+50, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		return res

	# simplelist - iptv
	def simpleListTVGListEntry(self, entry):
		import time
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		self.ml.l.setFont(1, gFont(mp_globals.font, height - 7 * mp_globals.sizefactor))
		res = [entry]
		color = int(entry[3][-1], 0) if entry[3] else 0xD3D3D3
		tvg_id = entry[3][2] if entry[3] and ('tvg-id' in entry[3]) and entry[3][2] and not entry[3][2].endswith('.ink') else None
		event = ""
		if tvg_id:
			events=mpepg.getEvent(tvg_id)
			if events:
				ch, now, next = events
				event = '%s - %s  %s' % (time.strftime('%H:%M',time.localtime(now[0])),time.strftime('%H:%M',time.localtime(now[1])),now[2])
				r_tm = '%+d min' % int((now[1]-time.mktime(time.localtime())) / 60)

		fhdoffset = 140 if mp_globals.videomode == 2 else 0
		width2 = 190+fhdoffset if event else width+fhdoffset
		icon_name = entry[2]
		iconwidth = self.DEFAULT_LM
		if icon_name:
			if icon_name[:4] not in ('http', 'file'):
				path = self.getIconPath(icon_name)
				icon = LoadPixmap(path)
				pwidth = icon.size().width()
				pheight = icon.size().height()
				vpos = round(float((height-pheight)/2))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 25, vpos, pwidth, pheight, icon))
				iconwidth = pwidth+50

		res.append((eListboxPythonMultiContent.TYPE_TEXT, iconwidth, 0, width2, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], color))
		if event:
			x_ofs2 = width2+iconwidth+10
			width2 = width-x_ofs2-self.DEFAULT_LM-100
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x_ofs2, 0, width2, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, event))
			x_ofs2 += width2+5
			width2 = 75
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x_ofs2, 0, width2, height, 1, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, r_tm))
		return res
##################

####### twitch
	def twitchListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 110, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[1]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 120, 0, width - 120, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res

####### pornhub
	def pornhubPlayListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width - 210, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 200, 0, 200, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "Videos: " + entry[1]))
		return res

	def pornhubPornstarListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "Rank: " + entry[3]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 160, 0, width - 370, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 200, 0, 200, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "Videos: " + entry[4]))
		return res
##################

####### kinox

	def kxStreamListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		if (config_mp.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters_prz, entry[0], re.S|re.I)) or (config_mp.mediaportal.realdebrid_use.value and re.search(mp_globals.premium_hosters_rdb, entry[0], re.S|re.I)):
			premiumFarbe = int(config_mp.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 250, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 340, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 180, 0, 180, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[4], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 250, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 340, 0, 150, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 180, 0, 180, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[4]))
		return res

	def kxListSearchEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 120, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 130, 0, width - 130, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		return res
##################

####### ddl.me
	def DDLME_FilmListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 210 - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 200 - 2 * self.DEFAULT_LM, 0, 200, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[4]))
		return res

	def DDLMEStreamListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		if (config_mp.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters_prz, entry[0], re.S|re.I)) or (config_mp.mediaportal.realdebrid_use.value and re.search(mp_globals.premium_hosters_rdb, entry[0], re.S|re.I)):
			premiumFarbe = int(config_mp.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0] + entry[2], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, entry[0] + entry[2]))
		return res

	def DDLMEStreamListEntry2(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		if (config_mp.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters_prz, entry[0], re.S|re.I)) or (config_mp.mediaportal.realdebrid_use.value and re.search(mp_globals.premium_hosters_rdb, entry[0], re.S|re.I)):
			premiumFarbe = int(config_mp.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, 220, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, width - 720 - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2], premiumFarbe))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 450 - 2 * self.DEFAULT_LM, 0, 450, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, 250, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 260, 0, width - 720 - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 450 - 2 * self.DEFAULT_LM, 0, 450, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
		return res
##################

####### YouTube
	def YT_ListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		if entry[6] == 'R':
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, 160, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0], int("0xFF0000", 0)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 170, 0, width - 170 - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER,entry[1]))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.DEFAULT_LM, 0, width - 2 * self.DEFAULT_LM, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]+entry[1]))
		return res
##################

####### fashiontvguide
	def TvListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height * 2, 0, RT_HALIGN_LEFT, entry[0]+entry[1]))
		return res
##################

####### br_tv
	def BRBody1(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 2 * mp_globals.sizefactor))
		res = [entry]
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2] + " - " + entry[0]))
		return res
##################

####### searchalluc, sharedir
	def searchallucMultiListEntry(self, entry):
		width = self['liste'].instance.size().width()
		height = self['liste'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 3 * mp_globals.sizefactor))
		res = [entry]
		if (config_mp.mediaportal.premiumize_use.value and re.search(mp_globals.premium_hosters_prz, entry[2], re.S|re.I)) or (config_mp.mediaportal.realdebrid_use.value and re.search(mp_globals.premium_hosters_rdb, entry[2], re.S|re.I)):
			premiumFarbe = int(config_mp.mediaportal.premium_color.value, 0)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width - 380, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 370, 0, 180, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 180, 0, 180, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2], premiumFarbe))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width - 380, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[0]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 370, 0, 180, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[3]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 180, 0, 180, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, entry[2]))
		return res
##################

class MPScreenSummary(Screen):

	def __init__(self, session, parent):
		try:
			displaysize = getDesktop(1).size()
			if model in ["dm900","dm920"]:
				disp_id = ' id="3"'
				disp_size = str(displaysize.width()-8) + "," + str(displaysize.height())
				disp_pos = "8,0"
			elif model in ["dm7080"]:
				disp_id = ' id="3"'
				disp_size = str(displaysize.width()) + "," + str(displaysize.height()-14)
				disp_pos = "0,0"
			elif model in ["dm820"]:
				disp_id = ' id="2"'
				disp_size = str(displaysize.width()) + "," + str(displaysize.height())
				disp_pos = "0,0"
			else:
				disp_id = ' id="1"'
				disp_size = str(displaysize.width()) + "," + str(displaysize.height())
				disp_pos = "0,0"

		except:
			disp_size = "1,1"
			disp_id = ' id="1"'
			disp_pos = "0,0"

		self["cover"] = Pixmap()

		self.skin = '''<screen name="MPScreenSummary" backgroundColor="#00000000" position="''' + disp_pos + '''" size="''' + disp_size  + '''"''' + disp_id + '''>
				<widget name="cover" position="center,center" size="''' + disp_size + '''" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png" transparent="1" alphatest="blend" />
				</screen>'''

		self.skinName = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
		Screen.__init__(self, session)

	def updateCover(self, filename):
		CoverHelper(self['cover']).getCover(filename)