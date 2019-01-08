# -*- coding: utf-8 -*-
##############################################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2018
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

from Components.config import ConfigSubsection, config, configfile, ConfigText
from Tools.Directories import resolveFilename, fileExists, SCOPE_CONFIG

class Config(ConfigSubsection):
	def __init__(self):
		ConfigSubsection.__init__(self)

	def pickle_this(self, prefix, topickle, result):
		for (key, val) in topickle.items():
			name = '.'.join((prefix, key))
			try:
				x = eval(name)
				if isinstance(val, dict):
					self.pickle_this(name, val, result)
				elif isinstance(val, tuple):
					result += [name, '=', val[0], '\n']
				else:
					result += [name, '=', val, '\n']
			except:
				pass

	def pickle(self):
		result = []
		self.pickle_this("config_mp", self.saved_value, result)
		return ''.join(result)

	def unpickle(self, lines, base_file=True, append = False):
		tree = { }
		for l in lines:
			if not l or l[0] == '#':
				continue
			n = l.find('=')
			name = l[:n]
			val = l[n+1:].strip()
			names = name.split('.')
			base = tree
			for n in names[:-1]:
				base = base.setdefault(n, {})
			base[names[-1]] = val
			if not base_file:
				try:
					configEntry = eval(name)
					if configEntry is not None:
						configEntry.value = val
				except (SyntaxError, KeyError):
					pass
		if "config_mp" in tree:
			try:
				self.setSavedValue(tree["config_mp"], append)
			except:
				self.setSavedValue(tree["config_mp"])

	def saveToFile(self, filename):
		try:
			from Tools.IO import saveFile
			saveFile(filename, self.pickle())
		except:
			text = self.pickle()
			f = open(filename, "w")
			f.write(text)
			f.close()

	def loadFromFile(self, filename, base_file=False, append = False, import_mp=False):
		CONFIG_FILE_OLD = resolveFilename(SCOPE_CONFIG, "settings")
		CONFIG_FILE = resolveFilename(SCOPE_CONFIG, "mp_config")

		f = open(filename, "r")
		lines_read = f.readlines()
		lines = []

		f_old = open(CONFIG_FILE_OLD, "r")
		lines_read_old = f_old.readlines()

		if fileExists(CONFIG_FILE):
			config.mediaportal = ConfigSubsection()
			config.mediaportal.retries = ConfigSubsection()
			config.mediaportal.retries.pincode = ConfigSubsection()
			config.mediaportal.retries.adultpin = ConfigSubsection()
			for l in lines_read_old:
				if "config.mediaportal" in l:
					exec(l.split('=')[0] + ' = ConfigText(default = "foobar")')
					try:
						exec(l.split('=')[0] + '.save_forced = False')
					except:
						pass
					exec(l.split('=')[0] + '.value = "foobar"')
					exec(l.split('=')[0] + '.save()')
			configfile.save()

		if import_mp and not fileExists(CONFIG_FILE):
			fn = open(CONFIG_FILE, "w")

		for l in lines_read:
			if import_mp and "config.mediaportal" in l:
				fn.write(l.replace("config","config_mp"))
			tmp = l.split('=')
			x = tmp[0].split('.')
			if x[1] == 'mediaportal':
				lines.append(l)
		self.unpickle(lines, base_file, append)

		if import_mp:
			fn.close()

		f.close()
		f_old.close()

config_mp = Config()

class ConfigFile:
	CONFIG_FILE_OLD = resolveFilename(SCOPE_CONFIG, "settings")
	CONFIG_FILE = resolveFilename(SCOPE_CONFIG, "mp_config")

	def load(self):
		try:
			if not fileExists(self.CONFIG_FILE):
				config_mp.loadFromFile(self.CONFIG_FILE_OLD, True, import_mp=True)
			config_mp.loadFromFile(self.CONFIG_FILE, True)
		except IOError, e:
			print "unable to load config (%s), assuming defaults..." % str(e)

	def save(self):
		config_mp.saveToFile(self.CONFIG_FILE)

	def __resolveValue(self, pickles, cmap):
		key = pickles[0]
		if cmap.has_key(key):
			if len(pickles) > 1:
				return self.__resolveValue(pickles[1:], cmap[key].dict())
			else:
				return str(cmap[key].value)
		return None

	def getResolvedKey(self, key):
		names = key.split('.')
		if len(names) > 1:
			if names[0] == "config_mp":
				ret=self.__resolveValue(names[1:], config_mp.content.items)
				if ret and len(ret):
					return ret
		return None

configfile_mp = ConfigFile()
configfile_mp.load()