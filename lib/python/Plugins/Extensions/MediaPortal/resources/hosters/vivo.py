# -*- coding: utf-8 -*-
import base64
import re
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def vivo(self, data, url):
	crypt = re.findall('data-stream="(.*?)">', data)
	if crypt:
		stream_url = base64.b64decode(crypt[0])
		self._callback(stream_url)
	else:
		self.stream_not_found()