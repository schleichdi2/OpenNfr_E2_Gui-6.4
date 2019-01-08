# -*- coding: utf-8 -*-

from Plugins.Extensions.MediaPortal.plugin import _
from imports import *
from twagenthelper import twAgentGetPage
from debuglog import printlog as printl

MDEBUG = False

class MenuHelper(MPScreen):
	def __init__(self, session, menuMaxLevel, genreMenu, baseUrl, genreBase, menuListentry, skin='MP_Plugin', default_cover='file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/default_cover.png', widgets_files=None, cookieJar=None):

		self.mh_cookieJar = cookieJar

		MPScreen.__init__(self, session, skin=skin, default_cover=default_cover, widgets=widgets_files)

		self["actions"] = ActionMap(["MP_Actions2", "MP_Actions"], {
			"ok"    	: self.mh_keyOK,
			"cancel"	: self.mh_keyCancel,
			"up"		: self.mh_keyUp,
			"down"		: self.mh_keyDown,
			"left"		: self.mh_keyLeft,
			"0"		: self.closeAll,
			"right"		: self.mh_keyRight,
			"upUp" 		: self.key_repeatedUp,
			"rightUp" 	: self.key_repeatedUp,
			"leftUp" 	: self.key_repeatedUp,
			"downUp" 	: self.key_repeatedUp,
			"upRepeated"	: self.keyUpRepeated,
			"downRepeated"	: self.keyDownRepeated,
			"rightRepeated"	: self.keyRightRepeated,
			"leftRepeated"	: self.keyLeftRepeated
		}, -1)

		self['name'] = Label(_("Selection:"))

		self.mh_keyLocked = True
		self.mh_On_setGenreStrTitle = []
		self.mh_genreMenu = genreMenu
		self.mh_menuListentry = menuListentry
		self.mh_menuLevel = 0
		self.mh_menuMaxLevel = menuMaxLevel
		self.mh_menuIdx = [0,0,0,0]
		self.mh_genreSelected = False
		self.mh_menuListe = []
		self.mh_baseUrl = baseUrl
		self.mh_genreBase = genreBase
		self.mh_genreName = ["","","",""]
		self.mh_genreUrl = ["","","",""]
		self.mh_genreTitle = ""
		self.mh_lastPageUrl = ""
		self.contenttitle = "%%EMPTY%%"

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

	def mh_initMenu(self):
		self.mh_buildMenu(self.mh_baseUrl)

	def mh_buildMenu(self, url, addlocation=False, agent=None, headers=std_headers):
		self.mh_menuListe = []
		self.mh_menuListe.append((_('Please wait...'),None))
		self.ml.setList(map(self.mh_menuListentry, self.mh_menuListe))
		self.mh_lastPageUrl = url
		self.d_print("mh_buildMenu:",url)
		if not url:
			self.mh_parseCategorys(None)
		else:
			try:
				import requests
				s = requests.session()
				headers = {'User-Agent': agent}
				page = s.get(url, cookies=self.mh_cookieJar, headers=headers, timeout=15)
				return self.mh_parseCategorys(page.content)
			except:
				return twAgentGetPage(url, agent=agent, cookieJar=self.mh_cookieJar, headers=headers, addlocation=addlocation, timeout=(10,30)).addCallback(self.mh_parseCategorys).addErrback(self.mh_dataError)

	def mh_dataError(self, error):
		self.d_print("mh_dataError:")
		printl(error,self,"E")

	def mh_parseCategorys(self, data):
		self.d_print('mh_parseCategorys:')
		entrys = self.mh_parseData(data)
		self.mh_genMenu(entrys)

	def mh_parseData(self, data):
		return None

	def mh_genMenu(self, entrys):
		self.d_print('mh_genMenu:')
		if entrys:
			root_len = len(entrys[0][0].split('/'))
			for (url, nm) in entrys:
				i = len(url.split('/'))-root_len
				nm = decodeHtml(nm)
				if i == 0 or self.mh_menuMaxLevel == 0:
					self.mh_genreMenu[0].append((nm, url))
					self.d_print('Menu[0][-1]=',nm,' : ',url)

					key1 = url
					self.d_print('key1=',key1)

					if self.mh_menuMaxLevel > 0:
						self.mh_genreMenu[1].append([])

					if self.mh_menuMaxLevel > 1:
						self.mh_genreMenu[2].append([])
					continue

				if self.mh_menuMaxLevel > 0 and i == 1:
					if self.mh_menuMaxLevel > 1:
						self.mh_genreMenu[2][-1].append([])
					if key1 in url:
						key2 = url
						url = url.replace(key1, '', 1)
						self.mh_genreMenu[1][-1].append((nm, url))
						self.d_print('Menu[1][-1]=',nm,' : ',url)
					else:
						key2 = None
						self.mh_genreMenu[1][-1].append(None)
						self.d_print('Menu[1][-1]=None')
					continue

				if self.mh_menuMaxLevel > 1 and i == 2:
					if key2 in url:
						url = url.replace(key2, '', 1)
						self.mh_genreMenu[2][-1][-1].append((nm, url))
						self.d_print('Menu[2][-1][-1]=',nm,' : ',url)
					else:
						self.mh_genreMenu[2][-1][-1].append(None)
						self.d_print('Menu[2][-1][-1]=None')

			self.mh_loadMenu()
		else:
			self.d_print('No menudata found!')
			self.mh_menuListe[0]((_('No menudata found!'),None))
			self.ml.setList(map(self.mh_menuListentry, self.mh_menuListe))

	def scanMenu(self,html,menu_marker,marker_num=1,findall=True,themes=[],themes_ex=[],url_ex=[],base_url=None,init_level=-1):
		if themes:
			findall = False

		level = init_level
		l = len(html)
		a = 0
		mfound = tfound = skip_level0 = False
		menu = []

		while a < l:
			if not mfound:
				for mi in range(marker_num):
					i = html.find(menu_marker,a)
					if i >= 0:
						self.d_print( menu_marker,i)
						a = i + len(menu_marker)
						i = html.find('>',a)
						if i >= 0:
							a = i + 1
							mfound = True
							self.d_print( ">",i)
					else:
						mfound = False
						break
			i = html.find('<',a)
			if i >= 0:
				a = i + 1
				i = html.find('ul',a,a+2)
				if i >= 0:
					self.d_print( "<ul",i)
					a = i + 2
					i = html.find('>',a)
					if i >= 0:
						a = i + 1
						if tfound or skip_level0:
							level += 1
							self.d_print( 'level:',level)
						self.d_print( ">",i)
						continue
					else:
						break

				i = html.find('/ul>',a,a+4)
				if i >= 0:
					self.d_print( "</ul>",i)
					a = i + 4
					if tfound or skip_level0:
						level -= 1
						self.d_print( 'level:',level)
						if not level:
							tfound = False
							level = -1
					continue

				i = html.find('/li>',a,a+4)
				if i >= 0:
					self.d_print( "</li>",i)
					a = i + 4
					continue

				i = html.find('li',a,a+2)
				if i >= 0:
					a = i+2
					self.d_print( "<li",i)
					i = html.find('>',a)
					if i >= 0:
						self.d_print( ">",i)
						a = i + 1
						i = html.find('<a ',a)
						if i >= 0:
							self.d_print( "<a ",i)
							a = i
							b = html.find('>',a)
							i = html.find('href="',a,b)
							if i < 0:
								i = html.find(' rel="',a,b)
							if i >= 0:
								self.d_print( 'href="',i)
								a = i + 6
								i = html.find('"',a)
								if i >= 0:
									self.d_print( '"',i)
									url = html[a:i]
									a = i + 1
									i = html.find('>',a)
									if i >= 0:
										a = i + 1
										i = html.find('<img',a,a+4)
										if i >= 0:
											a = i + 4
											i = html.find('/>',a)
											if i >= 0:
												a = i + 2
										i = html.find('</a>',a)
										if i >= 0:
											name = html[a:i]
											name = stripAllTags(name)
											self.d_print( '</a>',i)
											if not tfound and findall or name in themes:
												if name in themes_ex:
													self.d_print('found t_ex:',name)
													level += 1
													self.d_print('skip_level0 = True')
													skip_level0 = True
												else:
													name = decodeHtml(name).strip()
													self.d_print( 'found:',name)
													if skip_level0 and level == 0:
														self.d_print('skip_level0 = False')
														skip_level0 = False
														level -= 1
													if not skip_level0:
														tfound = True
														level += 1
											elif not tfound:
												self.d_print('name:',name)
											a = i + 4
											if tfound and not skip_level0:
												if themes_ex and [1 for item in themes_ex if item in name]:
													self.d_print('found t_ex:',name)
													continue
												if url_ex and [1 for item in url_ex if item in url]:
													continue
												if url[-1] == '/':
													url = url[:-1]
												if base_url:
													url = url.replace(base_url,'')
												self.d_print("level:",level,' URL:',url,' Name:',name)
												menu.append((level,url,name))
											continue
				self.d_print("scan inter.")
				break
		return menu

	def mh_genMenu2(self,menudata):
		self.d_print('mh_genMenu2:')
		self.mh_genreMenu = []
		self.mh_menuMaxLevel = -1

		if menudata:
			for i,a,b in menudata:
				if i > self.mh_menuMaxLevel:
					self.mh_menuMaxLevel = i
					self.mh_genreMenu.append([])
			self.d_print('mh_menuMaxLevel=',self.mh_menuMaxLevel)

			for (i, url, nm) in menudata:
				nm = decodeHtml(nm)
				if i == 0:
					self.mh_genreMenu[0].append((nm, url))
					self.d_print('Menu[0][-1]=',nm,' : ',url)

					if self.mh_menuMaxLevel > 0:
						self.mh_genreMenu[1].append([])

					if self.mh_menuMaxLevel > 1:
						self.mh_genreMenu[2].append([])

					if self.mh_menuMaxLevel > 2:
						self.mh_genreMenu[3].append([])
					continue

				elif self.mh_menuMaxLevel > 0 and i == 1:
					if self.mh_menuMaxLevel > 1:
						self.mh_genreMenu[2][-1].append([])
					if self.mh_menuMaxLevel > 2:
						self.mh_genreMenu[3][-1].append([])
					self.mh_genreMenu[1][-1].append((nm, url))
					self.d_print('Menu[1][-1]=',nm,' : ',url)
					continue

				elif self.mh_menuMaxLevel > 1 and i == 2:
					if self.mh_menuMaxLevel > 2:
						self.mh_genreMenu[3][-1][-1].append([])
					self.mh_genreMenu[2][-1][-1].append((nm, url))
					self.d_print('Menu[2][-1][-1]=',nm,' : ',url)

				elif self.mh_menuMaxLevel > 2 and i == 3:
					self.mh_genreMenu[3][-1][-1][-1].append((nm, url))
					self.d_print('Menu[3][-1][-1][-1]=',nm,' : ',url)

			self.mh_loadMenu()
		else:
			self.d_print('No menudata found!')
			self.ml.setList(map(self.mh_menuListentry, [(_('No results found!'),None)]))
			self.mh_setGenreStrTitle()

	def mh_setGenreStrTitle(self):
		try:
			genreName = self['liste'].getCurrent()[0][0]
			genreLink = self['liste'].getCurrent()[0][1]
			if self.mh_menuLevel in range(self.mh_menuMaxLevel+1):
				if self.mh_menuLevel == 0:
					self.mh_genreName[self.mh_menuLevel] = genreName
				else:
					self.mh_genreName[self.mh_menuLevel] = ':'+genreName

				self.mh_genreUrl[self.mh_menuLevel] = genreLink

			if self.mh_menuLevel == 1:
				contenttitle = "%s" % (self.mh_genreName[0])
			elif self.mh_menuLevel == 2:
				contenttitle = "%s%s" % (self.mh_genreName[0],self.mh_genreName[1])
			else:
				if self.contenttitle == "%%EMPTY%%":
					self.contenttitle = self['ContentTitle'].text
				else:
					contenttitle = ""
			if self.contenttitle != "%%EMPTY%%" and self.mh_menuLevel == 0:
				self['ContentTitle'].setText(self.contenttitle)
			else:
				self['ContentTitle'].setText(contenttitle)
			self.mh_genreTitle = "%s%s%s" % (self.mh_genreName[0],self.mh_genreName[1],self.mh_genreName[2])
			if self.mh_genreTitle != (400 * "—"):
				self['name'].setText(_("Selection:")+" "+self.mh_genreTitle)
			else:
				self['name'].setText("")

			for f, args in self.mh_On_setGenreStrTitle:
				f(*args)
		except:
			pass

	def mh_loadMenu(self):
		self.d_print("loadMenu:")
		self.mh_setMenu(0, True)
		self.mh_keyLocked = False

	def keyUpRepeated(self):
		if self.mh_keyLocked:
			return
		self['liste'].up()

	def keyDownRepeated(self):
		if self.mh_keyLocked:
			return
		self['liste'].down()

	def key_repeatedUp(self):
		if self.mh_keyLocked:
			return
		self.mh_menuIdx[self.mh_menuLevel] = self['liste'].getSelectedIndex()
		self.mh_setGenreStrTitle()

	def keyLeftRepeated(self):
		if self.mh_keyLocked:
			return
		self['liste'].pageUp()

	def keyRightRepeated(self):
		if self.mh_keyLocked:
			return
		self['liste'].pageDown()

	def mh_keyUp(self):
		self['liste'].up()
		self.mh_menuIdx[self.mh_menuLevel] = self['liste'].getSelectedIndex()
		self.mh_setGenreStrTitle()

	def mh_keyDown(self):
		self['liste'].down()
		self.mh_menuIdx[self.mh_menuLevel] = self['liste'].getSelectedIndex()
		self.mh_setGenreStrTitle()

	def mh_keyMenuUp(self):
		self.d_print("keyMenuUp:")
		if self.mh_keyLocked:
			return
		self.mh_menuIdx[self.mh_menuLevel] = self['liste'].getSelectedIndex()
		self.mh_setMenu(-1)

	def mh_keyRight(self):
		self['liste'].pageDown()
		self.mh_menuIdx[self.mh_menuLevel] = self['liste'].getSelectedIndex()
		self.mh_setGenreStrTitle()

	def mh_keyLeft(self):
		self['liste'].pageUp()
		self.mh_menuIdx[self.mh_menuLevel] = self['liste'].getSelectedIndex()
		self.mh_setGenreStrTitle()

	def mh_keyOK(self):
		self.d_print("keyOK:")
		if self.mh_keyLocked or not self.mh_menuListe:
			return

		self.mh_menuIdx[self.mh_menuLevel] = self['liste'].getSelectedIndex()
		self.mh_setMenu(1)

		if self.mh_genreSelected:
			self.d_print("Genre selected:")
			self.mh_callGenreListScreen()

	def mh_callGenreListScreen(self):
		pass

	def mh_setMenu(self, levelIncr, menuInit=False):
		self.d_print("setMenu: ",levelIncr)
		self.mh_genreSelected = False
		if (self.mh_menuLevel+levelIncr) in range(self.mh_menuMaxLevel+1):
			if levelIncr < 0:
				self.mh_genreName[self.mh_menuLevel] = ""

			self.mh_menuLevel += levelIncr

			if levelIncr > 0 or menuInit:
				self.mh_menuIdx[self.mh_menuLevel] = 0

			if self.mh_menuLevel == 0:
				self.d_print("level-0")
				if self.mh_genreMenu[0]:
					self.mh_menuListe = []
					for (Name,Url) in self.mh_genreMenu[0]:
						self.mh_menuListe.append((Name,Url))
					self.ml.setList(map(self.mh_menuListentry, self.mh_menuListe))
					self['liste'].moveToIndex(self.mh_menuIdx[0])
				else:
					self.mh_genreName[self.mh_menuLevel] = ""
					self.mh_genreUrl[self.mh_menuLevel] = ""
					self.mh_genreUrl[1] = ""
					self.mh_genreUrl[2] = ""
					self.mh_genreUrl[3] = ""
					self.d_print("No menu entrys!")
			elif self.mh_menuLevel == 1:
				self.d_print("level-1")
				if self.mh_genreMenu[1][self.mh_menuIdx[0]]:
					self.mh_menuListe = []
					for (Name,Url) in self.mh_genreMenu[1][self.mh_menuIdx[0]]:
						self.mh_menuListe.append((Name,Url))
					self.ml.setList(map(self.mh_menuListentry, self.mh_menuListe))
					self['liste'].moveToIndex(self.mh_menuIdx[1])
				else:
					self.mh_genreName[self.mh_menuLevel] = ""
					self.mh_genreUrl[self.mh_menuLevel] = ""
					self.mh_genreUrl[2] = ""
					self.mh_genreUrl[3] = ""
					self.mh_menuLevel -= levelIncr
					self.mh_genreSelected = True
					self.d_print("No menu entrys!")
			elif self.mh_menuLevel == 2:
				self.d_print("level-2")
				if self.mh_genreMenu[2][self.mh_menuIdx[0]][self.mh_menuIdx[1]]:
					self.mh_menuListe = []
					for (Name,Url) in self.mh_genreMenu[2][self.mh_menuIdx[0]][self.mh_menuIdx[1]]:
						self.mh_menuListe.append((Name,Url))
					self.ml.setList(map(self.mh_menuListentry, self.mh_menuListe))
					self['liste'].moveToIndex(self.mh_menuIdx[2])
				else:
					self.mh_genreName[self.mh_menuLevel] = ""
					self.mh_genreUrl[self.mh_menuLevel] = ""
					self.mh_genreUrl[3] = ""
					self.mh_menuLevel -= levelIncr
					self.mh_genreSelected = True
					self.d_print("No menu entrys!")
			elif self.mh_menuLevel == 3:
				self.d_print("level-3")
				if self.mh_genreMenu[3][self.mh_menuIdx[0]][self.mh_menuIdx[1]][self.mh_menuIdx[2]]:
					self.mh_menuListe = []
					for (Name,Url) in self.mh_genreMenu[3][self.mh_menuIdx[0]][self.mh_menuIdx[1]][self.mh_menuIdx[2]]:
						self.mh_menuListe.append((Name,Url))
					self.ml.setList(map(self.mh_menuListentry, self.mh_menuListe))
					self['liste'].moveToIndex(self.mh_menuIdx[3])
				else:
					self.mh_genreName[self.mh_menuLevel] = ""
					self.mh_genreUrl[self.mh_menuLevel] = ""
					self.mh_menuLevel -= levelIncr
					self.mh_genreSelected = True
					self.d_print("No menu entrys!")
		else:
			self.d_print("Entry selected")
			self.mh_genreSelected = True

		self.d_print("menuLevel: ",self.mh_menuLevel)
		self.d_print("mainIdx: ",self.mh_menuIdx[0])
		self.d_print("subIdx_1: ",self.mh_menuIdx[1])
		self.d_print("subIdx_2: ",self.mh_menuIdx[2])
		self.d_print("subIdx_3: ",self.mh_menuIdx[3])
		self.d_print("genreSelected: ",self.mh_genreSelected)
		self.d_print("menuListe: ",self.mh_menuListe)
		self.d_print("genreUrl: ",self.mh_genreUrl)

		self.mh_setGenreStrTitle()

	def d_print(self,*args):
		global MDEBUG
		if MDEBUG:
			s = ''
			for arg in args:
				s += str(arg)
			printl(s)

	def mh_keyCancel(self):
		if self.mh_menuLevel == 0:
			self.close()
		else:
			self.mh_keyMenuUp()