# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def flyflv(self, data):
	parse = re.search('config: "(.*?)"', data, re.I)
	if parse:
		urlparts = re.findall("http://www.flyflv.com(.*?)\?e=(\d+)&ip=(.*?)$", parse.group(1))
		if urlparts:
			urlcodepart= "%s%s%s%s" % ("Gte7#@s#3F1",urlparts[0][0],urlparts[0][1],urlparts[0][2])
			cryptpart = sl_encrypt(urlcodepart).replace("+","-").replace("/","_").replace("=","")
			hdurl = "%s&st=%s" %(parse.group(1),cryptpart)
			getPage(hdurl).addCallback(self.flyflvData).addErrback(self.errorload)
	else:
		stream_url = re.findall('file:\s"(.*?)"', data)
		if stream_url:
			print stream_url
			self._callback(stream_url[0])
		else:
			parse = re.search('var configUrl="(.*?)"', data, re.I)
			if parse:
				getPage(parse.group(1)).addCallback(self.flyflvData).addErrback(self.errorload)
			else:
				self.stream_not_found()

def flyflvData(self, data):
	parse = re.search('<hd.file>(.*?)</hd.file>', data, re.I)
	if parse:
		self._callback(parse.group(1))
	else:
		parse = re.search('<file>(.*?)</file>', data, re.I)
		if parse:
			self._callback(parse.group(1))
		else:
			self.stream_not_found()

def sl_encrypt(arg1):
	return rstr2b64(binl2rstr(core_md5(rstr2binl(arg1), len(arg1) * 8)))

def binl2rstr(arg1):
	_local2 = ""
	_local3 = 0
	while (_local3 < (len(arg1) * 32)):
		_local2 = _local2 + chr(((arg1[(_local3 >> 5)] >> (_local3 % 32)) & 0xFF))
		_local3 = (_local3 + 8)
	return (_local2);

def extend_array_to_length(array, length, default=None):
	if len(array) >= length:
		return list(array)
	return list(array) + [default] * (length - len(array))

def swrap(num):
	num = num & 0xFFFFFFFF
	if num > 0x7FFFFFFF:
		return int(num - 0x100000000)
	else:
		return int(num)

def ushr(num, bits):
	if num < 0:
		num += 0x100000000
	return int(num >> bits)

def md5_cmn(q, a, b, x, s, t):
	return safe_add(bit_rol(safe_add(safe_add(a, q), safe_add(x, t)), s), b)

def md5_ff(a, b, c, d, x, s, t):
	return md5_cmn((b&c) | ((~b) & d), a, b, x, s, t)

def md5_gg(a,b,c,d,x,s,t):
	return md5_cmn((b&d) | (c & (~d)), a, b, x, s, t)

def md5_hh(a,b,c,d,x,s,t):
	return md5_cmn(b^c^d, a, b, x, s, t)

def md5_ii(a,b,c,d,x,s,t):
	return md5_cmn(c ^ (b | (~d)), a, b, x, s, t)

def safe_add(x,y):
	lsw = (x & 0xFFFF) + (y & 0xFFFF)
	msw = (x >> 16) + (y >> 16) + (lsw >> 16)
	return swrap(msw << 16) | (lsw & 0xFFFF)

def bit_rol(num,cnt):
	return swrap(num << cnt) | ushr(num, 32-cnt)

