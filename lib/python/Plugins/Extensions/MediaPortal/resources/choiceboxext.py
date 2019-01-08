# -*- coding: utf-8 -*-
from imports import *
import mp_globals
from Screens.Screen import Screen
from Components.ActionMap import NumberActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from enigma import RT_HALIGN_LEFT, RT_VALIGN_CENTER, eListboxPythonMultiContent, gFont

pwidth = 0

class ChoiceListExt(MenuList):
	def __init__(self, list, selection = 0, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.selection = selection

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.moveToIndex(self.selection)

class ChoiceBoxExt(Screen):
	IS_DIALOG = True

	def ChoiceEntryComponent(self, data):
		width = self['list'].instance.size().width()
		height = self['list'].l.getItemSize().height()
		self.ml.l.setFont(0, gFont(mp_globals.font, height - 4 * mp_globals.sizefactor))

		res = [data[1]]

		skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		key = "key_" + data[0] + ".png"
		path = "%s/%s/images/%s" % (skin_path, mp_globals.currentskin, key)
		if not fileExists(path):
			path = "%s/%s/images/%s" % (skin_path, mp_globals.skinFallback, key)
			if not fileExists(path):
				path = resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/buttons/" + key)

		png = LoadPixmap(path)
		if png is not None:
			global pwidth
			pwidth = png.size().width()
			pheight = png.size().height()
			vpos = round(float((height-pheight)/2))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 5, vpos, pwidth, pheight, png))
		if data[1][0] == "--":
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 1000, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "-"*200))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, pwidth+15, 0, 1000, height, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, data[1][0]))
		return res

	def __init__(self, session, title = "", list = [], keys = None, selection = 0, titlebartext = None, allow_cancel = True):
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath
		path = "%s/%s/MP_ChoiceBox.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/MP_ChoiceBox.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		Screen.__init__(self, session)

		self.allow_cancel = allow_cancel

		self["text"] = Label(title)
		self["title"] = Label()
		self["bgup"] = Label()
		self["bgdown"] = Label()
		self.list = []
		self.summarylist = []

		if keys is None:
			self.__keys = [ "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "red", "green", "yellow", "blue", "text" ] + (len(list) - 10) * [""]
		else:
			self.__keys = keys + (len(list) - len(keys)) * [""]

		self.keymap = {}
		pos = 0
		for x in list:
			strpos = str(self.__keys[pos])
			# don't show empty entries (filters for mainscreen)
			if x[0] != "":
				self.list.append((strpos, x))
			if self.__keys[pos] != "":
				self.keymap[self.__keys[pos]] = list[pos]
			self.summarylist.append((self.__keys[pos],x[0]))
			pos += 1
		self.ml = ChoiceListExt([], selection = selection)
		self["list"] = self.ml

		self["summary_list"] = StaticText()
		self.updateSummary()

		self["actions"] = NumberActionMap(["WizardActions", "InputActions", "ColorActions", "DirectionActions"],
		{
			"ok": self.go,
			"back": self.cancel,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal,
			"red": self.keyRed,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
			"text": self.keyText,
			"up": self.up,
			"down": self.down
		}, -1)

		self.titlebartext = titlebartext
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.ml.setList(map(self.ChoiceEntryComponent, self.list))
		if self.titlebartext:
			self.setTitle(self.titlebartext)
			self["title"].setText(self.titlebartext)
		else:
			self["title"].setText(_("Input"))

	def keyLeft(self):
		pass

	def keyRight(self):
		pass

	def up(self):
		if len(self["list"].list) > 0:
			while 1:
				self["list"].instance.moveSelection(self["list"].instance.moveUp)
				self.updateSummary(self["list"].l.getCurrentSelectionIndex())
				if self["list"].l.getCurrentSelection()[0][0] != "--" or self["list"].l.getCurrentSelectionIndex() == 0:
					break

	def down(self):
		if len(self["list"].list) > 0:
			while 1:
				self["list"].instance.moveSelection(self["list"].instance.moveDown)
				self.updateSummary(self["list"].l.getCurrentSelectionIndex())
				if self["list"].l.getCurrentSelection()[0][0] != "--" or self["list"].l.getCurrentSelectionIndex() == len(self["list"].list) - 1:
					break

	def keyNumberGlobal(self, number):
		self.goKey(str(number))

	def go(self):
		cursel = self["list"].l.getCurrentSelection()
		if cursel:
			self.goEntry(cursel[0])
		else:
			self.cancel()

	def goEntry(self, entry):
		if len(entry) > 2 and isinstance(entry[1], str) and entry[1] == "CALLFUNC":
			arg = self["list"].l.getCurrentSelection()[0]
			entry[2](arg)
		else:
			self.close(entry)

	def goKey(self, key):
		if self.keymap.has_key(key):
			entry = self.keymap[key]
			self.goEntry(entry)

	def keyRed(self):
		self.goKey("red")

	def keyGreen(self):
		self.goKey("green")

	def keyYellow(self):
		self.goKey("yellow")

	def keyBlue(self):
		self.goKey("blue")

	def keyText(self):
		self.goKey("text")

	def updateSummary(self, curpos=0):
		pos = 0
		summarytext = ""
		for entry in self.summarylist:
			if pos > curpos-2 and pos < curpos+5:
				if pos == curpos:
					summarytext += ">"
				else:
					summarytext += entry[0]
				summarytext += ' ' + entry[1] + '\n'
			pos += 1
		self["summary_list"].setText(summarytext)

	def cancel(self):
		if self.allow_cancel:
			self.close(None)