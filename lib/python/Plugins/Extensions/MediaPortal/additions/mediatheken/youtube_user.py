# -*- coding: utf-8 -*-
from os.path import exists
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.additions.mediatheken.youtube import YT_ListScreen
default_cover = "file://%s/youtube.png" % (config_mp.mediaportal.iconcachepath.value + "logos")

class show_USER_Genre(MPScreen):

	def __init__(self, session):

		MPScreen.__init__(self, session, skin='MP_Plugin', default_cover=default_cover)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"	: self.closeAll,
			"ok"    : self.keyOK,
			"cancel": self.keyCancel,
			"green"	: self.keyGreen
		}, -1)

		self['title'] = Label("YouTube")
		self['ContentTitle'] = Label(_("User Channels"))
		self['name'] = Label(_("Selection:"))
		self['F2'] = Label(_("Load"))

		self.user_path = config_mp.mediaportal.watchlistpath.value + "mp_userchan.xml"
		self.show_help = config_mp.mediaportal.show_userchan_help.value
		self.keyLocked = True
		self.genreliste = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		if not exists(self.user_path):
			self.getUserFile(fInit=True)

		if self.show_help:
			self.genreliste.append((_("With this extension you can add your favorite YouTube channels themselves."), ""))
			self.genreliste.append(("", ""))
			self.genreliste.append((_("For each channel, only two entries are added:"), ""))
			self.genreliste.append((_("'<name> channel name </name>' and '<user> owner name </user>'"), ""))
			self.genreliste.append(("", ""))
			self.genreliste.append((_("With the 'Green' button the user file:"), ""))
			self.genreliste.append((_("'%s' is loaded.") % self.user_path, ""))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		else:
			self.getUserFile()

	def getUserFile(self, fInit=False):
		fname = mp_globals.pluginPath + "/resources/mp_userchan.xml"
		try:
			if fInit:
				shutil.copyfile(fname, self.user_path)
				return
			fp = open(self.user_path)
			data = fp.read()
			fp.close()
		except IOError, e:
			self.genreliste = []
			self.genreliste.append((str(e), ""))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))
		else:
			list = re.findall('<name>(.*?)</name>.*?<user>(.*?)</user>', data, re.S)
			self.genreliste = []
			if list:
				for (name, user) in list:
					self.genreliste.append((name.strip(), '/'+user.strip()))
				self.keyLocked = False
			else:
				self.genreliste.append((_("No channels found!"), ""))
			self.ml.setList(map(self._defaultlistcenter, self.genreliste))

	def keyGreen(self):
		self.getUserFile()

	def keyOK(self):
		if self.keyLocked:
			return

		genre = self['liste'].getCurrent()[0][0]
		stvLink = self['liste'].getCurrent()[0][1]
		if stvLink == '/':
			return
		url = "gdata.youtube.com/feeds/api/users"+stvLink+"/uploads?"
		self.session.open(YT_ListScreen, url, genre, title="YouTube")