def core_md5(x, length):
	max_access_x = max(length>>5 + 1, (((length+64)>>9)<<4) + 15)
	x = extend_array_to_length(x, max_access_x+1, 0)
	x[length>>5] |= swrap(0x80 << ((length)%32))
	x[(((length+64)>>9)<<4)+14] = length
	a = 1732584193
	b = -271733879
	c = -1732584194
	d = 271733878
	for i in range(0, len(x), 16):
		olda = a
		oldb = b
		oldc = c
		oldd = d
		a=md5_ff(a,b,c,d,x[i+0],7,-680876936); d=md5_ff(d,a,b,c,x[i+1],12,-389564586); c=md5_ff(c,d,a,b,x[i+2],17,606105819); b=md5_ff(b,c,d,a,x[i+3],22,-1044525330);
		a=md5_ff(a,b,c,d,x[i+4],7,-176418897); d=md5_ff(d,a,b,c,x[i+5],12,1200080426); c=md5_ff(c,d,a,b,x[i+6],17,-1473231341); b=md5_ff(b,c,d,a,x[i+7],22,-45705983);
		a=md5_ff(a,b,c,d,x[i+8],7,1770035416); d=md5_ff(d,a,b,c,x[i+9],12,-1958414417); c=md5_ff(c,d,a,b,x[i+10],17,-42063); b=md5_ff(b,c,d,a,x[i+11],22,-1990404162);
		a=md5_ff(a,b,c,d,x[i+12],7,1804603682); d=md5_ff(d,a,b,c,x[i+13],12,-40341101); c=md5_ff(c,d,a,b,x[i+14],17,-1502002290); b=md5_ff(b,c,d,a,x[i+15],22,1236535329);
		a=md5_gg(a,b,c,d,x[i+1],5,-165796510); d=md5_gg(d,a,b,c,x[i+6],9,-1069501632); c=md5_gg(c,d,a,b,x[i+11],14,643717713); b=md5_gg(b,c,d,a,x[i+0],20,-373897302);
		a=md5_gg(a,b,c,d,x[i+5],5,-701558691); d=md5_gg(d,a,b,c,x[i+10],9,38016083); c=md5_gg(c,d,a,b,x[i+15],14,-660478335); b=md5_gg(b,c,d,a,x[i+4],20,-405537848);
		a=md5_gg(a,b,c,d,x[i+9],5,568446438); d=md5_gg(d,a,b,c,x[i+14],9,-1019803690); c=md5_gg(c,d,a,b,x[i+3],14,-187363961); b=md5_gg(b,c,d,a,x[i+8],20,1163531501);
		a=md5_gg(a,b,c,d,x[i+13],5,-1444681467); d=md5_gg(d,a,b,c,x[i+2],9,-51403784); c=md5_gg(c,d,a,b,x[i+7],14,1735328473); b=md5_gg(b,c,d,a,x[i+12],20,-1926607734);
		a=md5_hh(a,b,c,d,x[i+5],4,-378558); d=md5_hh(d,a,b,c,x[i+8],11,-2022574463); c=md5_hh(c,d,a,b,x[i+11],16,1839030562); b=md5_hh(b,c,d,a,x[i+14],23,-35309556);
		a=md5_hh(a,b,c,d,x[i+1],4,-1530992060); d=md5_hh(d,a,b,c,x[i+4],11,1272893353); c=md5_hh(c,d,a,b,x[i+7],16,-155497632); b=md5_hh(b,c,d,a,x[i+10],23,-1094730640);
		a=md5_hh(a,b,c,d,x[i+13],4,681279174); d=md5_hh(d,a,b,c,x[i+0],11,-358537222); c=md5_hh(c,d,a,b,x[i+3],16,-722521979); b=md5_hh(b,c,d,a,x[i+6],23,76029189);
		a=md5_hh(a,b,c,d,x[i+9],4,-640364487); d=md5_hh(d,a,b,c,x[i+12],11,-421815835); c=md5_hh(c,d,a,b,x[i+15],16,530742520); b=md5_hh(b,c,d,a,x[i+2],23,-995338651);
		a=md5_ii(a,b,c,d,x[i+0],6,-198630844); d=md5_ii(d,a,b,c,x[i+7],10,1126891415); c=md5_ii(c,d,a,b,x[i+14],15,-1416354905); b=md5_ii(b,c,d,a,x[i+5],21,-57434055);
		a=md5_ii(a,b,c,d,x[i+12],6,1700485571); d=md5_ii(d,a,b,c,x[i+3],10,-1894986606); c=md5_ii(c,d,a,b,x[i+10],15,-1051523); b=md5_ii(b,c,d,a,x[i+1],21,-2054922799);
		a=md5_ii(a,b,c,d,x[i+8],6,1873313359); d=md5_ii(d,a,b,c,x[i+15],10,-30611744); c=md5_ii(c,d,a,b,x[i+6],15,-1560198380); b=md5_ii(b,c,d,a,x[i+13],21,1309151649);
		a=md5_ii(a,b,c,d,x[i+4],6,-145523070); d=md5_ii(d,a,b,c,x[i+11],10,-1120210379); c=md5_ii(c,d,a,b,x[i+2],15,718787259); b=md5_ii(b,c,d,a,x[i+9],21,-343485551);
		a=safe_add(a,olda); b=safe_add(b,oldb); c=safe_add(c,oldc); d=safe_add(d,oldd);
	return (a,b,c,d)

def rstr2binl(arg1):
	_local2 = []
	for x in range((len(arg1) >> 2)+1):
		_local2.append(0)
	_local3 = 0
	while (_local3 < (len(arg1) * 8)):
		_local2[(_local3 >> 5)] = (_local2[(_local3 >> 5)] | ((ord(arg1[_local3 / 8]) & 0xFF) << (_local3 % 32)));
		_local3 = (_local3 + 8);
	string_local = str(_local2).strip('[]').replace(" ","")
	return _local2

def rstr2b64(_arg1):
	_local6 = 0
	_local7 = 0
	_local2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
	_local3 = ""
	_local4 = len(_arg1)
	_local5 = 0
	helper2 = 0
	while (_local5 < _local4):
		if (((_local5 + 1) < _local4)):
			helper1 = ord(_arg1[_local5 + 1]) << 8
		else:
			helper1 = 0
		if (((_local5 + 2) < _local4)):
			helper2 = ord(_arg1[_local5 + 2])
		else:
			helper2 = 0
		_local6 = ((ord(_arg1[_local5]) << 16) | helper1 | helper2)
		_local7 = 0
		while (_local7 < 4):
			if (((_local5 * 8) + (_local7 * 6)) > (len(_arg1) * 8)):
				_local3 = (_local3 + "")
			else:
				_local3 = (_local3 + _local2[ ((_local6 >> (6 * (3 - _local7))) & 63)] )
			_local7 += 1
		_local5 = _local5 + 3
	return (_local3)