# -*- coding: utf-8 -*-
from Components.Converter.Converter import Converter
from Poll import Poll
from enigma import iServiceInformation, iPlayableService, iPlayableServicePtr
from Components.Element import cached
from os import path as os_path
try:
	from Plugins.Extensions.MediaPortal.resources.sepg.mp_epg import SimpleEPG, mpepg
	MP_EPG = True
except:
	MP_EPG = False
print "[MPServiceName] MP_EPG:",MP_EPG
MOVIE_EXTS = frozenset((".ts", ".avi", ".divx", ".mpg", ".mpeg", ".mkv", ".mp4", ".mov", ".iso"))

class MPServiceName(Poll, Converter, object):
	NAME = 0

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.type = self.NAME
		self.poll_interval = 30*1000
		self.poll_enabled = True

	def getServiceInfoValue(self, info, what, ref=None):
		v = ref and info.getInfo(ref, what) or info.getInfo(what)
		if v != iServiceInformation.resIsString:
			return "N/A"
		return ref and info.getInfoString(ref, what) or info.getInfoString(what)

	@cached
	def getText(self):
		service = self.source.service
		if isinstance(service, iPlayableServicePtr):
			info = service and service.info()
			ref = None
		else: # reference
			info = service and self.source.info
			ref = service
		if info is None:
			return ""
		if self.type == self.NAME:
			name = ref and info.getName(ref)
			if name is None:
				name = info.getName()
			sname, ext = os_path.splitext(name)
			if ext in MOVIE_EXTS:
				name = sname.replace("_", " ")
			serv_ref = self.getServiceInfoValue(info, iServiceInformation.sServiceref, ref)
			if serv_ref and serv_ref.startswith('4097'):
				if MP_EPG and mpepg.has_epg:
					ss = serv_ref.split(':', 5)
					if ss[4] == '1955':
						epg_id = ss[3].lower()
						result = mpepg.getEvent(epg_id)
						if result:
							name += ' - %s' % result[1][2]
			return name.replace('\xc2\x86', '').replace('\xc2\x87', '')

	text = property(getText)

	def changed(self, what):
		if what[0] == self.CHANGED_POLL or what[0] != self.CHANGED_SPECIFIC or what[1] in (iPlayableService.evStart,):
			Converter.changed(self, what)
