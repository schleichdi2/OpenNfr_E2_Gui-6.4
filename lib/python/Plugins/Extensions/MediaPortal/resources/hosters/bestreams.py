# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def bestreams(self, data, link, ck):
		c1 = re.search('cookie\(\'file_id\', \'(.*?)\'', data)
		c2 = re.search('cookie\(\'aff\', \'(.*?)\'', data)
		p1 = re.search('type="hidden" name="op" value="(.*?)"', data)
		p3 = re.search('type="hidden" name="id" value="(.*?)"', data)
		p4 = re.search('type="hidden" name="fname" value="(.*?)"', data)
		p6 = re.search('type="hidden" name="hash" value="(.*?)"', data)
		if c1 and c2 and p1 and p3 and p4 and p6:
			ck.update({'file_id':c1.group(1)})
			ck.update({'aff':c2.group(1)})
			ck.update({'ref_url':'/%s' % p3.group(1)})
			info = urlencode({'op': p1.group(1),
							'usr_login': '',
							'id': p3.group(1),
							'fname': p4.group(1),
							'referer':  link,
							'hash': p6.group(1),
							'imhuman': 'Proceed+to+video'})
			reactor.callLater(1, self.bestreamsCalllater, link, method='POST', cookies=ck, postdata=info, headers={'Content-Type': 'application/x-www-form-urlencoded'})
		else:
			self.stream_not_found()

def bestreamsCalllater(self, *args, **kwargs):
	print "drin"
	getPage(*args, **kwargs).addCallback(self.bestreamsPostData).addErrback(self.errorload)

def bestreamsPostData(self, data):
	stream_url = None
	stream_url = re.findall('file: "(.*?)"', data, re.S)
	if stream_url:
		url = urllib.unquote(stream_url[-1])
		self._callback(url)
	else:
		self.stream_not_found()