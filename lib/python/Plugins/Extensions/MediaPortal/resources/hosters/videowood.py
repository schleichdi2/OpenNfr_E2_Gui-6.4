# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *

def videowood(self, data):
	parse = re.search('(....ωﾟ.*?);</script>', data)
	if parse:
		todecode = parse.group(1).split(';')
		todecode = todecode[-1].replace(' ','')

		code = {
			"(ﾟДﾟ)[ﾟoﾟ]" : "o",
			"(ﾟДﾟ) [return]" : "\\",
			"(ﾟДﾟ) [ ﾟΘﾟ]" : "_",
			"(ﾟДﾟ) [ ﾟΘﾟﾉ]" : "b",
			"(ﾟДﾟ) [ﾟｰﾟﾉ]" : "d",
			"(ﾟДﾟ)[ﾟεﾟ]": "/",
			"(oﾟｰﾟo)": '(u)',
			"3ﾟｰﾟ3": "u",
			"(c^_^o)": "0",
			"(o^_^o)": "3",
			"ﾟεﾟ": "return",
			"ﾟωﾟﾉ": "undefined",
			"_": "3",
			"(ﾟДﾟ)['0']" : "c",
			"c": "0",
			"(ﾟΘﾟ)": "1",
			"o": "3",
			"(ﾟｰﾟ)": "4",
			}
		cryptnumbers = []
		for searchword,isword in code.iteritems():
			todecode = todecode.replace(searchword,isword)
		for i in range(len(todecode)):
			if todecode[i:i+2] == '/+':
				for j in range(i+2, len(todecode)):
					if todecode[j:j+2] == '+/':
						cryptnumbers.append(todecode[i+1:j])
						i = j
						break
						break
		finalstring = ''
		for item in cryptnumbers:
			chrnumber = '\\'
			jcounter = 0
			while jcounter < len(item):
				clipcounter = 0
				if item[jcounter] == '(':
					jcounter +=1
					clipcounter += 1
					for k in range(jcounter, len(item)):
						if item[k] == '(':
							clipcounter += 1
						elif item[k] == ')':
							clipcounter -= 1
						if clipcounter == 0:
							jcounter = 0
							chrnumber = chrnumber + str(eval(item[:k+1]))
							item = item[k+1:]
							break
				else:
					jcounter +=1
			finalstring = finalstring + chrnumber.decode('unicode-escape')
		stream_url = re.search('=\s*(\'|")(.*?)$', finalstring)
		if stream_url:
			self._callback(stream_url.group(2).encode('utf-8'))
			return
	self.stream_not_found()