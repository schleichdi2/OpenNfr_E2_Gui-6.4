# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect

def vidzi(self, data):
		get_packedjava = re.findall("<script type=.text.javascript.>(eval.function.*?)</script>", data, re.S)
		if get_packedjava and detect(get_packedjava[0]):
			sJavascript = get_packedjava[0].replace('eval (function','eval(function')
			sUnpacked = unpack(sJavascript)
			if sUnpacked:
				stream_url = re.search('file:\s*[\'|"](http[^,\s\"]+.mp4)[\'|"]', sUnpacked.replace('\\',''), re.S)
				if not stream_url:
					stream_url = re.search('file:\s*"(.*?)"', sUnpacked.replace('\\',''), re.S)
				if stream_url:
					self._callback(stream_url.group(1))
					return
				else:
					self.stream_not_found()
			else:
				self.stream_not_found()
		else:
			stream_url = re.search('file:\s*"(.*?)"', data, re.S)
			if stream_url:
				self._callback(stream_url.group(1))
			else:
				self.stream_not_found()