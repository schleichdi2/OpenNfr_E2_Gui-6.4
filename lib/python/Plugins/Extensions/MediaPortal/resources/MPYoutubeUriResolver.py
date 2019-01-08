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
	from yt_url import youtubeUrl
	from tw_util import getPage
	import re

	from Tools.Log import Log

	class MPYoutubeUriResolver(eUriResolver):

		_schemas = ("mp_youtube", "mp_yt")
		instance = None

		def __init__(self):
			eUriResolver.__init__(self, StringList(self._schemas))
			Log.i(self._schemas)

		def resolve(self, service, uri):
			Log.i(uri)
			liveurl = None
			try:
				uri = uri.split("://")[1]
				uri = uri.split("/")
				if uri[0] == "live":
					liveurl = "https://youtube.com/user/%s/live" % uri[1]
					video_id = None
				else:
					video_id = uri[0]
			except:
				pass
			def onUrlReady(uri):
				try:
					if not service.ptrValid():
						Log.w("Service became invalid!")
						return
					if uri:
						if ".m3u8" in uri:
							if "hls_variant" in uri:
								getPage(uri).addCallback(self.parseData, service)
							else:
								uri = uri.replace('%252F','%2F').replace('%253D','%3D').replace('%252B','%2B').replace('%253B','%3B')
								service.setResolvedUri(uri, eServiceReference.idDVB)
						else:
							service.setResolvedUri(uri, eServiceReference.idGST)
					else:
						service.failedToResolveUri()
				except:
					service.failedToResolveUri()

			if video_id:
				y = youtubeUrl(self)
				y.addCallback(onUrlReady)
				y.getVideoUrl(video_id, 2, dash=None, fmt_map=None)
			elif liveurl:
				getPage(liveurl).addCallback(self.parseLive, service)
			else:
				service.failedToResolveUri()

			return True

		def parseLive(self, data, service):
			data = data.replace('\/','/')
			urls = re.findall('hlsvp":"(http.*?\.m3u8)","', data, re.S)
			if urls:
				uri = urls[-1]
				try:
					if not service.ptrValid():
						Log.w("Service became invalid!")
						return
					if uri:
						if "hls_variant" in uri:
							getPage(uri).addCallback(self.parseData, service)
						else:
							uri = uri.replace('%252F','%2F').replace('%253D','%3D').replace('%252B','%2B').replace('%253B','%3B')
							service.setResolvedUri(uri, eServiceReference.idDVB)
					else:
						service.failedToResolveUri()
				except:
					service.failedToResolveUri()
			else:
				service.failedToResolveUri()

		def parseData(self, data, service):
			urls = re.findall('(https://.*?itag\/(\d+)\/.*?)\n', data, re.S)
			if urls:
				uri = urls[-1][0]
				try:
					if not service.ptrValid():
						Log.w("Service became invalid!")
						return
					if uri:
						uri = uri.replace('%252F','%2F').replace('%253D','%3D').replace('%252B','%2B').replace('%253B','%3B')
						service.setResolvedUri(uri, eServiceReference.idDVB)
					else:
						service.failedToResolveUri()
				except:
					service.failedToResolveUri()
			else:
				service.failedToResolveUri()

except ImportError:
	pass