# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _

from enigma import gFont, addFont, eTimer, eConsoleAppContainer, ePicLoad, loadPNG, getDesktop, eServiceReference, iPlayableService, eListboxPythonMultiContent, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, eListbox, gPixmapPtr, getPrevAsciiCode, eBackgroundFileEraser

from Plugins.Plugin import PluginDescriptor

from twisted import __version__
from twisted.internet import reactor, defer
from twisted.web.http_headers import Headers
from twisted.internet.defer import Deferred, succeed
from twisted.web import http
from twisted.python import failure

from twisted.web import error as weberror

from cookielib import CookieJar

from zope.interface import implements

from twagenthelper import TwAgentHelper, twAgentGetPage
from tw_util import downloadPage, getPage
from sepg.mp_epg import SimpleEPG, mpepg, mutex
from sepg import log

from Components.ActionMap import NumberActionMap, ActionMap, HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.Button import Button
from config import config_mp, configfile_mp
from Components.config import config, ConfigInteger, ConfigSelection, getConfigListEntry, ConfigText, ConfigDirectory, ConfigBoolean, configfile, ConfigSelection, ConfigSubsection, ConfigPIN, NoSave, ConfigNothing, ConfigIP

yes_no_descriptions = {False: _("no"), True: _("yes")}
class ConfigYesNo(ConfigBoolean):
	def __init__(self, default = False):
		ConfigBoolean.__init__(self, default = default, descriptions = yes_no_descriptions)

try:
	from Components.config import ConfigPassword
except ImportError:
	ConfigPassword = ConfigText
try:
	from Components.config import ConfigOnOff
except ImportError:
	from Components.config import ConfigEnableDisable
	ConfigOnOff = ConfigEnableDisable
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.Boolean import Boolean
from Components.Input import Input

from Screens.InfoBar import MoviePlayer, InfoBar
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarNotifications

from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Screens.HelpMenu import HelpableScreen

from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN, SCOPE_CURRENT_SKIN, SCOPE_FONTS, createDir
from Tools.LoadPixmap import LoadPixmap
from Tools.NumericalTextInput import NumericalTextInput

import re, urllib, urllib2, os, cookielib, socket, sha, shutil, datetime, math, hashlib, random, json, md5, string, xml.etree.cElementTree, StringIO, Queue, threading, sys

from urllib2 import Request, URLError, urlopen as urlopen2
from socket import gaierror, error
from urllib import quote, unquote_plus, unquote, urlencode
from binascii import unhexlify, hexlify
from urlparse import parse_qs
from time import time, localtime, strftime, mktime

# MediaPortal Imports
from debuglog import printlog as printl

class InsensitiveKey(object):
	def __init__(self, key):
		self.key = key
	def __hash__(self):
		return hash(self.key.lower())
	def __eq__(self, other):
		return self.key.lower() == other.key.lower()
	def __str__(self):
		return self.key

class InsensitiveDict(dict):
	def __setitem__(self, key, value):
		key = InsensitiveKey(key)
		super(InsensitiveDict, self).__setitem__(key, value)
	def __getitem__(self, key):
		key = InsensitiveKey(key)
		return super(InsensitiveDict, self).__getitem__(key)

def r_getPage(url, *args, **kwargs):
	def retry(err):
		return getPage(url.replace('https:','http:'), *args, **kwargs)
	return twAgentGetPage(url, *args, **kwargs).addErrback(retry)

import mp_globals

#if mp_globals.isDreamOS:
#	from pixmapext import PixmapExt as Pixmap

try:
	from Screens.InfoBarGenerics import InfoBarServiceErrorPopupSupport
except:
	class InfoBarServiceErrorPopupSupport:
		def __init__(self):
			pass

try:
	from Screens.InfoBarGenerics import InfoBarGstreamerErrorPopupSupport
	mp_globals.stateinfo = True
except:
	class InfoBarGstreamerErrorPopupSupport:
		def __init__(self):
			mp_globals.stateinfo = False

from mp_globals import std_headers
from streams import isSupportedHoster, get_stream_link
from mpscreen import MPScreen, MPSetupScreen, SearchHelper
from simpleplayer import SimplePlayer
from coverhelper import CoverHelper
from showAsThumb import ThumbsHelper
from messageboxext import MessageBoxExt

def registerFont(file, name, scale, replacement):
	addFont(file, name, scale, replacement)

def getUserAgent():
	userAgents = [
		"Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
		"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; de) Presto/2.9.168 Version/11.52",
		"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20120101 Firefox/35.0",
		"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0",
		"Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0",
		"Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
		"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36",
		"Mozilla/5.0 (compatible; Konqueror/4.5; FreeBSD) KHTML/4.5.4 (like Gecko)",
		"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",
	]
	return random.choice(userAgents)

def getUpdateUrl():
	updateurls = [
		'http://e2-mediaportal.sourceforge.net/version.txt',
		'http://dhwz.github.io/e2-mediaportal/version.txt',
		'http://dhwz.gitlab.io/pages/version.txt'
	]
	return random.choice(updateurls)

def getIconUrl():
	iconurls = [
		'http://dhwz.gitlab.io/pages/',
		'http://dhwz.github.io/e2-mediaportal/',
		'http://dhwz.gitlab.io/pages/'
	]
	return random.choice(iconurls)

def testWebConnection(host="www.google.de", port=80, timeout=3):
	import socket

	try:
		socket.setdefaulttimeout(timeout)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
		return True
	except Exception as ex:
		return False

