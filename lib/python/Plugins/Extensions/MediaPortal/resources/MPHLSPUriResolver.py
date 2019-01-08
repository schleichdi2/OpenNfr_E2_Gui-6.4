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

try:
	from enigma import eServiceReference, eUriResolver, StringList
	from simpleplayer import M3U8Player
	from imports import *
	import mp_globals

	from Tools.Log import Log

	class MPHLSPUriResolver(eUriResolver, M3U8Player):

		_schemas = ("mp_hlsproxy", "mp_hlsp")
		instance = None

		def __init__(self):
			eUriResolver.__init__(self, StringList(self._schemas))
			M3U8Player.__init__(self)
			Log.i(self._schemas)

		def _getBandwidth(self):
			videoPrio = int(config_mp.mediaportal.videoquali_others.value)
			if videoPrio == 2:
				bw = 4000000
			elif videoPrio == 1:
				bw = 1000000
			else:
				bw = 250000
			return bw

		def resolve(self, service, uri):
			Log.i(uri)
			uri = uri.replace('mp_hlsproxy://','').replace('mp_hlsp://','')
			def onUrlReady(uri):
				try:
					if not service.ptrValid():
						Log.w("Service became invalid!")
						return
					if uri:
						self._bitrate = self._getBandwidth()
						path = config_mp.mediaportal.storagepath.value
						ip = "127.0.0.1" #".".join(str(x) for x in config_mp.mediaportal.hls_proxy_ip.value)
						import uuid
						uid = uuid.uuid1()
						uri = 'http://%s:%d/?url=%s&bitrate=%d&path=%s&uid=%s' % (ip, mp_globals.hls_proxy_port, uri, self._bitrate, path, uid)
						service.setResolvedUri(uri, eServiceReference.idGST)
					else:
						service.failedToResolveUri()
				except:
					service.failedToResolveUri()

			onUrlReady(uri)

			return True

except ImportError:
	pass