# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def streamango(self, data):
	get_packedjava = re.findall("mango.js.*?(eval.function.*?\{\}\)\))", data, re.S)
	if get_packedjava and detect(get_packedjava[0]):
		sJavascript = get_packedjava[0]
		sUnpacked = unpack(sJavascript)
		if sUnpacked:
			url = None
			js = sUnpacked.decode('string_escape').replace('window.d=function','d=function')
			dec = re.findall('video\/mp4\",src:(.*?\)),', data, re.S)
			js = js + ';\nvidurl = ' + dec[0] + ';\nreturn vidurl;'
			try:
				import execjs
				node = execjs.get("Node")
				url = str(node.exec_(js))
			except:
				self.session.open(MessageBoxExt, _("This plugin requires packages python-pyexecjs and nodejs."), MessageBoxExt.TYPE_INFO)
			if url:
				if url.startswith('//'):
					url = 'https:' + url
				self._callback(url)
			else:
				self.stream_not_found()
		else:
			self.stream_not_found()
	else:
		self.stream_not_found()