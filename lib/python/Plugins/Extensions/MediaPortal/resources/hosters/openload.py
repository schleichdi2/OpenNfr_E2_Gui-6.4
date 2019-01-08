# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt
import requests

try:
	from youtube_dl import YoutubeDL
	youtubedl = True
except:
	youtubedl = False

if os.path.exists("/usr/bin/phantomjs"):
	phantomjs = True
else:
	phantomjs = False

def openload(self, data, link, count=0):

	stream_url = re.findall('"url":"(.*?)"', data)
	if stream_url:
		self._callback(stream_url[0].replace('\\',''))
	elif youtubedl and phantomjs:
		result = None
		try:
			os.environ["QT_QPA_PLATFORM"] = "phantom"
			ytdl = YoutubeDL({'nocheckcertificate':True, 'restrictfilenames':True, 'no_warnings':True})
			result = ytdl.extract_info(link, ie_key="Openload", download=False, process=True)
			os.environ["QT_QPA_PLATFORM"] = ""
		except Exception as e:
			os.environ["QT_QPA_PLATFORM"] = ""
			if re.search('File not found', str(e), re.S):
				self.stream_not_found()
			else:
				printl("[openload]: %s" % e,'',"E")
				if count < 3:
					printl("[openload]: retry",'',"E")
					count += 1
					self.openload("", link, count)
				else:
					self.session.open(MessageBoxExt, _("youtube-dl: unable to extract URL. This error occasionally occurs, please try again.\nIf this error persists a youtube-dl upgrade may be needed.\n\nAlternatively you may visit https://olpair.com to pair your IP."), MessageBoxExt.TYPE_INFO, timeout=5)
		else:
			if result:
				self._callback(str(result['url']).replace('https','http'))
			else:
				self.stream_not_found()
	elif re.search('IP address not authorized', data):
		message = self.session.open(MessageBoxExt, _("IP address not authorized. Visit https://olpair.com to pair your IP.\n\nAlternatively you may install youtube-dl and phantomjs to extend resolver functionality."), MessageBoxExt.TYPE_ERROR)
	else:
		self.stream_not_found()

