# -*- coding: utf-8 -*-
from update import *

config.mpgz = ConfigSubsection()
config.mpgz.version = NoSave(ConfigText(default="2019010401"))

def autostart(reason, session=None, **kwargs):
	if reason == 0:
		if session is not None:
			_session = session
			addFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal1.ttf", "mediaportal", 100, False)
			addFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal_clean.ttf", "mediaportal_clean", 100, False)
			if config_mp.mediaportal.autoupdate.value:
				config.misc.standbyCounter.addNotifier(checkupdate(session).standbyCounterChanged, initial_call = False)
				checkupdate(session).checkforupdate()

def Plugins(path, **kwargs):
	result = [
		PluginDescriptor(name="mpgz", description="mpgz - Updater", where = [PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart, wakeupfnc = None)
	]
	return result
