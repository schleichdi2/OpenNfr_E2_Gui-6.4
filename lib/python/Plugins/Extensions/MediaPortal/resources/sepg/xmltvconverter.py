# -*- coding: utf-8 -*-
#
#    Copyright (c) 2015 Billy2011, MediaPortal Team
#    Based on XmltvConverter from xmltv.org

import time
import calendar
from xml.etree.cElementTree import ElementTree, Element, SubElement, tostring, iterparse
from twisted.internet import reactor, defer
import log

# %Y%m%d%H%M%S 
def quickptime(str):
	return time.struct_time((int(str[0:4]), int(str[4:6]), int(str[6:8]),
				 int(str[8:10]), int(str[10:12]), 0,
				 -1, -1, 0))

def get_time_utc(timestring, fdateparse):
	try:
		values = timestring.split(' ')
		tm = fdateparse(values[0])
		timegm = calendar.timegm(tm)
		#suppose file says +0300 => that means we have to substract 3 hours from localtime to get gmt
		timegm -= (3600*int(values[1])/100)
		return timegm
	except Exception, e:
		print>>log, "[XMLTVConverter] get_time_utc error:", e
		return 0

# Preferred language should be configurable, but for now,
# we just like German better!
def get_xml_string(elem, name):
	r = ''
	try:
		for node in elem.findall(name):
			txt = node.text
			lang = node.get('lang', None)
			if not r:
				r = txt
			elif lang == "de":
				r = txt 
	except Exception,  e:
		print>>log, "[XMLTVConverter] get_xml_string error:",  e
	# Now returning UTF-8 by default, the epgdat/oudeis must be adjusted to make this work. 
	return r.encode('utf-8')

def enumerateProgrammes(fp):
	"""Enumerates programme ElementTree nodes from file object 'fp'"""
	fp.readline()
	try:
		for event, elem in iterparse(fp):
			if elem.tag == 'programme':
				yield elem
				elem.clear()
			elif elem.tag == 'channel':
				# Throw away channel elements, save memory
				elem.clear()    
	except Exception, e:
		print>>log, "[XMLTVConverter] enumerateProgrammes error:", e
		yield None

class XMLTVConverter:
	def __init__(self, dateformat = '%Y%m%d%H%M%S %Z'):
		if dateformat.startswith('%Y%m%d%H%M%S'):
		    self.dateParser = quickptime
		else:
			self.dateParser = lambda x: time.strptime(x, dateformat) 
    
	def enumFile(self, fileobj):
		lastUnknown = None
		for elem in enumerateProgrammes(fileobj):
			if not elem: continue
			channel = elem.get('channel')
			try:
				start = get_time_utc(elem.get('start'), self.dateParser)
				stop = get_time_utc(elem.get('stop'), self.dateParser)
				title = get_xml_string(elem, 'title')
				subtitle = get_xml_string(elem, 'sub-title')
				if not stop or not start or (stop <= start):
					print>>log, "[XMLTVConverter] Bad start/stop time: %s (%s) - %s (%s) [%s]" % (elem.get('start'), start, elem.get('stop'), stop, title)  
				yield (channel, (int(start), int(stop), title, subtitle))
			except Exception,  e:
				print>>log, "[XMLTVConverter] parsing event error:", e
