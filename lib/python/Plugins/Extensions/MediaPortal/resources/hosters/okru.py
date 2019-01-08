# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def okru(self, data):
	json_data = json.loads(data)
	streams = []
	if 'videos' in json_data.keys():
		for entry in json_data['videos']:
			streams.append(str(entry['url']))
	else:
		self.stream_not_found()

	if len(streams) > 0:
		self._callback(streams[-1])
	else:
		self.stream_not_found()