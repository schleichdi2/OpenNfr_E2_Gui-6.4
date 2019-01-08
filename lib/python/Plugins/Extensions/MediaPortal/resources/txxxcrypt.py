# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

class txxxcrypt:

	def getVideoPage(self, data):
		try:
			import execjs
			node = execjs.get("Node")
		except:
			printl('nodejs not found',self,'E')
			self.session.open(MessageBoxExt, _("This plugin requires packages python-pyexecjs and nodejs."), MessageBoxExt.TYPE_INFO)
			return
		decoder = "decrypt=function(_0xf4bdx6) {"\
			"var _0xf4bdx7 = '',"\
			"    _0xf4bdx8 = 0;"\
			"/[^\u0410\u0412\u0421\u0415\u041cA-Za-z0-9\.\,\~]/g ['exec'](_0xf4bdx6) && console['log']('error decoding url');"\
			"_0xf4bdx6 = _0xf4bdx6['replace'](/[^\u0410\u0412\u0421\u0415\u041cA-Za-z0-9\.\,\~]/g, '');"\
			"do {"\
			"var _0xf4bdx9 = '\u0410\u0412\u0421D\u0415FGHIJKL\u041CNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~' ['indexOf'](_0xf4bdx6['charAt'](_0xf4bdx8++)),"\
			"_0xf4bdxa = '\u0410\u0412\u0421D\u0415FGHIJKL\u041CNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~' ['indexOf'](_0xf4bdx6['charAt'](_0xf4bdx8++)),"\
			"_0xf4bdxb = '\u0410\u0412\u0421D\u0415FGHIJKL\u041CNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~' ['indexOf'](_0xf4bdx6['charAt'](_0xf4bdx8++)),"\
			"_0xf4bdxc = '\u0410\u0412\u0421D\u0415FGHIJKL\u041CNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~' ['indexOf'](_0xf4bdx6['charAt'](_0xf4bdx8++)),"\
			"_0xf4bdx9 = _0xf4bdx9 << 2 | _0xf4bdxa >> 4,"\
			"_0xf4bdxa = (_0xf4bdxa & 15) << 4 | _0xf4bdxb >> 2,"\
			"_0xf4bdxd = (_0xf4bdxb & 3) << 6 | _0xf4bdxc,"\
			"_0xf4bdx7 = _0xf4bdx7 + String['fromCharCode'](_0xf4bdx9);"\
			"64 != _0xf4bdxb && (_0xf4bdx7 += String['fromCharCode'](_0xf4bdxa));"\
			"64 != _0xf4bdxc && (_0xf4bdx7 += String['fromCharCode'](_0xf4bdxd))"\
			"} while (_0xf4bdx8 < _0xf4bdx6['length']);;"\
			"return unescape(_0xf4bdx7)"\
			"};"
		video_url = re.findall('var video_url\s{0,1}={0,1}(.*?);', data, re.S)
		hash = re.findall('video_url\s{0,1}\+\=\s{0,1}(?:\"|\')\|\|/get_file/(\d+/[a-f0-9]+)/', data, re.S)
		hash2 = re.findall('video_url\s{0,1}\+\=\s{0,1}(?:\"|\')\|\|/get_file/(\d+/[a-f0-9]+)/\|\|(.*?)\|\|(.*?)(?:\"|\');', data, re.S)
		js = decoder + "\n" + 'video_url=decrypt('+video_url[0]+');' + "return video_url;"
		url = str(node.exec_(js))
		if hash:
			mainurl = url.split('get_file/')[0]
			tokenurl = url.split('get_file/')[1]
			tokenurl = tokenurl.replace(tokenurl.split('/')[0]+'/'+tokenurl.split('/')[1],hash[0])
			url = mainurl + "get_file/" + tokenurl
		if hash2:
			url = url + '&lip=' + hash2[0][1] +'&lt=' + hash2[0][2]
		url = url.replace('https','http')
		self.playVideo(url)