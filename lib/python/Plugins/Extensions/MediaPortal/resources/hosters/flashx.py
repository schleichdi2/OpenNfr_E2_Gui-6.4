# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
from Plugins.Extensions.MediaPortal.resources.packer import unpack, detect
import requests

def flashx(self, url):
	if url:
		self.callPremium(url.replace('flashx.co','flashx.tv').replace('.html','.jsp'))
	else:
		self.stream_not_found()