def decodeHtml(text):
	import HTMLParser
	h = HTMLParser.HTMLParser()
	# We have to repeat this multiple times (fixes e.g. broken Liveleak encodings)
	try:
		text = h.unescape(text).encode('utf-8')
		text = h.unescape(text).encode('utf-8')
		text = h.unescape(text).encode('utf-8')
	except:
		text = text.decode('latin1').encode('utf-8')

	# New HTML5 encodings
	text = text.replace('&period;','.')
	text = text.replace('&comma;',',')
	text = text.replace('&semi;',';')
	text = text.replace('&colon;',':')
	text = text.replace('&plus;','+')
	text = text.replace('&amp;','&')
	text = text.replace('&equals;','=')
	text = text.replace('&num;','#')
	text = text.replace('&excl;','!')
	text = text.replace('&quest;','?')
	text = text.replace('&lowbar;','_')
	text = text.replace('&rpar;',')')
	text = text.replace('&lpar;','(')
	text = text.replace('&rsqb;',']')
	text = text.replace('&lsqb;','[')

	text = text.replace('&IOcy;','Ё')
	text = text.replace('&DJcy;','Ђ')
	text = text.replace('&GJcy;','Ѓ')
	text = text.replace('&Jukcy;','Є')
	text = text.replace('&DScy;','Ѕ')
	text = text.replace('&Iukcy;','І')
	text = text.replace('&YIcy;','Ї')
	text = text.replace('&Jsercy;','Ј')
	text = text.replace('&LJcy;','Љ')
	text = text.replace('&NJcy;','Њ')
	text = text.replace('&TSHcy;','Ћ')
	text = text.replace('&KJcy;','Ќ')
	text = text.replace('&Ubrcy;','Ў')
	text = text.replace('&DZcy;','Џ')
	text = text.replace('&Acy;','А')
	text = text.replace('&Bcy;','Б')
	text = text.replace('&Vcy;','В')
	text = text.replace('&Gcy;','Г')
	text = text.replace('&Dcy;','Д')
	text = text.replace('&IEcy;','Е')
	text = text.replace('&ZHcy;','Ж')
	text = text.replace('&Zcy;','З')
	text = text.replace('&Icy;','И')
	text = text.replace('&Jcy;','Й')
	text = text.replace('&Kcy;','К')
	text = text.replace('&Lcy;','Л')
	text = text.replace('&Mcy;','М')
	text = text.replace('&Ncy;','Н')
	text = text.replace('&Ocy;','О')
	text = text.replace('&Pcy;','П')
	text = text.replace('&Rcy;','Р')
	text = text.replace('&Scy;','С')
	text = text.replace('&Tcy;','Т')
	text = text.replace('&Ucy;','У')
	text = text.replace('&Fcy;','Ф')
	text = text.replace('&KHcy;','Х')
	text = text.replace('&TScy;','Ц')
	text = text.replace('&CHcy;','Ч')
	text = text.replace('&SHcy;','Ш')
	text = text.replace('&SHCHcy;','Щ')
	text = text.replace('&HARDcy;','Ъ')
	text = text.replace('&Ycy;','Ы')
	text = text.replace('&SOFTcy;','Ь')
	text = text.replace('&Ecy;','Э')
	text = text.replace('&YUcy;','Ю')
	text = text.replace('&YAcy;','Я')
	text = text.replace('&acy;','а')
	text = text.replace('&bcy;','б')
	text = text.replace('&vcy;','в')
	text = text.replace('&gcy;','г')
	text = text.replace('&dcy;','д')
	text = text.replace('&iecy;','е')
	text = text.replace('&zhcy;','ж')
	text = text.replace('&zcy;','з')
	text = text.replace('&icy;','и')
	text = text.replace('&jcy;','й')
	text = text.replace('&kcy;','к')
	text = text.replace('&lcy;','л')
	text = text.replace('&mcy;','м')
	text = text.replace('&ncy;','н')
	text = text.replace('&ocy;','о')
	text = text.replace('&pcy;','п')
	text = text.replace('&rcy;','р')
	text = text.replace('&scy;','с')
	text = text.replace('&tcy;','т')
	text = text.replace('&ucy;','у')
	text = text.replace('&fcy;','ф')
	text = text.replace('&khcy;','х')
	text = text.replace('&tscy;','ц')
	text = text.replace('&chcy;','ч')
	text = text.replace('&shcy;','ш')
	text = text.replace('&shchcy;','щ')
	text = text.replace('&hardcy;','ъ')
	text = text.replace('&ycy;','ы')
	text = text.replace('&softcy;','ь')
	text = text.replace('&ecy;','э')
	text = text.replace('&yucy;','ю')
	text = text.replace('&yacy;','я')
	text = text.replace('&iocy;','ё')
	text = text.replace('&djcy;','ђ')
	text = text.replace('&gjcy;','ѓ')
	text = text.replace('&jukcy;','є')
	text = text.replace('&dscy;','ѕ')
	text = text.replace('&iukcy;','і')
	text = text.replace('&yicy;','ї')
	text = text.replace('&jsercy;','ј')
	text = text.replace('&ljcy;','љ')
	text = text.replace('&njcy;','њ')
	text = text.replace('&tshcy;','ћ')
	text = text.replace('&kjcy;','ќ')
	text = text.replace('&ubrcy;','ў')
	text = text.replace('&dzcy;','џ')

	# Replace only \uxxxx
	if re.search('\\u[0-9a-fA-F]{4}', text, re.S):
		endpos = len(text)
		pos = 0
		out = ''
		while pos < endpos:
			if text[pos] == "\\" and text[pos+1] == "u" and re.match('[0-9a-fA-F]{4}', text[pos+2:pos+6], re.S):
				dec = text[pos:pos+6].decode('unicode-escape').encode('utf-8')
				out += dec
				pos += 6
			else:
				out += text[pos]
				pos += 1
	else: out = text
	return out

def stripAllTags(html):
	cleanr = re.compile('<.*?>')
	cleantext = re.sub(cleanr,'', html.replace('\n',''))
	return cleantext