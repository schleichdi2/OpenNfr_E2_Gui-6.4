# -*- coding: utf-8 -*-
##############################################################################################################
#
#    MediaPortal for Dreambox OS
#
#    Coded by MediaPortal Team (c) 2013-2019
#
#  This plugin is open source but it is NOT free software.
#
#  This plugin may only be distributed to and executed on hardware which
#  is licensed by Dream Property GmbH. This includes commercial distribution.
#  In other words:
#  It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
#  to hardware which is NOT licensed by Dream Property GmbH.
#  It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
#  on hardware which is NOT licensed by Dream Property GmbH.
#
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#
#  If you want to use or modify the code or parts of it,
#  you have to keep OUR license and inform us about the modifications, but it may NOT be
#  commercially distributed other than under the conditions noted above.
#
#  As an exception regarding execution on hardware, you are permitted to execute this plugin on VU+ hardware
#  which is licensed by satco europe GmbH, if the VTi image is used on that hardware.
#
#  As an exception regarding modifcations, you are NOT permitted to remove
#  any copy protections implemented in this plugin or change them for means of disabling
#  or working around the copy protections, unless the change has been explicitly permitted
#  by the original authors. Also decompiling and modification of the closed source
#  parts is NOT permitted.
#
#  Advertising with this plugin is NOT allowed.
#  For other uses, permission from the authors is necessary.
#
##############################################################################################################

SHOW_HANG_STAT = False

# General imports
from . import _
from Tools.BoundFunction import boundFunction
from base64 import b64decode as bsdcd
from resources.imports import *
from resources.update import *
from resources.simplelist import *
from resources.simpleplayer import SimplePlaylistIO
from resources.twagenthelper import twAgentGetPage, twDownloadPage
from resources.configlistext import ConfigListScreenExt
from resources.choiceboxext import ChoiceBoxExt
from resources.pininputext import PinInputExt
from resources.decrypt import *
from resources.realdebrid import realdebrid_oauth2
try:
	from Components.config import ConfigPassword
except ImportError:
	ConfigPassword = ConfigText

from twisted.internet import task
from resources.twisted_hang import HangWatcher

CONFIG = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/additions/additions.xml"

desktopSize = getDesktop(0).size()
if desktopSize.width() == 1920:
	mp_globals.videomode = 2
	mp_globals.fontsize = 30
	mp_globals.sizefactor = 3
	mp_globals.pagebar_posy = 985

try:
	from enigma import eMediaDatabase
	mp_globals.isDreamOS = True
except:
	mp_globals.isDreamOS = False

try:
	f = open("/proc/stb/info/model", "r")
	model = ''.join(f.readlines()).strip()
except:
	model = ''

try:
	from Components.ScreenAnimations import *
	mp_globals.animations = True
	sa = ScreenAnimations()
	sa.fromXML(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/animations.xml"))
except:
	mp_globals.animations = False

try:
	from Components.CoverCollection import CoverCollection
	if mp_globals.isDreamOS and model not in ["dm520","dm525"]:
		mp_globals.covercollection = True
	else:
		mp_globals.covercollection = False
except:
	mp_globals.covercollection = False

try:
	from enigma import eWallPythonMultiContent, BT_SCALE
	from Components.BaseWall import BaseWall
	class CoverWall(BaseWall):
		def setentry(self, entry):
			res = [entry]
			res.append((eWallPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, eWallPythonMultiContent.SHOW_ALWAYS, 0, 0, 0, 0, 100, 100, 100, 100, loadPNG(entry[2]), None, None, BT_SCALE))
			return res
	mp_globals.isVTi = True
except:
	mp_globals.isVTi = False

try:
	from enigma import getVTiVersionString
	mp_globals.fakeScale = True
except:
	try:
		import boxbranding
		mp_globals.fakeScale = True
	except:
		if fileExists("/etc/.box"):
			mp_globals.fakeScale = True
		else:
			mp_globals.fakeScale = False

try:
	import requests
except:
	requestsModule = False
else:
	requestsModule = True

try:
	from Plugins.Extensions.MediaInfo.plugin import MediaInfo
	MediaInfoPresent = True
except:
	MediaInfoPresent = False

def lastMACbyte():
	try:
		return int(open('/sys/class/net/eth0/address').readline().strip()[-2:], 16)
	except:
		return 256

def calcDefaultStarttime():
	try:
		# Use the last MAC byte as time offset (half-minute intervals)
		offset = lastMACbyte() * 30
	except:
		offset = 7680
	return (5 * 60 * 60) + offset

def downloadPage(url, path):
	agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 Safari/537.36"
	return twDownloadPage(url, path, timeout=30, agent=agent)

def grabpage(pageurl, method='GET', postdata={}):
	agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 Safari/537.36"
	if requestsModule:
		try:
			import urlparse
			s = requests.session()
			url = urlparse.urlparse(pageurl)
			if method == 'GET':
				headers = {'User-Agent': agent}
				page = s.get(url.geturl(), headers=headers, timeout=15)
			return page.content
		except:
			return None
	else:
		return None

from Components.config import ConfigClock, ConfigSequence

class ConfigPORNPIN(ConfigInteger):
	def __init__(self, default, len = 4, censor = ""):
		ConfigSequence.__init__(self, seperator = ":", limits = [(1000, (10**len)-1)], censor_char = censor, default = default)

config_mp.mediaportal = ConfigSubsection()
config.mediaportal = ConfigSubsection()

# Fake entry fuer die Kategorien
config_mp.mediaportal.fake_entry = NoSave(ConfigNothing())

# EPG Import
config_mp.mediaportal.epg_enabled = ConfigOnOff(default = False)
config_mp.mediaportal.epg_runboot = ConfigOnOff(default = False)
config_mp.mediaportal.epg_wakeupsleep = ConfigOnOff(default = False)
config_mp.mediaportal.epg_wakeup = ConfigClock(default = calcDefaultStarttime())
config_mp.mediaportal.epg_deepstandby = ConfigSelectionExt(default = "skip", choices = [
		("wakeup", _("Wake up and import")),
		("skip", _("Skip the import"))
		])

# Allgemein
config_mp.mediaportal.version = NoSave(ConfigText(default="2019032402"))
config.mediaportal.version = NoSave(ConfigText(default="2019032402"))
config_mp.mediaportal.autoupdate = ConfigYesNo(default = True)
config.mediaportal.autoupdate = NoSave(ConfigYesNo(default = True))

config_mp.mediaportal.skinfail = ConfigYesNo(default = False)

config_mp.mediaportal.retries = ConfigSubsection()

config_mp.mediaportal.pincode = ConfigPIN(default = 0000)
config_mp.mediaportal.retries.pincode = ConfigSubsection()
config_mp.mediaportal.retries.pincode.tries = ConfigInteger(default = 3)
config_mp.mediaportal.retries.pincode.time = ConfigInteger(default = 0)

config_mp.mediaportal.adultpincode = ConfigPORNPIN(default = random.randint(1,999), len = 4)
if config_mp.mediaportal.adultpincode.value < 1:
	config_mp.mediaportal.adultpincode.value = random.randint(1,999)

config_mp.mediaportal.retries.adultpin = ConfigSubsection()
config_mp.mediaportal.retries.adultpin.tries = ConfigInteger(default = 3)
config_mp.mediaportal.retries.adultpin.time = ConfigInteger(default = 0)

config_mp.mediaportal.showporn = ConfigYesNo(default = False)
config_mp.mediaportal.hideporn_startup = ConfigYesNo(default = True)
config_mp.mediaportal.showuseradditions = ConfigYesNo(default = False)
config_mp.mediaportal.pinuseradditions = ConfigYesNo(default = False)
config_mp.mediaportal.ena_suggestions = ConfigYesNo(default = True)

config_mp.mediaportal.animation_coverart = ConfigSelectionExt(default = "mp_crossfade_fast", choices = [("mp_crossfade_fast", _("Crossfade (fast)")),("mp_crossfade_slow", _("Crossfade (slow)"))])
config_mp.mediaportal.animation_label = ConfigSelectionExt(default = "mp_crossfade_fast", choices = [("mp_crossfade_fast", _("Crossfade (fast)")),("mp_crossfade_slow", _("Crossfade (slow)"))])

skins = []
if mp_globals.videomode == 2:
	mp_globals.skinsPath = "/skins_1080"
	for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/"):
		if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/", skin)):
			skins.append(skin)
	config_mp.mediaportal.skin2 = ConfigSelectionExt(default = "clean_fhd", choices = skins)
	config.mediaportal.skin2 = NoSave(ConfigSelectionExt(default = "clean_fhd", choices = skins))
	mp_globals.skinFallback = "/clean_fhd"
else:
	mp_globals.skinsPath = "/skins_720"
	for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_720/"):
		if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_720/", skin)):
			if skin != "original":
				skins.append(skin)
	config_mp.mediaportal.skin2 = ConfigSelectionExt(default = "clean_hd", choices = skins)
	config.mediaportal.skin2 = NoSave(ConfigSelectionExt(default = "clean_hd", choices = skins))
	mp_globals.skinFallback = "/clean_hd"

config_mp.mediaportal.skin = NoSave(ConfigText(default=config_mp.mediaportal.skin2.value))

config_mp.mediaportal.debugMode = ConfigSelectionExt(default="Silent", choices = ["High", "Normal", "Silent"])

if mp_globals.covercollection or mp_globals.isVTi:
	if config_mp.mediaportal.debugMode.value == "High":
		config_mp.mediaportal.ansicht = ConfigSelectionExt(default = "wall2", choices = [("wall2", _("Wall 2.0")), ("wall", _("Wall")), ("liste", _("List"))])
	else:
		config_mp.mediaportal.ansicht = ConfigSelectionExt(default = "wall2", choices = [("wall2", _("Wall 2.0")), ("liste", _("List"))])
elif mp_globals.videomode == 2 and mp_globals.fakeScale:
	config_mp.mediaportal.ansicht = ConfigSelectionExt(default = "wall", choices = [("wall", _("Wall")), ("liste", _("List"))])
elif mp_globals.videomode == 2 and not mp_globals.isDreamOS:
	config_mp.mediaportal.ansicht = ConfigSelectionExt(default = "liste", choices = [("liste", _("List"))])
else:
	config_mp.mediaportal.ansicht = ConfigSelectionExt(default = "wall", choices = [("wall", _("Wall")), ("liste", _("List"))])
config_mp.mediaportal.wallmode = ConfigSelectionExt(default = "color_zoom", choices = [("color_zoom", _("Color")),("bw_zoom", _("Black&White"))])
config_mp.mediaportal.wall2mode = ConfigSelectionExt(default = "color", choices = [("color", _("Color")),("bw", _("Black&White"))])
config_mp.mediaportal.hlsp_enable = ConfigYesNo(default = True)
config_mp.mediaportal.hls_proxy_ip = ConfigIP(default = [127,0,0,1], auto_jump = True)
config_mp.mediaportal.hls_proxy_port = ConfigInteger(default = 0, limits = (0,65535))
config_mp.mediaportal.hls_buffersize = ConfigInteger(default = 32, limits = (1,64))
config_mp.mediaportal.storagepath = ConfigText(default="/tmp/mediaportal/tmp/", fixed_size=False)
config_mp.mediaportal.iconcachepath = ConfigText(default="/media/hdd/mediaportal/", fixed_size=False)
config_mp.mediaportal.autoplayThreshold = ConfigInteger(default = 50, limits = (1,100))
config_mp.mediaportal.filter = ConfigSelectionExt(default = "ALL", choices = ["ALL", "Mediathek", "User-additions", "Fun", "NewsDoku", "Sport", "Music", "Porn"])
config.mediaportal.filter = NoSave(ConfigSelectionExt(default = "ALL", choices = ["ALL"]))
config_mp.mediaportal.youtubeenablevp9 = ConfigYesNo(default = False)
config_mp.mediaportal.youtubeenabledash = ConfigYesNo(default = False)
config_mp.mediaportal.youtubeenabledash720p = ConfigYesNo(default = False)
config_mp.mediaportal.youtubeenabledash480p = ConfigYesNo(default = False)
config_mp.mediaportal.youtubeprio = ConfigSelectionExt(default = "2", choices = [("0", "360p"),("1", "480p"),("2", "720p"),("3", "1080p"),("4", "1440p"),("5", "2160p")])
config_mp.mediaportal.videoquali_others = ConfigSelectionExt(default = "2", choices = [("0", _("Low")),("1", _("Medium")),("2", _("High"))])
config_mp.mediaportal.pornpin = ConfigYesNo(default = True)
config_mp.mediaportal.pornpin_cache = ConfigSelectionExt(default = "0", choices = [("0", _("never")), ("5", _("5 minutes")), ("15", _("15 minutes")), ("30", _("30 minutes")), ("60", _("60 minutes"))])
config_mp.mediaportal.kidspin = ConfigYesNo(default = False)
config_mp.mediaportal.setuppin = ConfigYesNo(default = False)
config_mp.mediaportal.watchlistpath = ConfigText(default="/etc/enigma2/", fixed_size=False)
config_mp.mediaportal.sortplugins = ConfigSelectionExt(default = "abc", choices = [("hits", "Hits"), ("abc", "ABC"), ("user", "User")])
config_mp.mediaportal.pagestyle = ConfigSelectionExt(default="Graphic", choices = ["Graphic", "Text"])
config_mp.mediaportal.font = ConfigSelectionExt(default = "1", choices = [("1", "Mediaportal 1")])
config_mp.mediaportal.showAsThumb = ConfigYesNo(default = False)
config_mp.mediaportal.restorelastservice = ConfigSelectionExt(default = "1", choices = [("1", _("after SimplePlayer quits")),("2", _("after MediaPortal quits"))])
config_mp.mediaportal.backgroundtv = ConfigYesNo(default = False)
config_mp.mediaportal.minitv = ConfigYesNo(default = True)

# Konfiguration erfolgt in SimplePlayer
config_mp.mediaportal.sp_playmode = ConfigSelectionExt(default = "forward", choices = [("forward", _("Forward")),("backward", _("Backward")),("random", _("Random")),("endless", _("Endless"))])
config_mp.mediaportal.sp_on_movie_stop = ConfigSelectionExt(default = "quit", choices = [("ask", _("Ask user")), ("quit", _("Return to previous service"))])
config_mp.mediaportal.sp_on_movie_eof = ConfigSelectionExt(default = "quit", choices = [("ask", _("Ask user")), ("quit", _("Return to previous service")), ("pause", _("Pause movie at end"))])
config_mp.mediaportal.sp_seekbar_sensibility = ConfigInteger(default = 10, limits = (1,50))
config_mp.mediaportal.sp_infobar_cover_off = ConfigYesNo(default = False)
config_mp.mediaportal.sp_use_number_seek = ConfigYesNo(default = True)
config_mp.mediaportal.sp_pl_number = ConfigInteger(default = 1, limits = (1,99))
config_mp.mediaportal.sp_use_yt_with_proxy = ConfigSelectionExt(default = "no", choices = [("no", _("No")), ("prz", "with Premiumize"), ("rdb", "with Real-Debrid"), ("proxy", "with a HTTP Proxy")])
config_mp.mediaportal.sp_on_movie_start = ConfigSelectionExt(default = "start", choices = [("start", _("Start from the beginning")), ("ask", _("Ask user")), ("resume", _("Resume from last position"))])
config_mp.mediaportal.sp_save_resumecache = ConfigYesNo(default = False)
config_mp.mediaportal.sp_radio_cover = ConfigSelectionExt(default = "large", choices = [("large", _("large")), ("small", _("small")), ("off", _("off"))])
if model in ["dm900","dm920"]:
	config_mp.mediaportal.sp_radio_visualization = ConfigSelectionExt(default = "1", choices = [("0", _("Off")), ("1", _("Mode 1")), ("2", _("Mode 2")), ("3", _("Mode 3"))])
else:
	config_mp.mediaportal.sp_radio_visualization = ConfigSelectionExt(default = "1", choices = [("0", _("Off")), ("1", _("Mode 1")), ("2", _("Mode 2"))])
config_mp.mediaportal.sp_radio_bgsaver = ConfigSelectionExt(default = "1", choices = [("0", _("Off")), ("1", _("Ken Burns effect")), ("2", _("Just photos"))])
config_mp.mediaportal.sp_radio_bgsaver_keywords = ConfigText(default="music", fixed_size=False)
config_mp.mediaportal.yt_proxy_username = ConfigText(default="user!", fixed_size=False)
config_mp.mediaportal.yt_proxy_password = ConfigPassword(default="pass!", fixed_size=False)
config_mp.mediaportal.yt_proxy_host = ConfigText(default = "example_proxy.com!", fixed_size = False)
config_mp.mediaportal.yt_proxy_port = ConfigInteger(default = 8080, limits = (0,65535))
config_mp.mediaportal.hlsp_proxy_username = ConfigText(default="user!", fixed_size=False)
config_mp.mediaportal.hlsp_proxy_password = ConfigPassword(default="pass!", fixed_size=False)
config_mp.mediaportal.hlsp_proxy_host = ConfigText(default = "example_proxy.com!", fixed_size = False)
config_mp.mediaportal.hlsp_proxy_port = ConfigInteger(default = 8080, limits = (0,65535))
config_mp.mediaportal.sp_use_hlsp_with_proxy = ConfigSelectionExt(default = "no", choices = [("no", _("No")), ("always", "Use it always"), ("plset", "Set in the playlist")])

# premiumize.me
config_mp.mediaportal.premiumize_use = ConfigYesNo(default = False)
config_mp.mediaportal.premiumize_username = ConfigText(default="user!", fixed_size=False)
config_mp.mediaportal.premiumize_password = ConfigPassword(default="pass!", fixed_size=False)
config_mp.mediaportal.premiumize_proxy_config_url = ConfigText(default="", fixed_size=False)

# real-debrid.com
config_mp.mediaportal.realdebrid_use = ConfigYesNo(default = False)
config_mp.mediaportal.realdebrid_accesstoken = ConfigText(default="", fixed_size=False)
config_mp.mediaportal.realdebrid_refreshtoken = ConfigText(default="", fixed_size=False)
config_mp.mediaportal.realdebrid_rclient_id = ConfigText(default="", fixed_size=False)
config_mp.mediaportal.realdebrid_rclient_secret = ConfigText(default="", fixed_size=False)

# Premium Hosters
config_mp.mediaportal.premium_color = ConfigSelectionExt(default="0xFFFF00", choices = [("0xFF0000",_("Red")),("0xFFFF00",_("Yellow")),("0x00FF00",_("Green")),("0xFFFFFF",_("White")),("0x00ccff",_("Light Blue")),("0x66ff99",_("Light Green"))])

# Userchannels Help
config_mp.mediaportal.show_userchan_help = ConfigYesNo(default = True)

# SimpleList
config_mp.mediaportal.simplelist_gcoversupp = ConfigYesNo(default = True)

# Radio
config_mp.mediaportal.is_radio = ConfigYesNo(default=False)

mp_globals.yt_a_backup = bsdcd(bsdcd(bsdcd(decrypt('kj8yV97e3t4fDPdo3ca07O6kKsuY9oZkvUqpBPJPkvzRYyzeAuLofAra3HKWsJmhvQ8EsGMDfnziGjqj3047WS8bojGewMj+in3daO4hlTSA6GUSwft7LNFdibC0hxTppR1VLXaRvKs=', CONFIG, 256))))
mp_globals.yt_a = bsdcd(bsdcd(bsdcd(decrypt('UZaWW4SEhITpj4ekRW9S5/qupnllwhRtf/E+k6BPucAMPts9j6xKJy3M1asKr3H0enK1QKFMvP03B4TW3vmWlKoZC9nKU1SY+rAHh+D/X3g0GyhgaRZKh0+mRaOrbnl8c7jfeYEHgU8=', CONFIG, 256))))
mp_globals.yt_i = bsdcd(bsdcd(bsdcd(decrypt('9ZKWW7W1tbVrxwsoRtc68/x46WsllFgLly3gXAz9y30Kb3u8wQDv8IkMeEhBLq6qmIVUnRR4vDmhyKaEI+yXGKYbP6uSyF1VIml94KxsPWYbgZ1jjBY8poOZAJJlqevbmo5e+jhzSZD/yiSJZB++WB7Qu6w4uHyccvAROJJdugm+sNhmyMGn74pTzYVtvetM9qJBNd3ddSYS/8qagLVxmJa0ahrVsJxVDFEQf0JeQtjGq/+j21YpZUiF+LQ9BzT8dq8p1J5YGBlzXvrDXpBWpcFMorw=', CONFIG, 256))))
mp_globals.yt_s = bsdcd(bsdcd(bsdcd(decrypt('9ZKWW8/Pz88jw+viDYpexb2691qucHXmNFnpAi7jmw0ElKgz8ecT5Xk4JEJlopqhHedBLa1g5g0DVl4ViAy14V+BLwjFRyHAmFnk29HqtedGRKgNZA2GT2cPGLhO8P/rtV+FQfqdaQA=', CONFIG, 256))))
mp_globals.bdmt = bsdcd(bsdcd(bsdcd(decrypt('Q8fFWGdnZ2djFfvOea2AHqS5bqR9nO0b8bxJ433nOffxa5nD1ELvd/Nm9sdojTjgz0knJTFI2jl0RYrtf4c5YnqSS3hkiq+CjpnV3uQG4Kr5wZZ91zKE3A==', CONFIG, 256))))

# Global variable
autoStartTimer = None
_session = None

# eUriResolver Imports for DreamOS
##############################################################################################################
try:
	from enigma import eUriResolver

	from resources.MPYoutubeUriResolver import MPYoutubeUriResolver
	MPYoutubeUriResolver.instance = MPYoutubeUriResolver()
	eUriResolver.addResolver(MPYoutubeUriResolver.instance)

	from resources.MPHLSPUriResolver import MPHLSPUriResolver
	MPHLSPUriResolver.instance = MPHLSPUriResolver()
	eUriResolver.addResolver(MPHLSPUriResolver.instance)

	from resources.MPEuronewsUriResolver import MPEuronewsUriResolver
	MPEuronewsUriResolver.instance = MPEuronewsUriResolver()
	eUriResolver.addResolver(MPEuronewsUriResolver.instance)

except ImportError:
	pass
##############################################################################################################


conf = xml.etree.cElementTree.parse(CONFIG)
for x in conf.getroot():
	if x.tag == "set" and x.get("name") == 'additions':
		root =  x
		for x in root:
			if x.tag == "plugin":
				if x.get("type") == "mod":
					modfile = x.get("modfile")
					if fileExists('/etc/enigma2/mp_override/'+modfile.split('.')[1]+'.py'):
						sys.path.append('/etc/enigma2/mp_override')
						exec("from "+modfile.split('.')[1]+" import *")
					else:
						exec("from additions."+modfile+" import *")
					exec("config_mp.mediaportal."+x.get("confopt")+" = ConfigYesNo(default = "+x.get("default")+")")

xmlpath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/additions/")
for file in os.listdir(xmlpath):
	if file.endswith(".xml") and file != "additions.xml":
		useraddition = xmlpath + file

		conf = xml.etree.cElementTree.parse(useraddition)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions_user':
				root =  x
				for x in root:
					if x.tag == "plugin":
						if x.get("type") == "mod":
							try:
								modfile = x.get("modfile")
								if fileExists('/etc/enigma2/mp_override/'+modfile.split('.')[1]+'.py'):
									sys.path.append('/etc/enigma2/mp_override')
									exec("from "+modfile.split('.')[1]+" import *")
								else:
									exec("from additions."+modfile+" import *")
								exec("config_mp.mediaportal."+x.get("confopt")+" = ConfigYesNo(default = "+x.get("default")+")")
							except Exception as e:
								printl(e,'',"E")

class CheckPathes:

	def __init__(self, session):
		self.session = session
		self.cb = None

	def checkPathes(self, cb):
		self.cb = cb
		res, msg = SimplePlaylistIO.checkPath(config_mp.mediaportal.watchlistpath.value, '', True)
		if not res:
			self.session.openWithCallback(self._callback, MessageBoxExt, msg, MessageBoxExt.TYPE_ERROR)

		res, msg = SimplePlaylistIO.checkPath(config_mp.mediaportal.storagepath.value, '', True)
		if not res:
			self.session.openWithCallback(self._callback, MessageBoxExt, msg, MessageBoxExt.TYPE_ERROR)

		if mp_globals.pluginPath in config_mp.mediaportal.iconcachepath.value:
			config_mp.mediaportal.iconcachepath.value = "/media/hdd/mediaportal/"
			config_mp.mediaportal.iconcachepath.save()
			configfile_mp.save()
		elif "/tmp/" in config_mp.mediaportal.iconcachepath.value:
			config_mp.mediaportal.iconcachepath.value = "/media/hdd/mediaportal/"
			config_mp.mediaportal.iconcachepath.save()
			configfile_mp.save()
		elif "/usr/lib/enigma2/" in config_mp.mediaportal.iconcachepath.value:
			config_mp.mediaportal.iconcachepath.value = "/media/hdd/mediaportal/"
			config_mp.mediaportal.iconcachepath.save()
			configfile_mp.save()
		elif "/var/volatile/" in config_mp.mediaportal.iconcachepath.value:
			config_mp.mediaportal.iconcachepath.value = "/media/hdd/mediaportal/"
			config_mp.mediaportal.iconcachepath.save()
			configfile_mp.save()
		elif "/var/share/" in config_mp.mediaportal.iconcachepath.value:
			config_mp.mediaportal.iconcachepath.value = "/media/hdd/mediaportal/"
			config_mp.mediaportal.iconcachepath.save()
			configfile_mp.save()
		elif "/usr/share/" in config_mp.mediaportal.iconcachepath.value:
			config_mp.mediaportal.iconcachepath.value = "/media/hdd/mediaportal/"
			config_mp.mediaportal.iconcachepath.save()
			configfile_mp.save()

		res, msg = SimplePlaylistIO.checkPath(config_mp.mediaportal.iconcachepath.value + "icons/", '', True)
		if not res:
			self.session.openWithCallback(self._callback, MessageBoxExt, msg, MessageBoxExt.TYPE_ERROR)

		res, msg = SimplePlaylistIO.checkPath(config_mp.mediaportal.iconcachepath.value + "icons_bw/", '', True)
		if not res:
			self.session.openWithCallback(self._callback, MessageBoxExt, msg, MessageBoxExt.TYPE_ERROR)

		res, msg = SimplePlaylistIO.checkPath(config_mp.mediaportal.iconcachepath.value + "logos/", '', True)
		if not res:
			self.session.openWithCallback(self._callback, MessageBoxExt, msg, MessageBoxExt.TYPE_ERROR)

	def _callback(self, answer):
		if self.cb:
			self.cb()

class PinCheck:

	def __init__(self):
		self.pin_entered = False
		self.timer = eTimer()
		if mp_globals.isDreamOS:
			self.timer_conn = self.timer.timeout.connect(self.lock)
		else:
			self.timer.callback.append(self.lock)

	def pinEntered(self):
		self.pin_entered = True
		self.timer.start(60000*int(config_mp.mediaportal.pornpin_cache.value), 1)

	def lock(self):
		self.pin_entered = False

pincheck = PinCheck()

class CheckPremiumize:

	def __init__(self, session):
		self.session = session

	def premiumize(self):
		if config_mp.mediaportal.premiumize_use.value:
			self.puser = config_mp.mediaportal.premiumize_username.value
			self.ppass = config_mp.mediaportal.premiumize_password.value
			url = "https://api.premiumize.me/pm-api/v1.php?method=accountstatus&params[login]=%s&params[pass]=%s" % (self.puser, self.ppass)
			r_getPage(url, timeout=15).addCallback(self.premiumizeData).addErrback(self.dataError)
		else:
			self.session.open(MessageBoxExt, _("premiumize.me is not activated."), MessageBoxExt.TYPE_ERROR)

	def premiumizeData(self, data):
		if re.search('status":200', data):
			infos = re.findall('"account_name":"(.*?)","type":"(.*?)","expires":(.*?),".*?trafficleft_gigabytes":(.*?)}', data, re.S|re.I)
			if infos:
				(a_name, a_type, a_expires, a_left) = infos[0]
				deadline = datetime.datetime.fromtimestamp(int(a_expires)).strftime('%d-%m-%Y')
				pmsg = "premiumize.me\n\nUser:\t%s\nType:\t%s\nExpires:\t%s\nPoints left:\t%4.2f" % (a_name, a_type, deadline, float(a_left))
				self.session.open(MessageBoxExt, pmsg , MessageBoxExt.TYPE_INFO)
			else:
				self.session.open(MessageBoxExt, _("premiumize.me failed."), MessageBoxExt.TYPE_ERROR)
		elif re.search('status":401', data):
			self.session.open(MessageBoxExt, _("premiumize: Login failed."), MessageBoxExt.TYPE_INFO, timeout=3)

	def premiumizeProxyConfig(self, msgbox=True):
		return
		url = config_mp.mediaportal.premiumize_proxy_config_url.value
		if re.search('^https://.*?\.pac', url):
			r_getPage(url, method="GET", timeout=15).addCallback(self.premiumizeProxyData, msgbox).addErrback(self.dataError)
		else:
			self.premiumize()

	def premiumizeProxyData(self, data, msgbox):
		m = re.search('PROXY (.*?):(\d{2}); PROXY', data)
		if m:
			mp_globals.premium_yt_proxy_host = m.group(1)
			mp_globals.premium_yt_proxy_port = int(m.group(2))
			print 'YT-Proxy:',m.group(1), ':', mp_globals.premium_yt_proxy_port
			if msgbox:
				self.session.open(MessageBoxExt, _("premiumize: YT ProxyHost found."), MessageBoxExt.TYPE_INFO)
		else:
			if msgbox:
				self.session.open(MessageBoxExt, _("premiumize: YT ProxyHost not found!"), MessageBoxExt.TYPE_ERROR)

	def dataError(self, error):
		printl(error,self,"E")

class MPSetup(Screen, CheckPremiumize, ConfigListScreenExt):

	def __init__(self, session):

		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/MP_Setup.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/MP_Setup.xml"

		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)

		Screen.__init__(self, session)

		self.configlist = []

		ConfigListScreenExt.__init__(self, self.configlist, on_change=self._onKeyChange, enableWrapAround=True)

		skins = []
		if mp_globals.videomode == 2:
			mp_globals.skinsPath = "/skins_1080"
			for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/"):
				if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_1080/", skin)):
					skins.append(skin)
			config_mp.mediaportal.skin2.setChoices(skins, "clean_fhd")
		else:
			mp_globals.skinsPath = "/skins_720"
			for skin in os.listdir("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_720/"):
				if os.path.isdir(os.path.join("/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/skins_720/", skin)):
					skins.append(skin)
			config_mp.mediaportal.skin2.setChoices(skins, "clean_hd")

		self._getConfig()

		if config_mp.mediaportal.adultpincode.value < 1:
			config_mp.mediaportal.adultpincode.value = random.randint(1,999)

		self['title'] = Label(_("Setup"))
		self['F1'] = Label("Premium")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label("")

		self["actions"] = ActionMap(["MP_Actions2", "MP_Actions"], {
			"ok"    : self.keySave,
			"cancel": self.keyCancel,
			"up": self.keyUp,
			"down": self.keyDown,
			"nextBouquet": self.keyPreviousSection,
			"prevBouquet": self.keyNextSection,
			"red" : self.premium
		}, -1)

		self.onFirstExecBegin.append(self.loadDisplayCover)

	def loadDisplayCover(self):
		self.summaries.updateCover('file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/default_cover.png')

	def _separator(self):
		if mp_globals.isDreamOS:
			pass
		else:
			self.configlist.append(getConfigListEntry(400 * "¯", ))

	def _spacer(self):
		self.configlist.append(getConfigListEntry("", config_mp.mediaportal.fake_entry, False))

	def _getConfig(self):
		self.configlist = []
		self.sport = []
		self.music = []
		self.fun = []
		self.newsdoku = []
		self.mediatheken = []
		self.porn = []
		self.useradditions = []
		### Allgemein
		self.configlist.append(getConfigListEntry(_("GENERAL"), ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Automatic Update Check:"), config_mp.mediaportal.autoupdate, False))
		self.configlist.append(getConfigListEntry(_("Mainview Style:"), config_mp.mediaportal.ansicht, True))
		if config_mp.mediaportal.ansicht.value == "wall":
			self.configlist.append(getConfigListEntry(_("Wall Mode:"), config_mp.mediaportal.wallmode, True))
		if config_mp.mediaportal.ansicht.value == "wall2":
			self.configlist.append(getConfigListEntry(_("Wall 2.0 Mode:"), config_mp.mediaportal.wall2mode, False))
		if (config_mp.mediaportal.ansicht.value == "wall" or config_mp.mediaportal.ansicht.value == "wall2"):
			self.configlist.append(getConfigListEntry(_("Page Display Style:"), config_mp.mediaportal.pagestyle, False))
		self.configlist.append(getConfigListEntry(_("Skin:"), config_mp.mediaportal.skin2, False))
		#self.configlist.append(getConfigListEntry(_("ShowAsThumb as Default:"), config_mp.mediaportal.showAsThumb, False))
		self.configlist.append(getConfigListEntry(_("Disable Background-TV:"), config_mp.mediaportal.backgroundtv, True))
		if not config_mp.mediaportal.backgroundtv.value:
			self.configlist.append(getConfigListEntry(_("Restore last service:"), config_mp.mediaportal.restorelastservice, False))
			self.configlist.append(getConfigListEntry(_("Disable Mini-TV:"), config_mp.mediaportal.minitv, False))
		self.configlist.append(getConfigListEntry(_("Enable search suggestions:"), config_mp.mediaportal.ena_suggestions, False))
		if mp_globals.animations:
			self.configlist.append(getConfigListEntry(_("Coverart animation")+":", config_mp.mediaportal.animation_coverart, False))
			self.configlist.append(getConfigListEntry(_("Label animation")+":", config_mp.mediaportal.animation_label, False))
		self._spacer()
		self.configlist.append(getConfigListEntry(_("YOUTH PROTECTION"), ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Setup PIN:"), config_mp.mediaportal.pincode, False))
		self.configlist.append(getConfigListEntry(_("Setup PIN Query:"), config_mp.mediaportal.setuppin, False))
		self.configlist.append(getConfigListEntry(_("Kids PIN Query:"), config_mp.mediaportal.kidspin, False))
		self.configlist.append(getConfigListEntry(_("Adult PIN:"), config_mp.mediaportal.adultpincode, False))
		self.configlist.append(getConfigListEntry(_("Adult PIN Query:"), config_mp.mediaportal.pornpin, False))
		self.configlist.append(getConfigListEntry(_("Remember Adult PIN:"), config_mp.mediaportal.pornpin_cache, False))
		self.configlist.append(getConfigListEntry(_("Auto hide adult section on startup:"), config_mp.mediaportal.hideporn_startup,False))
		self._spacer()
		self.configlist.append(getConfigListEntry(_("OTHER"), ))
		self._separator()
		#self.configlist.append(getConfigListEntry(_("Use HLS-Player:"), config_mp.mediaportal.hlsp_enable, True))
		#if config_mp.mediaportal.hlsp_enable.value:
		self.configlist.append(getConfigListEntry(_("HLS-Player buffersize [MB]:"), config_mp.mediaportal.hls_buffersize, False))
		#self.configlist.append(getConfigListEntry(_("HLS-Player IP:"), config_mp.mediaportal.hls_proxy_ip, False))
		#self.configlist.append(getConfigListEntry(_("HLS-Player Port:"), config_mp.mediaportal.hls_proxy_port, False))
		self.configlist.append(getConfigListEntry(_('Use HLS-Player Proxy:'), config_mp.mediaportal.sp_use_hlsp_with_proxy, False))
		self.configlist.append(getConfigListEntry(_("HLSP-HTTP-Proxy Host or IP:"), config_mp.mediaportal.hlsp_proxy_host, False))
		self.configlist.append(getConfigListEntry(_("HLSP-Proxy Port:"), config_mp.mediaportal.hlsp_proxy_port, False))
		self.configlist.append(getConfigListEntry(_("HLSP-Proxy username:"), config_mp.mediaportal.hlsp_proxy_username, False))
		self.configlist.append(getConfigListEntry(_("HLSP-Proxy password:"), config_mp.mediaportal.hlsp_proxy_password, False))
		self.configlist.append(getConfigListEntry(_("Temporary Cachepath:"), config_mp.mediaportal.storagepath, False))
		self.configlist.append(getConfigListEntry(_("Icon Cachepath:"), config_mp.mediaportal.iconcachepath, False))
		self.configlist.append(getConfigListEntry(_("Videoquality:"), config_mp.mediaportal.videoquali_others, False))
		self.configlist.append(getConfigListEntry(_("Watchlist/Playlist/Userchan path:"), config_mp.mediaportal.watchlistpath, False))
		self._spacer()
		self.configlist.append(getConfigListEntry(_("YOUTUBE"), ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Highest resolution for playback:"), config_mp.mediaportal.youtubeprio, False))
		self.configlist.append(getConfigListEntry(_("Enable DASH format (no seeking possible):"), config_mp.mediaportal.youtubeenabledash, True))
		if config_mp.mediaportal.youtubeenabledash.value:
			self.configlist.append(getConfigListEntry(_("Use DASH format for 480p:"), config_mp.mediaportal.youtubeenabledash480p, False))
			self.configlist.append(getConfigListEntry(_("Use DASH format for 720p:"), config_mp.mediaportal.youtubeenabledash720p, False))
			self.configlist.append(getConfigListEntry(_("Enable VP9 codec (required for resolutions >1080p):"), config_mp.mediaportal.youtubeenablevp9, False))
		self.configlist.append(getConfigListEntry(_("Show USER-Channels Help:"), config_mp.mediaportal.show_userchan_help, False))
		self.configlist.append(getConfigListEntry(_('Use Proxy:'), config_mp.mediaportal.sp_use_yt_with_proxy, True))
		if config_mp.mediaportal.sp_use_yt_with_proxy.value == "proxy":
			self.configlist.append(getConfigListEntry(_("HTTP-Proxy Host or IP:"), config_mp.mediaportal.yt_proxy_host, False))
			self.configlist.append(getConfigListEntry(_("HTTP-Proxy Port:"), config_mp.mediaportal.yt_proxy_port, False))
			self.configlist.append(getConfigListEntry(_("HTTP-Proxy username:"), config_mp.mediaportal.yt_proxy_username, False))
			self.configlist.append(getConfigListEntry(_("HTTP-Proxy password:"), config_mp.mediaportal.yt_proxy_password, False))
		#self._spacer()
		#self.configlist.append(getConfigListEntry("MP-EPG-IMPORTER", ))
		#self._separator()
		#self.configlist.append(getConfigListEntry(_("Enable import:"), config_mp.mediaportal.epg_enabled, True))
		#if config_mp.mediaportal.epg_enabled.value:
		#	self.configlist.append(getConfigListEntry(_("Automatic start time:"), config_mp.mediaportal.epg_wakeup, False))
		#	self.configlist.append(getConfigListEntry(_("Standby at startup:"), config_mp.mediaportal.epg_wakeupsleep, False))
		#	self.configlist.append(getConfigListEntry(_("When in deep standby:"), config_mp.mediaportal.epg_deepstandby, False))
		#	self.configlist.append(getConfigListEntry(_("Start import after booting up:"), config_mp.mediaportal.epg_runboot, False))
		self._spacer()
		self.configlist.append(getConfigListEntry("PREMIUMIZE.ME", ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Activate premiumize.me:"), config_mp.mediaportal.premiumize_use, True))
		if config_mp.mediaportal.premiumize_use.value:
			self.configlist.append(getConfigListEntry(_("Customer ID:"), config_mp.mediaportal.premiumize_username, False))
			self.configlist.append(getConfigListEntry(_("PIN:"), config_mp.mediaportal.premiumize_password, False))
			#self.configlist.append(getConfigListEntry(_("Autom. Proxy-Config.-URL:"), config_mp.mediaportal.premiumize_proxy_config_url, False))
		self._spacer()
		self.configlist.append(getConfigListEntry("REAL-DEBRID.COM", ))
		self._separator()
		self.configlist.append(getConfigListEntry(_("Activate Real-Debrid.com:"), config_mp.mediaportal.realdebrid_use, True))
		if config_mp.mediaportal.premiumize_use.value or config_mp.mediaportal.realdebrid_use.value:
			self._spacer()
			self.configlist.append(getConfigListEntry("PREMIUM", ))
			self._separator()
			self.configlist.append(getConfigListEntry(_("Streammarkercolor:"), config_mp.mediaportal.premium_color, False))

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
				for x in root:
					if x.tag == "plugin":
						if x.get("type") == "mod":
							modfile = x.get("modfile")
							gz = x.get("gz")
							if not config_mp.mediaportal.showuseradditions.value and gz == "1":
								pass
							else:
								exec("self."+x.get("confcat")+".append(getConfigListEntry(\""+x.get("name").replace("&amp;","&")+"\", config_mp.mediaportal."+x.get("confopt")+", False))")

		xmlpath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/additions/")
		for file in os.listdir(xmlpath):
			if file.endswith(".xml") and file != "additions.xml":
				useraddition = xmlpath + file

				conf = xml.etree.cElementTree.parse(useraddition)
				for x in conf.getroot():
					if x.tag == "set" and x.get("name") == 'additions_user':
						root =  x
						for x in root:
							if x.tag == "plugin":
								if x.get("type") == "mod":
									try:
										modfile = x.get("modfile")
										gz = x.get("gz")
										if not config_mp.mediaportal.showuseradditions.value and gz == "1":
											pass
										else:
											exec("self."+x.get("confcat")+".append(getConfigListEntry(\""+x.get("name").replace("&amp;","&")+"\", config_mp.mediaportal."+x.get("confopt")+", False))")
									except Exception as e:
										printl(e,self,"E")
		self._spacer()
		self.configlist.append(getConfigListEntry(_("LIBRARIES"), ))
		self._separator()
		self.mediatheken.sort(key=lambda t : t[0].lower())
		for x in self.mediatheken:
			self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		self._spacer()
		self.configlist.append(getConfigListEntry(_("NEWS & DOCUMENTARY"), ))
		self._separator()
		self.newsdoku.sort(key=lambda t : t[0].lower())
		for x in self.newsdoku:
			self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		self._spacer()
		self.configlist.append(getConfigListEntry(_("TECH & FUN"), ))
		self._separator()
		self.fun.sort(key=lambda t : t[0].lower())
		for x in self.fun:
			self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		self._spacer()
		self.configlist.append(getConfigListEntry(_("SPORTS"), ))
		self._separator()
		self.sport.sort(key=lambda t : t[0].lower())
		for x in self.sport:
			self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		self._spacer()
		self.configlist.append(getConfigListEntry(_("MUSIC"), ))
		self._separator()
		self.music.sort(key=lambda t : t[0].lower())
		for x in self.music:
			self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		if config_mp.mediaportal.showporn.value:
			self._spacer()
			self.configlist.append(getConfigListEntry(_("PORN"), ))
			self._separator()
			self.porn.sort(key=lambda t : t[0].lower())
			for x in self.porn:
				self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		test = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/additions/useradditions/")

		if len(os.listdir(test)) > 2:
			if config_mp.mediaportal.showuseradditions.value:
				self._spacer()
				self.configlist.append(getConfigListEntry(_("USER-ADDITIONS"), ))
				self._separator()
				self.useradditions.sort(key=lambda t : t[0].lower())
				for x in self.useradditions:
					self.configlist.append((_("Show ")+x[0]+":",x[1], False))

		self._spacer()
		self.configlist.append(getConfigListEntry("DEBUG", ))
		self._separator()
		self.configlist.append(getConfigListEntry("Debug-Mode:", config_mp.mediaportal.debugMode, False))
		if len(os.listdir(test)) > 2:
			self.configlist.append(getConfigListEntry(_("Activate User-additions:"), config_mp.mediaportal.showuseradditions, False))

		self["config"].list = self.configlist
		self["config"].setList(self.configlist)

	def _onKeyChange(self):
		try:
			cur = self["config"].getCurrent()
			if cur and cur[2]:
				self._getConfig()
		except:
			pass

	def keyOK(self):
		if self["config"].current:
			self["config"].current[1].onDeselect(self.session)
		if config_mp.mediaportal.watchlistpath.value[0] != '/':
			config_mp.mediaportal.watchlistpath.value = '/' + config_mp.mediaportal.watchlistpath.value
		if config_mp.mediaportal.watchlistpath.value[-1] != '/':
			config_mp.mediaportal.watchlistpath.value = config_mp.mediaportal.watchlistpath.value + '/'
		if config_mp.mediaportal.storagepath.value[0] != '/':
			config_mp.mediaportal.storagepath.value = '/' + config_mp.mediaportal.storagepath.value
		if config_mp.mediaportal.storagepath.value[-1] != '/':
			config_mp.mediaportal.storagepath.value = config_mp.mediaportal.storagepath.value + '/'
		if config_mp.mediaportal.storagepath.value[-4:] != 'tmp/':
			config_mp.mediaportal.storagepath.value = config_mp.mediaportal.storagepath.value + 'tmp/'
		if config_mp.mediaportal.iconcachepath.value[0] != '/':
			config_mp.mediaportal.iconcachepath.value = '/' + config_mp.mediaportal.iconcachepath.value
		if config_mp.mediaportal.iconcachepath.value[-1] != '/':
			config_mp.mediaportal.iconcachepath.value = config_mp.mediaportal.iconcachepath.value + '/'
		if (config_mp.mediaportal.showporn.value == False and config_mp.mediaportal.filter.value == 'Porn'):
			config_mp.mediaportal.filter.value = 'ALL'
		if (config_mp.mediaportal.showuseradditions.value == False and config_mp.mediaportal.filter.value == 'User-additions'):
			config_mp.mediaportal.filter.value = 'ALL'

		CheckPathes(self.session).checkPathes(self.cb_checkPathes)

		if (config_mp.mediaportal.showuseradditions.value and not config_mp.mediaportal.pinuseradditions.value):
			self.a = str(random.randint(1,9))
			self.b = str(random.randint(0,9))
			self.c = str(random.randint(0,9))
			self.d = str(random.randint(0,9))
			code = "%s %s %s %s" % (self.a,self.b,self.c,self.d)
			message = _("Some of the plugins may not be legally used in your country!\n\nIf you accept this then enter the following code now:\n\n%s" % (code))
			self.session.openWithCallback(self.keyOK2, MessageBoxExt, message, MessageBoxExt.TYPE_YESNO)
		else:
			if not config_mp.mediaportal.showuseradditions.value:
				config_mp.mediaportal.pinuseradditions.value = False
				config_mp.mediaportal.pinuseradditions.save()
			self.keySave()

	def premium(self):
		if config_mp.mediaportal.realdebrid_use.value:
			if mp_globals.isDreamOS:
				self.session.open(realdebrid_oauth2, None, calltype='user', is_dialog=True)
			else:
				self.session.open(realdebrid_oauth2, None, calltype='user')
		else:
			self.session.open(MessageBoxExt, _("Real-Debrid.com is not activated."), MessageBoxExt.TYPE_ERROR)
		self.premiumize()

	def cb_checkPathes(self):
		pass

	def keyOK2(self, answer):
		if answer is True:
			self.session.openWithCallback(self.validcode, PinInputExt, pinList = [(int(self.a+self.b+self.c+self.d))], triesEntry = config_mp.mediaportal.retries.pincode, title = _("Please enter the correct code"), windowTitle = _("Enter code"))
		else:
			config_mp.mediaportal.showuseradditions.value = False
			config_mp.mediaportal.showuseradditions.save()
			config_mp.mediaportal.pinuseradditions.value = False
			config_mp.mediaportal.pinuseradditions.save()
			self.keySave()

	def validcode(self, code):
		if code:
			config_mp.mediaportal.pinuseradditions.value = True
			config_mp.mediaportal.pinuseradditions.save()
			self.keySave()
		else:
			config_mp.mediaportal.showuseradditions.value = False
			config_mp.mediaportal.showuseradditions.save()
			config_mp.mediaportal.pinuseradditions.value = False
			config_mp.mediaportal.pinuseradditions.save()
			self.keySave()

	def createSummary(self):
		return MPSummary

class MPList(Screen, HelpableScreen):

	def __init__(self, session, lastservice):
		self.lastservice = mp_globals.lastservice = lastservice

		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		path = "%s/%s/MP_List.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/MP_List.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)

		Screen.__init__(self, session)

		addFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal1.ttf", "mediaportal", 100, False)

		if config_mp.mediaportal.backgroundtv.value:
			config_mp.mediaportal.minitv.value = True
			config_mp.mediaportal.minitv.save()
			config_mp.mediaportal.restorelastservice.value = "2"
			config_mp.mediaportal.restorelastservice.save()
			configfile_mp.save()
			session.nav.stopService()
			session.nav.playService(lastservice)
			session.nav.stopService()

		self["actions"] = ActionMap(["MP_Actions"], {
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"info"  : self.showPorn,
			"0": boundFunction(self.gotFilter, (_('ALL'),"all")),
			"1": boundFunction(self.gotFilter, (_('Libraries'),"mediatheken")),
			"2": boundFunction(self.gotFilter, (_('Tech & Fun'),"fun")),
			"3": boundFunction(self.gotFilter, (_('Music'),"music")),
			"4": boundFunction(self.gotFilter, (_('Sports'),"sport")),
			"5": boundFunction(self.gotFilter, (_('News & Documentary'),"newsdoku")),
			"6": boundFunction(self.gotFilter, (_('Porn'),"porn")),
			"7": boundFunction(self.gotFilter, (_('User-additions'),"useradditions"))
		}, -1)
		self["MP_Actions"] = HelpableActionMap(self, "MP_Actions", {
			"blue"  : (self.startChoose, _("Change filter")),
			"red"   : (self.keySimpleList, _("Open SimpleList")),
			"ok"    : (self.keyOK, _("Open selected Plugin")),
			"cancel": (self.keyCancel, _("Exit MediaPortal")),
			"menu" : (self.keySetup, _("MediaPortal Setup")),
		}, -1)

		self['title'] = Label("MediaPortal")
		self['version'] = Label(config_mp.mediaportal.version.value[0:8])

		self['name'] = Label("")

		self['F1'] = Label("SimpleList")
		self['F2'] = Label("")
		self['F3'] = Label("")
		self['F4'] = Label("")
		self['Exit'] = Label(_("Exit"))
		self['Help'] = Label(_("Help"))
		self['Menu'] = Label(_("Menu"))

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.ml.l.setFont(0, gFont(mp_globals.font, mp_globals.fontsize + 2 * mp_globals.sizefactor))
		if mp_globals.videomode == 2:
			self.ml.l.setItemHeight(96)
		else:
			self.ml.l.setItemHeight(62)
		self['liste'] = self.ml

		self.picload = ePicLoad()

		HelpableScreen.__init__(self)
		self.onLayoutFinish.append(self.layoutFinished)
		self.onFirstExecBegin.append(self.checkPathes)
		self.onFirstExecBegin.append(self.status)
		self.onFirstExecBegin.append(self.loadDisplayCover)

	def loadDisplayCover(self):
		self.summaries.updateCover('file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/default_cover.png')

	def layoutFinished(self):
		_hosters()

		self.icon_url = getIconUrl()
		icons_hashes = grabpage(self.icon_url+"icons/hashes")
		if icons_hashes:
			self.icons_data = re.findall('(.*?)\s\*(.*?\.png)', icons_hashes)
		else:
			self.icons_data = None

		logo_hashes = grabpage(self.icon_url+"logos/hashes")
		if logo_hashes:
			self.logo_data = re.findall('(.*?)\s\*(.*?\.png)', logo_hashes)
		else:
			self.logo_data = None

		if not mp_globals.start:
			self.close(self.session, True, self.lastservice)
		if config_mp.mediaportal.autoupdate.value:
			checkupdate(self.session).checkforupdate()

		self.all = []
		self.mediatheken = []
		self.fun = []
		self.music = []
		self.sport = []
		self.newsdoku = []
		self.porn = []
		self.useradditions = []

		self.cats = ['mediatheken','fun','music','sport','newsdoku','porn','useradditions']

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
				for x in root:
					if x.tag == "plugin":
						if x.get("type") == "mod":
							modfile = x.get("modfile")
							confcat = x.get("confcat")
							if not config_mp.mediaportal.showporn.value and confcat == "porn":
								pass
							else:
								gz = x.get("gz")
								if not config_mp.mediaportal.showuseradditions.value and gz == "1":
									pass
								else:
									mod = eval("config_mp.mediaportal." + x.get("confopt") + ".value")
									if mod:
										filter = x.get("filter")
										#check auf mehrere filter
										if re.search('/', filter):
											mfilter_raw = re.split('/', filter)
											for mfilter in mfilter_raw:
												if mfilter == "Mediathek":
													xfilter = "mediatheken"
												elif mfilter == "User-additions":
													xfilter = "useradditions"
												elif mfilter == "Fun":
													xfilter = "fun"
												elif mfilter == "NewsDoku":
													xfilter = "newsdoku"
												elif mfilter == "Sport":
													xfilter = "sport"
												elif mfilter == "Music":
													xfilter = "music"
												elif mfilter == "Porn":
													xfilter = "porn"
												exec("self."+xfilter+".append(self.hauptListEntry(\""+x.get("name").replace("&amp;","&")+"\", \""+x.get("icon")+"\", \""+x.get("modfile")+"\"))")
										else:
											exec("self."+x.get("confcat")+".append(self.hauptListEntry(\""+x.get("name").replace("&amp;","&")+"\", \""+x.get("icon")+"\", \""+x.get("modfile")+"\"))")
										exec("self.all.append(self.hauptListEntry(\""+x.get("name").replace("&amp;","&")+"\", \""+x.get("icon")+"\", \""+x.get("modfile")+"\"))")

		xmlpath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/additions/")
		for file in os.listdir(xmlpath):
			if file.endswith(".xml") and file != "additions.xml":
				useraddition = xmlpath + file

				conf = xml.etree.cElementTree.parse(useraddition)
				for x in conf.getroot():
					if x.tag == "set" and x.get("name") == 'additions_user':
						root =  x
						for x in root:
							if x.tag == "plugin":
								if x.get("type") == "mod":
									modfile = x.get("modfile")
									confcat = x.get("confcat")
									if not config_mp.mediaportal.showporn.value and confcat == "porn":
										pass
									else:
										gz = x.get("gz")
										if not config_mp.mediaportal.showuseradditions.value and gz == "1":
											pass
										else:
											mod = eval("config_mp.mediaportal." + x.get("confopt") + ".value")
											if mod:
												filter = x.get("filter")
												#check auf mehrere filter
												if re.search('/', filter):
													mfilter_raw = re.split('/', filter)
													for mfilter in mfilter_raw:
														if mfilter == "Mediathek":
															xfilter = "mediatheken"
														elif mfilter == "User-additions":
															xfilter = "useradditions"
														elif mfilter == "Fun":
															xfilter = "fun"
														elif mfilter == "NewsDoku":
															xfilter = "newsdoku"
														elif mfilter == "Sport":
															xfilter = "sport"
														elif mfilter == "Music":
															xfilter = "music"
														elif mfilter == "Porn":
															xfilter = "porn"
														exec("self."+xfilter+".append(self.hauptListEntry(\""+x.get("name").replace("&amp;","&")+"\", \""+x.get("icon")+"\", \""+x.get("modfile")+"\"))")
												else:
													exec("self."+x.get("confcat")+".append(self.hauptListEntry(\""+x.get("name").replace("&amp;","&")+"\", \""+x.get("icon")+"\", \""+x.get("modfile")+"\"))")
												exec("self.all.append(self.hauptListEntry(\""+x.get("name").replace("&amp;","&")+"\", \""+x.get("icon")+"\", \""+x.get("modfile")+"\"))")

		self.all.sort(key=lambda t : t[0][0].lower())
		self.mediatheken.sort(key=lambda t : t[0][0].lower())
		self.fun.sort(key=lambda t : t[0][0].lower())
		self.music.sort(key=lambda t : t[0][0].lower())
		self.sport.sort(key=lambda t : t[0][0].lower())
		self.newsdoku.sort(key=lambda t : t[0][0].lower())
		self.porn.sort(key=lambda t : t[0][0].lower())
		self.useradditions.sort(key=lambda t : t[0][0].lower())

		self.cat = 0

		if config_mp.mediaportal.filter.value == "ALL":
			name = _("ALL")
		elif config_mp.mediaportal.filter.value == "Mediathek":
			name = _("Libraries")
		elif config_mp.mediaportal.filter.value == "User-additions":
			name = _("User-additions")
		elif config_mp.mediaportal.filter.value == "Fun":
			name = _("Tech & Fun")
		elif config_mp.mediaportal.filter.value == "NewsDoku":
			name = _("News & Documentary")
		elif config_mp.mediaportal.filter.value == "Music":
			name = _("Music")
		elif config_mp.mediaportal.filter.value == "Sport":
			name = _("Sports")
		elif config_mp.mediaportal.filter.value == "Porn":
			name = _("Porn")
		self['F4'].setText(name)

		filter = config_mp.mediaportal.filter.value
		if filter == "ALL":
			xfilter = "all"
		elif filter == "Mediathek":
			xfilter = "mediatheken"
		elif filter == "User-additions":
			xfilter = "useradditions"
		elif filter == "Fun":
			xfilter = "fun"
		elif filter == "NewsDoku":
			xfilter = "newsdoku"
		elif filter == "Sport":
			xfilter = "sport"
		elif filter == "Music":
			xfilter = "music"
		elif filter == "Porn":
			xfilter = "porn"

		exec("self.currentlist = self."+xfilter)
		if len(self.currentlist) == 0:
			self.chFilter()
			config_mp.mediaportal.filter.save()
			configfile_mp.save()
			self.close(self.session, False, self.lastservice)
		else:
			exec("self.ml.setList(self."+xfilter+")")
			auswahl = self['liste'].getCurrent()[0][0]
			self['name'].setText(auswahl)

	def chFilter(self):
		if config_mp.mediaportal.filter.value == "ALL":
			config_mp.mediaportal.filter.value = "Mediathek"
		elif config_mp.mediaportal.filter.value == "Mediathek":
			config_mp.mediaportal.filter.value = "Fun"
		elif config_mp.mediaportal.filter.value == "Fun":
			config_mp.mediaportal.filter.value = "Music"
		elif config_mp.mediaportal.filter.value == "Music":
			config_mp.mediaportal.filter.value = "Sport"
		elif config_mp.mediaportal.filter.value == "Sport":
			config_mp.mediaportal.filter.value = "NewsDoku"
		elif config_mp.mediaportal.filter.value == "NewsDoku":
			config_mp.mediaportal.filter.value = "Porn"
		elif config_mp.mediaportal.filter.value == "Porn":
			config_mp.mediaportal.filter.value = "User-additions"
		elif config_mp.mediaportal.filter.value == "User-additions":
			config_mp.mediaportal.filter.value = "ALL"
		else:
			config_mp.mediaportal.filter.value = "ALL"

	def checkPathes(self):
		CheckPathes(self.session).checkPathes(self.cb_checkPathes)

	def cb_checkPathes(self):
		self.session.openWithCallback(self.restart, MPSetup)

	def status(self):
		update_agent = getUserAgent()
		update_url = getUpdateUrl()
		twAgentGetPage(update_url, agent=update_agent, timeout=30).addCallback(self.checkstatus)

	def checkstatus(self, html):
		if re.search(".*?<html", html):
			return
		self.html = html
		tmp_infolines = html.splitlines()
		statusurl = tmp_infolines[4]
		update_agent = getUserAgent()
		twAgentGetPage(statusurl, agent=update_agent, timeout=30).addCallback(_status)

	def hauptListEntry(self, name, icon, modfile=None):
		res = [(name, icon, modfile)]
		poster_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "icons", icon)
		url = self.icon_url+"icons/" + icon + ".png"
		remote_hash = ""
		ds = defer.DeferredSemaphore(tokens=5)
		if not fileExists(poster_path):
			if self.icons_data:
				for x,y in self.icons_data:
					if y == icon+'.png':
						d = ds.run(downloadPage, url, poster_path)
			poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath
		else:
			if self.icons_data:
				for x,y in self.icons_data:
					if y == icon+'.png':
						remote_hash = x
						local_hash = hashlib.md5(open(poster_path, 'rb').read()).hexdigest()
						if remote_hash != local_hash:
							d = ds.run(downloadPage, url, poster_path)
							poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath

		logo_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "logos", icon)
		url = self.icon_url+"logos/" + icon + ".png"
		if not fileExists(logo_path):
			if self.logo_data:
				for x,y in self.logo_data:
					if y == icon+'.png':
						d = ds.run(downloadPage, url, logo_path)
		else:
			if self.logo_data:
				for x,y in self.logo_data:
					if y == icon+'.png':
						remote_hash = x
						local_hash = hashlib.md5(open(logo_path, 'rb').read()).hexdigest()
						if remote_hash != local_hash:
							d = ds.run(downloadPage, url, logo_path)

		scale = AVSwitch().getFramebufferScale()
		if mp_globals.videomode == 2:
			self.picload.setPara((169, 90, scale[0], scale[1], False, 1, "#FF000000"))
		else:
			self.picload.setPara((109, 58, scale[0], scale[1], False, 1, "#FF000000"))
		if mp_globals.isDreamOS:
			self.picload.startDecode(poster_path, False)
		else:
			self.picload.startDecode(poster_path, 0, 0, False)
		pngthumb = self.picload.getData()
		if mp_globals.videomode == 2:
			res.append(MultiContentEntryPixmapAlphaBlend(pos=(0, 3), size=(169, 90), png=pngthumb))
			res.append(MultiContentEntryText(pos=(180, 0), size=(960, 96), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
		else:
			res.append(MultiContentEntryPixmapAlphaBlend(pos=(0, 2), size=(109, 58), png=pngthumb))
			res.append(MultiContentEntryText(pos=(117, 0), size=(640, 62), font=0, text=name, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
		return res

	def showPorn(self):
		if config_mp.mediaportal.showporn.value:
			config_mp.mediaportal.showporn.value = False
			if config_mp.mediaportal.filter.value == "Porn":
				config_mp.mediaportal.filter.value = "ALL"
			config_mp.mediaportal.showporn.save()
			config_mp.mediaportal.filter.save()
			configfile_mp.save()
			self.restart()
		else:
			self.session.openWithCallback(self.showPornOK, PinInputExt, pinList = [(config_mp.mediaportal.adultpincode.value)], triesEntry = config_mp.mediaportal.retries.adultpin, title = _("Please enter the correct PIN"), windowTitle = _("Enter adult PIN"))

	def showPornOK(self, pincode):
		if pincode:
			pincheck.pinEntered()
			config_mp.mediaportal.filter.value = "Porn"
			config_mp.mediaportal.filter.save()
			config_mp.mediaportal.showporn.value = True
			config_mp.mediaportal.showporn.save()
			configfile_mp.save()
			self.restart()

	def keySetup(self):
		if config_mp.mediaportal.setuppin.value:
			self.session.openWithCallback(self.pinok, PinInputExt, pinList = [(config_mp.mediaportal.pincode.value)], triesEntry = config_mp.mediaportal.retries.pincode, title = _("Please enter the correct PIN"), windowTitle = _("Enter setup PIN"))
		else:
			self.session.openWithCallback(self.restart, MPSetup)

	def keySimpleList(self):
		mp_globals.activeIcon = "simplelist"
		self.session.open(simplelistGenreScreen)

	def pinok(self, pincode):
		if pincode:
			self.session.openWithCallback(self.restart, MPSetup)

	def keyUp(self):
		exist = self['liste'].getCurrent()
		if exist == None:
			return
		self['liste'].up()
		auswahl = self['liste'].getCurrent()[0][0]
		self['name'].setText(auswahl)

	def keyDown(self):
		exist = self['liste'].getCurrent()
		if exist == None:
			return
		self['liste'].down()
		auswahl = self['liste'].getCurrent()[0][0]
		self['name'].setText(auswahl)

	def keyLeft(self):
		self['liste'].pageUp()
		auswahl = self['liste'].getCurrent()[0][0]
		self['name'].setText(auswahl)

	def keyRight(self):
		self['liste'].pageDown()
		auswahl = self['liste'].getCurrent()[0][0]
		self['name'].setText(auswahl)

	def keyOK(self):
		if not testWebConnection():
			self.session.open(MessageBoxExt, _('No connection to the Internet available.'), MessageBoxExt.TYPE_INFO, timeout=3)
			return

		exist = self['liste'].getCurrent()
		if exist == None:
			return
		auswahl = self['liste'].getCurrent()[0][0]
		icon = self['liste'].getCurrent()[0][1]
		mp_globals.activeIcon = icon

		self.pornscreen = None
		self.par1 = ""
		self.par2 = ""

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
				for x in root:
					if x.tag == "plugin":
						if x.get("type") == "mod":
							confcat = x.get("confcat")
							if auswahl ==  x.get("name").replace("&amp;","&"):
								status = [item for item in mp_globals.status if item[0] == x.get("modfile")]
								if status:
									if int(config_mp.mediaportal.version.value) < int(status[0][1]):
										if status[0][1] == "9999":
											self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"\n\nIf someone else is willing to provide a fix for this Plugin then please get in contact with us.") % status[0][2], MessageBoxExt.TYPE_INFO)
										else:
											self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"") % status[0][2], MessageBoxExt.TYPE_INFO)
										return
								param = ""
								param1 = x.get("param1")
								param2 = x.get("param2")
								kids = x.get("kids")
								if param1 != "":
									param = ", \"" + param1 + "\""
									self.par1 = param1
								if param2 != "":
									param = param + ", \"" + param2 + "\""
									self.par2 = param2
								if confcat == "porn":
									exec("self.pornscreen = " + x.get("screen") + "")
								elif kids != "1" and config_mp.mediaportal.kidspin.value:
									exec("self.pornscreen = " + x.get("screen") + "")
								else:
									exec("self.session.open(" + x.get("screen") + param + ")")

		xmlpath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/additions/")
		for file in os.listdir(xmlpath):
			if file.endswith(".xml") and file != "additions.xml":
				useraddition = xmlpath + file

				conf = xml.etree.cElementTree.parse(useraddition)
				for x in conf.getroot():
					if x.tag == "set" and x.get("name") == 'additions_user':
						root =  x
						for x in root:
							if x.tag == "plugin":
								if x.get("type") == "mod":
									confcat = x.get("confcat")
									if auswahl ==  x.get("name").replace("&amp;","&"):
										status = [item for item in mp_globals.status if item[0] == x.get("modfile")]
										if status:
											if int(config_mp.mediaportal.version.value) < int(status[0][1]):
												if status[0][1] == "9999":
													self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"\n\nIf someone else is willing to provide a fix for this Plugin then please get in contact with us.") % status[0][2], MessageBoxExt.TYPE_INFO)
												else:
													self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"") % status[0][2], MessageBoxExt.TYPE_INFO)
												return
										param = ""
										param1 = x.get("param1")
										param2 = x.get("param2")
										kids = x.get("kids")
										if param1 != "":
											param = ", \"" + param1 + "\""
											self.par1 = param1
										if param2 != "":
											param = param + ", \"" + param2 + "\""
											self.par2 = param2
										if confcat == "porn":
											exec("self.pornscreen = " + x.get("screen") + "")
										elif kids != "1" and config_mp.mediaportal.kidspin.value:
											exec("self.pornscreen = " + x.get("screen") + "")
										else:
											exec("self.session.open(" + x.get("screen") + param + ")")

		if self.pornscreen:
			if config_mp.mediaportal.pornpin.value:
				if pincheck.pin_entered == False:
					self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config_mp.mediaportal.adultpincode.value)], triesEntry = config_mp.mediaportal.retries.adultpin, title = _("Please enter the correct PIN"), windowTitle = _("Enter adult PIN"))
				else:
					if self.par1 == "":
						self.session.open(self.pornscreen)
					elif self.par2 == "":
						self.session.open(self.pornscreen, self.par1)
					else:
						self.session.open(self.pornscreen, self.par1, self.par2)
			else:
				if self.par1 == "":
					self.session.open(self.pornscreen)
				elif self.par2 == "":
					self.session.open(self.pornscreen, self.par1)
				else:
					self.session.open(self.pornscreen, self.par1, self.par2)

	def pincheckok(self, pincode):
		if pincode:
			pincheck.pinEntered()
			if self.par1 == "":
				self.session.open(self.pornscreen)
			elif self.par2 == "":
				self.session.open(self.pornscreen, self.par1)
			else:
				self.session.open(self.pornscreen, self.par1, self.par2)

	def keyCancel(self):
		config_mp.mediaportal.filter.save()
		configfile_mp.save()
		self.close(self.session, True, self.lastservice)

	def restart(self):
		config_mp.mediaportal.filter.save()
		configfile_mp.save()
		if autoStartTimer is not None:
			autoStartTimer.update()
		self.close(self.session, False, self.lastservice)

	def startChoose(self):
		if not config_mp.mediaportal.showporn.value:
			xporn = ""
		else:
			xporn = _('Porn')
		if not config_mp.mediaportal.showuseradditions.value:
			useradd = ""
		else:
			useradd = _('User-additions')
		rangelist = [[_('ALL'), 'all'], [_('Libraries'), 'mediatheken'], [_('Tech & Fun'), 'fun'], [_('Music'), 'music'], [_('Sports'), 'sport'], [_('News & Documentary'), 'newsdoku'], [xporn, 'porn'], [useradd, 'useradditions']]
		self.session.openWithCallback(self.gotFilter, ChoiceBoxExt, keys=["0", "1", "2", "3", "4", "5", "6", "7"], title=_('Select Filter'), list = rangelist)

	def gotFilter(self, filter):
		if filter:
			if not config_mp.mediaportal.showporn.value and filter[1] == "porn":
				return
			if not config_mp.mediaportal.showuseradditions.value and filter[1] == "useradditions":
				return
			if filter[0] == "":
				return
			elif filter:
				if filter[1] == "all":
					xfilter = "ALL"
				elif filter[1] == "mediatheken":
					xfilter = "Mediathek"
				elif filter[1] == "useradditions":
					xfilter = "User-additions"
				elif filter[1] == "fun":
					xfilter = "Fun"
				elif filter[1] == "newsdoku":
					xfilter = "NewsDoku"
				elif filter[1] == "sport":
					xfilter = "Sport"
				elif filter[1] == "music":
					xfilter = "Music"
				elif filter[1] == "porn":
					xfilter = "Porn"
				config_mp.mediaportal.filter.value = xfilter
				exec("self.currentlist = self."+filter[1])
				if len(self.currentlist) == 0:
					self.chFilter()
					config_mp.mediaportal.filter.save()
					configfile_mp.save()
					self.close(self.session, False, self.lastservice)
				else:
					exec("self.ml.setList(self."+filter[1]+")")
					self['F4'].setText(filter[0])
					self.ml.moveToIndex(0)
					auswahl = self['liste'].getCurrent()[0][0]
					self['name'].setText(auswahl)

	def createSummary(self):
		return MPSummary

class MPSort(MPScreen):

	def __init__(self, session):
		MPScreen.__init__(self, session, skin='MP_Sort')

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)

		self['title'] = Label(_("Userdefined Plugin sorting"))
		self.list = []
		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self["liste"] = self.ml
		self.selected = False

		self["actions"] = ActionMap(["MP_Actions"], {
			"ok":	self.select,
			"cancel": self.keyCancel
		}, -1)

		self.onLayoutFinish.append(self.readconfig)

	def select(self):
		if not self.selected:
			self.last_newidx = self["liste"].getSelectedIndex()
			self.last_plugin_name = self["liste"].getCurrent()[0][0]
			self.last_plugin_pic = self["liste"].getCurrent()[0][1]
			self.last_plugin_genre = self["liste"].getCurrent()[0][2]
			self.last_plugin_hits = self["liste"].getCurrent()[0][3]
			self.last_plugin_msort = self["liste"].getCurrent()[0][4]
			self.selected = True
			self.readconfig()
		else:
			self.now_newidx = self["liste"].getSelectedIndex()
			self.now_plugin_name = self["liste"].getCurrent()[0][0]
			self.now_plugin_pic = self["liste"].getCurrent()[0][1]
			self.now_plugin_genre = self["liste"].getCurrent()[0][2]
			self.now_plugin_hits = self["liste"].getCurrent()[0][3]
			self.now_plugin_msort = self["liste"].getCurrent()[0][4]

			count_move = 0
			config_tmp = open("/etc/enigma2/mp_pluginliste.tmp" , "w")
			# del element from list
			del self.config_list_select[int(self.last_newidx)];
			# add element to list at the right place
			self.config_list_select.insert(int(self.now_newidx), (self.last_plugin_name, self.last_plugin_pic, self.last_plugin_genre, self.last_plugin_hits, self.now_newidx));

			# liste neu nummerieren
			for (name, pic, genre, hits, msort) in self.config_list_select:
				count_move += 1
				config_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (name, pic, genre, hits, count_move))

			config_tmp.close()
			shutil.move("/etc/enigma2/mp_pluginliste.tmp", "/etc/enigma2/mp_pluginliste")
			self.selected = False
			self.readconfig()

	def readconfig(self):
		config_read = open("/etc/enigma2/mp_pluginliste","r")
		self.config_list = []
		self.config_list_select = []
		for line in config_read.readlines():
			ok = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', line, re.S)
			if ok:
				(name, pic, genre, hits, msort) = ok[0]
				if config_mp.mediaportal.filter.value != "ALL":
					if genre == config_mp.mediaportal.filter.value:
						self.config_list_select.append((name, pic, genre, hits, msort))
						self.config_list.append((name, pic, genre, hits, msort))
				else:
					self.config_list_select.append((name, pic, genre, hits, msort))
					self.config_list.append((name, pic, genre, hits, msort))

		self.config_list.sort(key=lambda x: int(x[4]))
		self.config_list_select.sort(key=lambda x: int(x[4]))
		self.ml.setList(map(self.MPSort, self.config_list))
		config_read.close()

	def keyCancel(self):
		config_mp.mediaportal.sortplugins.value = "user"
		self.close()

class MPWall(Screen, HelpableScreen):

	def __init__(self, session, lastservice, filter):
		self.lastservice = mp_globals.lastservice = lastservice
		self.wallbw = False
		self.wallzoom = False

		self.plugin_liste = []

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
				for x in root:
					if x.tag == "plugin":
						if x.get("type") == "mod":
							modfile = x.get("modfile")
							confcat = x.get("confcat")
							if not config_mp.mediaportal.showporn.value and confcat == "porn":
								pass
							else:
								gz = x.get("gz")
								if not config_mp.mediaportal.showuseradditions.value and gz == "1":
									pass
								else:
									mod = eval("config_mp.mediaportal." + x.get("confopt") + ".value")
									if mod:
										y = eval("self.plugin_liste.append((\"" + x.get("name").replace("&amp;","&") + "\", \"" + x.get("icon") + "\", \"" + x.get("filter") + "\"))")

		xmlpath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/additions/")
		for file in os.listdir(xmlpath):
			if file.endswith(".xml") and file != "additions.xml":
				useraddition = xmlpath + file

				conf = xml.etree.cElementTree.parse(useraddition)
				for x in conf.getroot():
					if x.tag == "set" and x.get("name") == 'additions_user':
						root =  x
						for x in root:
							if x.tag == "plugin":
								if x.get("type") == "mod":
									try:
										modfile = x.get("modfile")
										confcat = x.get("confcat")
										if not config_mp.mediaportal.showporn.value and confcat == "porn":
											pass
										else:
											gz = x.get("gz")
											if not config_mp.mediaportal.showuseradditions.value and gz == "1":
												pass
											else:
												mod = eval("config_mp.mediaportal." + x.get("confopt") + ".value")
												if mod:
													y = eval("self.plugin_liste.append((\"" + x.get("name").replace("&amp;","&") + "\", \"" + x.get("icon") + "\", \"" + x.get("filter") + "\"))")
									except Exception as e:
										printl(e,self,"E")

		if len(self.plugin_liste) == 0:
			self.plugin_liste.append(("","","Mediathek"))

		# Porn
		if (config_mp.mediaportal.showporn.value == False and config_mp.mediaportal.filter.value == 'Porn'):
			config_mp.mediaportal.filter.value = 'ALL'

		# User-additions
		if (config_mp.mediaportal.showuseradditions.value == False and config_mp.mediaportal.filter.value == 'User-additions'):
			config_mp.mediaportal.filter.value = 'ALL'

		# Plugin Sortierung
		if config_mp.mediaportal.sortplugins != "default":

			# Erstelle Pluginliste falls keine vorhanden ist.
			self.sort_plugins_file = "/etc/enigma2/mp_pluginliste"
			if not fileExists(self.sort_plugins_file):
				open(self.sort_plugins_file,"w").close()

			pluginliste_leer = os.path.getsize(self.sort_plugins_file)
			if pluginliste_leer == 0:
				first_count = 0
				read_pluginliste = open(self.sort_plugins_file,"a")
				for name,picname,genre in self.plugin_liste:
					read_pluginliste.write('"%s" "%s" "%s" "%s" "%s"\n' % (name, picname, genre, "0", str(first_count)))
					first_count += 1
				read_pluginliste.close()

			# Lese Pluginliste ein.
			if fileExists(self.sort_plugins_file):
				read_pluginliste_tmp = open(self.sort_plugins_file+".tmp","w")
				read_pluginliste = open(self.sort_plugins_file,"r")
				p_dupeliste = []

				for rawData in read_pluginliste.readlines():
					data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)

					if data:
						(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
						pop_count = 0
						for pname, ppic, pgenre in self.plugin_liste:
							if p_name not in p_dupeliste:
								if p_name == pname:
									read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, pgenre, p_hits, p_sort))
									p_dupeliste.append((p_name))
									self.plugin_liste.pop(int(pop_count))

								pop_count += 1

				if len(self.plugin_liste) != 0:
					for pname, ppic, pgenre in self.plugin_liste:
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (pname, ppic, pgenre, "0", "99"))

				read_pluginliste.close()
				read_pluginliste_tmp.close()
				shutil.move(self.sort_plugins_file+".tmp", self.sort_plugins_file)

				self.new_pluginliste = []
				read_pluginliste = open(self.sort_plugins_file,"r")
				for rawData in read_pluginliste.readlines():
					data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
					if data:
						(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
						self.new_pluginliste.append((p_name, p_picname, p_genre, p_hits, p_sort))
				read_pluginliste.close()

			# Sortieren nach hits
			if config_mp.mediaportal.sortplugins.value == "hits":
				self.new_pluginliste.sort(key=lambda x: int(x[3]))
				self.new_pluginliste.reverse()

			# Sortieren nach abcde..
			elif config_mp.mediaportal.sortplugins.value == "abc":
				self.new_pluginliste.sort(key=lambda x: str(x[0]).lower())

			elif config_mp.mediaportal.sortplugins.value == "user":
				self.new_pluginliste.sort(key=lambda x: int(x[4]))

			self.plugin_liste = self.new_pluginliste

		skincontent = ""

		if config_mp.mediaportal.wallmode.value == "bw":
			self.wallbw = True
		elif config_mp.mediaportal.wallmode.value == "bw_zoom":
			self.wallbw = True
			self.wallzoom = True
		elif config_mp.mediaportal.wallmode.value == "color_zoom":
			self.wallzoom = True

		if mp_globals.videomode == 2:
			screenwidth = 1920
			posxstart = 85
			posxplus = 220
			posystart = 210
			posyplus = 122
			iconsize = "210,112"
			iconsizezoom = "272,146"
			zoomoffsetx = 31
			zoomoffsety = 17
		else:
			screenwidth = 1280
			posxstart = 22
			posxplus = 155
			posystart = 135
			posyplus = 85
			iconsize = "150,80"
			iconsizezoom = "194,104"
			zoomoffsetx = 22
			zoomoffsety = 12
		posx = posxstart
		posy = posystart
		for x in range(1,len(self.plugin_liste)+1):
			skincontent += "<widget name=\"zeile" + str(x) + "\" position=\"" + str(posx) + "," + str(posy) + "\" size=\"" + iconsize + "\" zPosition=\"1\" transparent=\"1\" alphatest=\"blend\" />"
			if self.wallzoom:
				skincontent += "<widget name=\"zeile_bw" + str(x) + "\" position=\"" + str(posx-zoomoffsetx) + "," + str(posy-zoomoffsety) + "\" size=\"" + iconsizezoom + "\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
			elif self.wallbw:
				skincontent += "<widget name=\"zeile_bw" + str(x) + "\" position=\"" + str(posx) + "," + str(posy) + "\" size=\"" + iconsize + "\" zPosition=\"1\" transparent=\"1\" alphatest=\"blend\" />"
			posx += posxplus
			if x in [8, 16, 24, 32, 40, 56, 64, 72, 80, 88, 104, 112, 120, 128, 136, 152, 160, 168, 176, 184, 200, 208, 216, 224, 232]:
				posx = posxstart
				posy += posyplus
			elif x in [48, 96, 144, 192, 240]:
				posx = posxstart
				posy = posystart

		# Page Style
		if config_mp.mediaportal.pagestyle.value == "Graphic":
			self.dump_liste_page_tmp = self.plugin_liste
			if config_mp.mediaportal.filter.value != "ALL":
				self.plugin_liste_page_tmp = []
				self.plugin_liste_page_tmp = [x for x in self.dump_liste_page_tmp if re.search(config_mp.mediaportal.filter.value, x[2])]
			else:
				self.plugin_liste_page_tmp = self.plugin_liste

			if len(self.plugin_liste_page_tmp) != 0:
				self.counting_pages = int(round(float((len(self.plugin_liste_page_tmp)-1) / 48) + 0.5))
				pagebar_size = self.counting_pages * 26 + (self.counting_pages-1) * 4
				start_pagebar = int(screenwidth / 2 - pagebar_size / 2)

				for x in range(1,self.counting_pages+1):
					normal = mp_globals.pagebar_posy
					skincontent += "<widget name=\"page_empty" + str(x) + "\" position=\"" + str(start_pagebar) + "," + str(normal) + "\" size=\"26,26\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
					skincontent += "<widget name=\"page_sel" + str(x) + "\" position=\"" + str(start_pagebar) + "," + str(normal) + "\" size=\"26,26\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
					start_pagebar += 30

		self.skin_dump = ""
		self.skin_dump += skincontent
		self.skin_dump += "</screen>"

		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		self.images_path = "%s/%s/images" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(self.images_path):
			self.images_path = self.skin_path + mp_globals.skinFallback + "/images"

		path = "%s/%s/MP_Wall.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			path = self.skin_path + mp_globals.skinFallback + "/MP_Wall.xml"
		with open(path, "r") as f:
			self.skin_dump2 = f.read()
			self.skin_dump2 += self.skin_dump
			self.skin = self.skin_dump2
			f.close()

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)

		Screen.__init__(self, session)

		addFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal1.ttf", "mediaportal", 100, False)

		if config_mp.mediaportal.backgroundtv.value:
			config_mp.mediaportal.minitv.value = True
			config_mp.mediaportal.minitv.save()
			config_mp.mediaportal.restorelastservice.value = "2"
			config_mp.mediaportal.restorelastservice.save()
			configfile_mp.save()
			session.nav.stopService()
			session.nav.playService(lastservice)
			session.nav.stopService()

		self["actions"] = ActionMap(["MP_Actions"], {
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"info"  : self.showPorn,
			"0": boundFunction(self.gotFilter, (_('ALL'),"all")),
			"1": boundFunction(self.gotFilter, (_('Libraries'),"Mediathek")),
			"2": boundFunction(self.gotFilter, (_('Tech & Fun'),"Fun")),
			"3": boundFunction(self.gotFilter, (_('Music'),"Music")),
			"4": boundFunction(self.gotFilter, (_('Sports'),"Sport")),
			"5": boundFunction(self.gotFilter, (_('News & Documentary'),"NewsDoku")),
			"6": boundFunction(self.gotFilter, (_('Porn'),"Porn")),
			"7": boundFunction(self.gotFilter, (_('User-additions'),"User-additions"))
		}, -1)
		self["MP_Actions"] = HelpableActionMap(self, "MP_Actions", {
			"blue"  : (self.startChoose, _("Change filter")),
			"green" : (self.chSort, _("Change sort order")),
			"yellow": (self.manuelleSortierung, _("Manual sorting")),
			"red"   : (self.keySimpleList, _("Open SimpleList")),
			"ok"    : (self.keyOK, _("Open selected Plugin")),
			"cancel": (self.keyCancel, _("Exit MediaPortal")),
			"nextBouquet" :	(self.page_next, _("Next page")),
			"prevBouquet" :	(self.page_back, _("Previous page")),
			"menu" : (self.keySetup, _("MediaPortal Setup")),
		}, -1)

		self['name'] = Label("")
		self['version'] = Label(config_mp.mediaportal.version.value[0:8])
		self['F1'] = Label("SimpleList")
		self['F2'] = Label("")
		self['F3'] = Label(_("Sort"))
		self['F4'] = Label("")
		self['CH+'] = Label(_("CH+"))
		self['CH-'] = Label(_("CH-"))
		self['Exit'] = Label(_("Exit"))
		self['Help'] = Label(_("Help"))
		self['Menu'] = Label(_("Menu"))
		self['page'] = Label("")

		for x in range(1,len(self.plugin_liste)+1):
			if self.wallbw or self.wallzoom:
				self["zeile"+str(x)] = Pixmap()
				self["zeile"+str(x)].show()
				self["zeile_bw"+str(x)] = Pixmap()
				self["zeile_bw"+str(x)].hide()
			else:
				self["zeile"+str(x)] = Pixmap()
				self["zeile"+str(x)].show()

		# Apple Page Style
		if config_mp.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			for x in range(1,self.counting_pages+1):
				self["page_empty"+str(x)] = Pixmap()
				self["page_empty"+str(x)].show()
				self["page_sel"+str(x)] = Pixmap()
				self["page_sel"+str(x)].show()

		self.selektor_index = 1
		self.select_list = 0
		self.picload = ePicLoad()

		HelpableScreen.__init__(self)
		self.onFirstExecBegin.append(self._onFirstExecBegin)
		self.onFirstExecBegin.append(self.checkPathes)
		self.onFirstExecBegin.append(self.status)
		self.onFirstExecBegin.append(self.loadDisplayCover)

	def loadDisplayCover(self):
		self.summaries.updateCover('file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/default_cover.png')

	def checkPathes(self):
		CheckPathes(self.session).checkPathes(self.cb_checkPathes)

	def cb_checkPathes(self):
		self.session.openWithCallback(self.restart, MPSetup)

	def status(self):
		update_agent = getUserAgent()
		update_url = getUpdateUrl()
		twAgentGetPage(update_url, agent=update_agent, timeout=30).addCallback(self.checkstatus)

	def checkstatus(self, html):
		if re.search(".*?<html", html):
			return
		self.html = html
		tmp_infolines = html.splitlines()
		statusurl = tmp_infolines[4]
		update_agent = getUserAgent()
		twAgentGetPage(statusurl, agent=update_agent, timeout=30).addCallback(_status)

	def manuelleSortierung(self):
		if config_mp.mediaportal.filter.value == 'ALL':
			self.session.openWithCallback(self.restart, MPSort)
		else:
			self.session.open(MessageBoxExt, _('Ordering is only possible with filter "ALL".'), MessageBoxExt.TYPE_INFO, timeout=3)

	def hit_plugin(self, pname):
		if fileExists(self.sort_plugins_file):
			read_pluginliste = open(self.sort_plugins_file,"r")
			read_pluginliste_tmp = open(self.sort_plugins_file+".tmp","w")
			for rawData in read_pluginliste.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
					if pname == p_name:
						new_hits = int(p_hits)+1
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, p_genre, str(new_hits), p_sort))
					else:
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, p_genre, p_hits, p_sort))
			read_pluginliste.close()
			read_pluginliste_tmp.close()
			shutil.move(self.sort_plugins_file+".tmp", self.sort_plugins_file)

	def _onFirstExecBegin(self):
		_hosters()
		if not mp_globals.start:
			self.close(self.session, True, self.lastservice)
		if config_mp.mediaportal.autoupdate.value:
			checkupdate(self.session).checkforupdate()

		if config_mp.mediaportal.filter.value == "ALL":
			name = _("ALL")
		elif config_mp.mediaportal.filter.value == "Mediathek":
			name = _("Libraries")
		elif config_mp.mediaportal.filter.value == "User-additions":
			name = _("User-additions")
		elif config_mp.mediaportal.filter.value == "Fun":
			name = _("Tech & Fun")
		elif config_mp.mediaportal.filter.value == "NewsDoku":
			name = _("News & Documentary")
		elif config_mp.mediaportal.filter.value == "Music":
			name = _("Music")
		elif config_mp.mediaportal.filter.value == "Sport":
			name = _("Sports")
		elif config_mp.mediaportal.filter.value == "Porn":
			name = _("Porn")
		self['F4'].setText(name)
		self.sortplugin = config_mp.mediaportal.sortplugins.value
		if self.sortplugin == "hits":
			self.sortplugin = "Hits"
		elif self.sortplugin == "abc":
			self.sortplugin = "ABC"
		elif self.sortplugin == "user":
			self.sortplugin = "User"
		self['F2'].setText(self.sortplugin)
		self.dump_liste = self.plugin_liste
		if config_mp.mediaportal.filter.value != "ALL":
			self.plugin_liste = []
			self.plugin_liste = [x for x in self.dump_liste if re.search(config_mp.mediaportal.filter.value, x[2])]
		if len(self.plugin_liste) == 0:
			self.chFilter()
			if config_mp.mediaportal.filter.value == "ALL":
				name = _("ALL")
			elif config_mp.mediaportal.filter.value == "Mediathek":
				name = _("Libraries")
			elif config_mp.mediaportal.filter.value == "User-additions":
				name = _("User-additions")
			elif config_mp.mediaportal.filter.value == "Fun":
				name = _("Tech & Fun")
			elif config_mp.mediaportal.filter.value == "NewsDoku":
				name = _("News & Documentary")
			elif config_mp.mediaportal.filter.value == "Music":
				name = _("Music")
			elif config_mp.mediaportal.filter.value == "Sport":
				name = _("Sports")
			elif config_mp.mediaportal.filter.value == "Porn":
				name = _("Porn")
			self['F4'].setText(name)

		if config_mp.mediaportal.sortplugins.value == "hits":
			self.plugin_liste.sort(key=lambda x: int(x[3]))
			self.plugin_liste.reverse()
		elif config_mp.mediaportal.sortplugins.value == "abc":
			self.plugin_liste.sort(key=lambda t : t[0].lower())
		elif config_mp.mediaportal.sortplugins.value == "user":
			self.plugin_liste.sort(key=lambda x: int(x[4]))

		icon_url = getIconUrl()
		if self.wallbw:
			icons_hashes = grabpage(icon_url+"icons_bw/hashes")
		else:
			icons_hashes = grabpage(icon_url+"icons/hashes")
		if icons_hashes:
			icons_data = re.findall('(.*?)\s\*(.*?\.png)', icons_hashes)
		else:
			icons_data = None


		icons_data_zoom = None
		if self.wallzoom:
			icons_hashes_zoom = grabpage(icon_url+"icons/hashes")
			if icons_hashes_zoom:
				icons_data_zoom = re.findall('(.*?)\s\*(.*?\.png)', icons_hashes_zoom)

		logo_hashes = grabpage(icon_url+"logos/hashes")
		if logo_hashes:
			logo_data = re.findall('(.*?)\s\*(.*?\.png)', logo_hashes)
		else:
			logo_data = None

		for x in range(1,len(self.plugin_liste)+1):
			postername = self.plugin_liste[int(x)-1][1]
			remote_hash = ""
			ds = defer.DeferredSemaphore(tokens=5)
			if self.wallbw:
				poster_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "icons_bw", postername)
				url = icon_url+"icons_bw/" + postername + ".png"
				if not fileExists(poster_path):
					if icons_data:
						for a,b in icons_data:
							if b == postername+'.png':
								d = ds.run(downloadPage, url, poster_path)
					poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath
				else:
					if icons_data:
						for a,b in icons_data:
							if b == postername+'.png':
								remote_hash = a
								local_hash = hashlib.md5(open(poster_path, 'rb').read()).hexdigest()
								if remote_hash != local_hash:
									d = ds.run(downloadPage, url, poster_path)
									poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath
			else:
				poster_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "icons", postername)
				url = icon_url+"icons/" + postername + ".png"
				if not fileExists(poster_path):
					if icons_data:
						for a,b in icons_data:
							if b == postername+'.png':
								d = ds.run(downloadPage, url, poster_path)
					poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath
				else:
					if icons_data:
						for a,b in icons_data:
							if b == postername+'.png':
								remote_hash = a
								local_hash = hashlib.md5(open(poster_path, 'rb').read()).hexdigest()
								if remote_hash != local_hash:
									d = ds.run(downloadPage, url, poster_path)
									poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath

			logo_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "logos", postername)
			url = icon_url+"logos/" + postername + ".png"
			if not fileExists(logo_path):
				if logo_data:
					for a,b in logo_data:
						if b == postername+'.png':
							d = ds.run(downloadPage, url, logo_path)
			else:
				if logo_data:
					for a,b in logo_data:
						if b == postername+'.png':
							remote_hash = a
							local_hash = hashlib.md5(open(logo_path, 'rb').read()).hexdigest()
							if remote_hash != local_hash:
								d = ds.run(downloadPage, url, logo_path)

			scale = AVSwitch().getFramebufferScale()
			if mp_globals.videomode == 2:
				self.picload.setPara((210, 112, scale[0], scale[1], False, 1, "#FF000000"))
			else:
				self.picload.setPara((150, 80, scale[0], scale[1], False, 1, "#FF000000"))
			if mp_globals.isDreamOS:
				self.picload.startDecode(poster_path, False)
			else:
				self.picload.startDecode(poster_path, 0, 0, False)

			self["zeile"+str(x)].instance.setPixmap(gPixmapPtr())
			self["zeile"+str(x)].hide()
			pic = self.picload.getData()
			if pic != None:
				self["zeile"+str(x)].instance.setPixmap(pic)
				if x <= 48:
					self["zeile"+str(x)].show()

			if self.wallzoom:
				poster_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "icons", postername)
				url = icon_url+"icons/" + postername + ".png"
				if not fileExists(poster_path):
					if icons_data_zoom:
						for a,b in icons_data_zoom:
							if b == postername+'.png':
								d = ds.run(downloadPage, url, poster_path)
					poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath
				else:
					if icons_data_zoom:
						for a,b in icons_data_zoom:
							if b == postername+'.png':
								remote_hash = a
								local_hash = hashlib.md5(open(poster_path, 'rb').read()).hexdigest()
								if remote_hash != local_hash:
									d = ds.run(downloadPage, url, poster_path)
									poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath

				scale = AVSwitch().getFramebufferScale()
				if mp_globals.videomode == 2:
					self.picload.setPara((272, 146, scale[0], scale[1], False, 1, "#FF000000"))
				else:
					self.picload.setPara((194, 104, scale[0], scale[1], False, 1, "#FF000000"))
				if mp_globals.isDreamOS:
					self.picload.startDecode(poster_path, False)
				else:
					self.picload.startDecode(poster_path, 0, 0, False)

				self["zeile_bw"+str(x)].instance.setPixmap(gPixmapPtr())
				self["zeile_bw"+str(x)].hide()
				pic = self.picload.getData()
				if pic != None:
					self["zeile_bw"+str(x)].instance.setPixmap(pic)
					if x <= 48:
						self["zeile_bw"+str(x)].hide()
			elif self.wallbw:
				poster_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "icons", postername)
				if not fileExists(poster_path):
					poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath

				scale = AVSwitch().getFramebufferScale()
				if mp_globals.videomode == 2:
					self.picload.setPara((210, 112, scale[0], scale[1], False, 1, "#FF000000"))
				else:
					self.picload.setPara((150, 80, scale[0], scale[1], False, 1, "#FF000000"))
				if mp_globals.isDreamOS:
					self.picload.startDecode(poster_path, False)
				else:
					self.picload.startDecode(poster_path, 0, 0, False)

				self["zeile_bw"+str(x)].instance.setPixmap(gPixmapPtr())
				self["zeile_bw"+str(x)].hide()
				pic = self.picload.getData()
				if pic != None:
					self["zeile_bw"+str(x)].instance.setPixmap(pic)
					if x <= 48:
						self["zeile_bw"+str(x)].hide()

		if config_mp.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			for x in range(1,self.counting_pages+1):
				poster_path = "%s/page_select.png" % (self.images_path)
				self["page_sel"+str(x)].instance.setPixmap(gPixmapPtr())
				self["page_sel"+str(x)].hide()
				pic = LoadPixmap(cached=True, path=poster_path)
				if pic != None:
					self["page_sel"+str(x)].instance.setPixmap(pic)
					if x == 1:
						self["page_sel"+str(x)].show()

			for x in range(1,self.counting_pages+1):
				poster_path = "%s/page.png" % (self.images_path)
				self["page_empty"+str(x)].instance.setPixmap(gPixmapPtr())
				self["page_empty"+str(x)].hide()
				pic = LoadPixmap(cached=True, path=poster_path)
				if pic != None:
					self["page_empty"+str(x)].instance.setPixmap(pic)
					if x > 1:
						self["page_empty"+str(x)].show()

		self.widget_list()

	def widget_list(self):
		count = 1
		counting = 1
		self.mainlist = []
		list_dummy = []
		self.plugin_counting = len(self.plugin_liste)

		for x in range(1,int(self.plugin_counting)+1):
			if count == 48:
				count += 1
				counting += 1
				list_dummy.append(x)
				self.mainlist.append(list_dummy)
				count = 1
				list_dummy = []
			else:
				count += 1
				counting += 1
				list_dummy.append(x)
				if int(counting) == int(self.plugin_counting)+1:
					self.mainlist.append(list_dummy)

		if config_mp.mediaportal.pagestyle.value == "Graphic":
			pageinfo = ""
		else:
			pageinfo = _("Page") + " %s / %s" % (self.select_list+1, len(self.mainlist))
		self['page'].setText(pageinfo)
		select_nr = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
		plugin_name = self.plugin_liste[int(select_nr)-1][0]
		self['name'].setText(plugin_name)
		self.hideshow2()

	def move_selector(self):
		select_nr = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
		plugin_name = self.plugin_liste[int(select_nr)-1][0]
		self['name'].setText(plugin_name)

	def keyOK(self):
		if not testWebConnection():
			self.session.open(MessageBoxExt, _('No connection to the Internet available.'), MessageBoxExt.TYPE_INFO, timeout=3)
			return

		if self.check_empty_list():
			return

		select_nr = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
		auswahl = self.plugin_liste[int(select_nr)-1][0]
		icon = self.plugin_liste[int(select_nr)-1][1]
		mp_globals.activeIcon = icon

		self.pornscreen = None
		self.par1 = ""
		self.par2 = ""
		self.hit_plugin(auswahl)

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
				for x in root:
					if x.tag == "plugin":
						if x.get("type") == "mod":
							confcat = x.get("confcat")
							if auswahl ==  x.get("name").replace("&amp;","&"):
								status = [item for item in mp_globals.status if item[0] == x.get("modfile")]
								if status:
									if int(config_mp.mediaportal.version.value) < int(status[0][1]):
										if status[0][1] == "9999":
											self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"\n\nIf someone else is willing to provide a fix for this Plugin then please get in contact with us.") % status[0][2], MessageBoxExt.TYPE_INFO)
										else:
											self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"") % status[0][2], MessageBoxExt.TYPE_INFO)
										return
								param = ""
								param1 = x.get("param1")
								param2 = x.get("param2")
								kids = x.get("kids")
								if param1 != "":
									param = ", \"" + param1 + "\""
									self.par1 = param1
								if param2 != "":
									param = param + ", \"" + param2 + "\""
									self.par2 = param2
								if confcat == "porn":
									exec("self.pornscreen = " + x.get("screen") + "")
								elif kids != "1" and config_mp.mediaportal.kidspin.value:
									exec("self.pornscreen = " + x.get("screen") + "")
								else:
									exec("self.session.open(" + x.get("screen") + param + ")")

		xmlpath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/additions/")
		for file in os.listdir(xmlpath):
			if file.endswith(".xml") and file != "additions.xml":
				useraddition = xmlpath + file

				conf = xml.etree.cElementTree.parse(useraddition)
				for x in conf.getroot():
					if x.tag == "set" and x.get("name") == 'additions_user':
						root =  x
						for x in root:
							if x.tag == "plugin":
								if x.get("type") == "mod":
									confcat = x.get("confcat")
									if auswahl ==  x.get("name").replace("&amp;","&"):
										status = [item for item in mp_globals.status if item[0] == x.get("modfile")]
										if status:
											if int(config_mp.mediaportal.version.value) < int(status[0][1]):
												if status[0][1] == "9999":
													self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"\n\nIf someone else is willing to provide a fix for this Plugin then please get in contact with us.") % status[0][2], MessageBoxExt.TYPE_INFO)
												else:
													self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"") % status[0][2], MessageBoxExt.TYPE_INFO)
												return
										param = ""
										param1 = x.get("param1")
										param2 = x.get("param2")
										kids = x.get("kids")
										if param1 != "":
											param = ", \"" + param1 + "\""
											self.par1 = param1
										if param2 != "":
											param = param + ", \"" + param2 + "\""
											self.par2 = param2
										if confcat == "porn":
											exec("self.pornscreen = " + x.get("screen") + "")
										elif kids != "1" and config_mp.mediaportal.kidspin.value:
											exec("self.pornscreen = " + x.get("screen") + "")
										else:
											exec("self.session.open(" + x.get("screen") + param + ")")

		if self.pornscreen:
			if config_mp.mediaportal.pornpin.value:
				if pincheck.pin_entered == False:
					self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config_mp.mediaportal.adultpincode.value)], triesEntry = config_mp.mediaportal.retries.adultpin, title = _("Please enter the correct PIN"), windowTitle = _("Enter adult PIN"))
				else:
					if self.par1 == "":
						self.session.open(self.pornscreen)
					elif self.par2 == "":
						self.session.open(self.pornscreen, self.par1)
					else:
						self.session.open(self.pornscreen, self.par1, self.par2)
			else:
				if self.par1 == "":
					self.session.open(self.pornscreen)
				elif self.par2 == "":
					self.session.open(self.pornscreen, self.par1)
				else:
					self.session.open(self.pornscreen, self.par1, self.par2)

	def pincheckok(self, pincode):
		if pincode:
			pincheck.pinEntered()
			if self.par1 == "":
				self.session.open(self.pornscreen)
			elif self.par2 == "":
				self.session.open(self.pornscreen, self.par1)
			else:
				self.session.open(self.pornscreen, self.par1, self.par2)

	def hideshow(self):
		if self.wallbw or self.wallzoom:
			test = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
			self["zeile_bw"+str(test)].hide()
			self["zeile"+str(test)].show()

	def hideshow2(self):
		if self.wallbw or self.wallzoom:
			test = self.mainlist[int(self.select_list)][int(self.selektor_index)-1]
			self["zeile_bw"+str(test)].show()
			self["zeile"+str(test)].hide()

	def keyLeft(self):
		if self.check_empty_list():
			return
		if self.selektor_index > 1:
			self.hideshow()
			self.selektor_index -= 1
			self.move_selector()
			self.hideshow2()
		else:
			self.page_back()

	def keyRight(self):
		if self.check_empty_list():
			return
		if self.selektor_index < 48 and self.selektor_index != len(self.mainlist[int(self.select_list)]):
			self.hideshow()
			self.selektor_index += 1
			self.move_selector()
			self.hideshow2()
		else:
			self.page_next()

	def keyUp(self):
		if self.check_empty_list():
			return
		if self.selektor_index-8 > 1:
			self.hideshow()
			self.selektor_index -= 8
			self.move_selector()
			self.hideshow2()
		else:
			self.hideshow()
			self.selektor_index = 1
			self.move_selector()
			self.hideshow2()

	def keyDown(self):
		if self.check_empty_list():
			return
		if self.selektor_index+8 <= len(self.mainlist[int(self.select_list)]):
			self.hideshow()
			self.selektor_index += 8
			self.move_selector()
			self.hideshow2()
		else:
			self.hideshow()
			self.selektor_index = len(self.mainlist[int(self.select_list)])
			self.move_selector()
			self.hideshow2()

	def page_next(self):
		if self.check_empty_list():
			return
		if self.select_list < len(self.mainlist)-1:
			self.hideshow()
			self.paint_hide()
			self.select_list += 1
			self.paint_new()

	def page_back(self):
		if self.check_empty_list():
			return
		if self.select_list > 0:
			self.hideshow()
			self.paint_hide()
			self.select_list -= 1
			self.paint_new_last()

	def check_empty_list(self):
		if len(self.plugin_liste) == 0:
			self['name'].setText('Keine Plugins der Kategorie %s aktiviert!' % config_mp.mediaportal.filter.value)
			return True
		else:
			return False

	def paint_hide(self):
		for x in self.mainlist[int(self.select_list)]:
			self["zeile"+str(x)].hide()

	def paint_new_last(self):
		if config_mp.mediaportal.pagestyle.value == "Graphic":
			pageinfo = ""
		else:
			pageinfo = _("Page") + " %s / %s" % (self.select_list+1, len(self.mainlist))
		self['page'].setText(pageinfo)
		self.selektor_index = len(self.mainlist[int(self.select_list)])
		self.move_selector()
		# Apple Page Style
		if config_mp.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			self.refresh_apple_page_bar()

		for x in self.mainlist[int(self.select_list)]:
			self["zeile"+str(x)].show()

		self.hideshow2()

	def paint_new(self):
		if config_mp.mediaportal.pagestyle.value == "Graphic":
			pageinfo = ""
		else:
			pageinfo = _("Page") + " %s / %s" % (self.select_list+1, len(self.mainlist))
		self['page'].setText(pageinfo)
		self.selektor_index = 1
		self.move_selector()
		# Apple Page Style
		if config_mp.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			self.refresh_apple_page_bar()

		for x in self.mainlist[int(self.select_list)]:
			self["zeile"+str(x)].show()

		self.hideshow2()

	# Apple Page Style
	def refresh_apple_page_bar(self):
		for x in range(1,len(self.mainlist)+1):
			if x == self.select_list+1:
				self["page_empty"+str(x)].hide()
				self["page_sel"+str(x)].show()
			else:
				self["page_sel"+str(x)].hide()
				self["page_empty"+str(x)].show()

	def keySetup(self):
		if config_mp.mediaportal.setuppin.value:
			self.session.openWithCallback(self.pinok, PinInputExt, pinList = [(config_mp.mediaportal.pincode.value)], triesEntry = config_mp.mediaportal.retries.pincode, title = _("Please enter the correct PIN"), windowTitle = _("Enter setup PIN"))
		else:
			self.session.openWithCallback(self.restart, MPSetup)

	def keySimpleList(self):
		mp_globals.activeIcon = "simplelist"
		self.session.open(simplelistGenreScreen)

	def pinok(self, pincode):
		if pincode:
			self.session.openWithCallback(self.restart, MPSetup)

	def chSort(self):
		if config_mp.mediaportal.sortplugins.value == "hits":
			config_mp.mediaportal.sortplugins.value = "abc"
		elif config_mp.mediaportal.sortplugins.value == "abc":
			config_mp.mediaportal.sortplugins.value = "user"
		elif config_mp.mediaportal.sortplugins.value == "user":
			config_mp.mediaportal.sortplugins.value = "hits"
		self.restart()

	def chFilter(self):
		if config_mp.mediaportal.filter.value == "ALL":
			config_mp.mediaportal.filter.value = "Mediathek"
		elif config_mp.mediaportal.filter.value == "Mediathek":
			config_mp.mediaportal.filter.value = "Fun"
		elif config_mp.mediaportal.filter.value == "Fun":
			config_mp.mediaportal.filter.value = "Music"
		elif config_mp.mediaportal.filter.value == "Music":
			config_mp.mediaportal.filter.value = "Sport"
		elif config_mp.mediaportal.filter.value == "Sport":
			config_mp.mediaportal.filter.value = "NewsDoku"
		elif config_mp.mediaportal.filter.value == "NewsDoku":
			config_mp.mediaportal.filter.value = "Porn"
		elif config_mp.mediaportal.filter.value == "Porn":
			config_mp.mediaportal.filter.value = "User-additions"
		elif config_mp.mediaportal.filter.value == "User-additions":
			config_mp.mediaportal.filter.value = "ALL"
		else:
			config_mp.mediaportal.filter.value = "ALL"
		self.restartAndCheck()

	def restartAndCheck(self):
		if config_mp.mediaportal.filter.value != "ALL":
			dump_liste2 = self.dump_liste
			self.plugin_liste = []
			self.plugin_liste = [x for x in dump_liste2 if re.search(config_mp.mediaportal.filter.value, x[2])]
			if len(self.plugin_liste) == 0:
				self.chFilter()
			else:
				config_mp.mediaportal.filter.save()
				configfile_mp.save()
				self.close(self.session, False, self.lastservice)
		else:
			config_mp.mediaportal.filter.save()
			configfile_mp.save()
			self.close(self.session, False, self.lastservice)

	def showPorn(self):
		if config_mp.mediaportal.showporn.value:
			config_mp.mediaportal.showporn.value = False
			if config_mp.mediaportal.filter.value == "Porn":
				config_mp.mediaportal.filter.value = "ALL"
			config_mp.mediaportal.showporn.save()
			config_mp.mediaportal.filter.save()
			configfile_mp.save()
			self.restart()
		else:
			self.session.openWithCallback(self.showPornOK, PinInputExt, pinList = [(config_mp.mediaportal.adultpincode.value)], triesEntry = config_mp.mediaportal.retries.adultpin, title = _("Please enter the correct PIN"), windowTitle = _("Enter adult PIN"))

	def showPornOK(self, pincode):
		if pincode:
			pincheck.pinEntered()
			config_mp.mediaportal.filter.value = "Porn"
			config_mp.mediaportal.filter.save()
			config_mp.mediaportal.showporn.value = True
			config_mp.mediaportal.showporn.save()
			configfile_mp.save()
			self.restart()

	def keyCancel(self):
		config_mp.mediaportal.filter.save()
		configfile_mp.save()
		self.close(self.session, True, self.lastservice)

	def restart(self):
		config_mp.mediaportal.filter.save()
		config_mp.mediaportal.sortplugins.save()
		configfile_mp.save()
		if autoStartTimer is not None:
			autoStartTimer.update()
		self.close(self.session, False, self.lastservice)

	def startChoose(self):
		if not config_mp.mediaportal.showporn.value:
			xporn = ""
		else:
			xporn = _('Porn')
		if not config_mp.mediaportal.showuseradditions.value:
			useradd = ""
		else:
			useradd = _('User-additions')
		rangelist = [[_('ALL'), 'all'], [_('Libraries'), 'Mediathek'], [_('Tech & Fun'), 'Fun'], [_('Music'), 'Music'], [_('Sports'), 'Sport'], [_('News & Documentary'), 'NewsDoku'], [xporn, 'Porn'], [useradd, 'User-additions']]
		self.session.openWithCallback(self.gotFilter, ChoiceBoxExt, keys=["0", "1", "2", "3", "4", "5", "6", "7"], title=_('Select Filter'), list = rangelist)

	def gotFilter(self, filter):
		if filter:
			if not config_mp.mediaportal.showporn.value and filter[1] == "Porn":
				return
			if not config_mp.mediaportal.showuseradditions.value and filter[1] == "User-additions":
				return
			if filter[0] == "":
				return
			elif filter:
				config_mp.mediaportal.filter.value = filter[1]
				self.restartAndCheck()

	def createSummary(self):
		return MPSummary

class MPWall2(Screen, HelpableScreen):

	def __init__(self, session, lastservice, filter):
		self.lastservice = mp_globals.lastservice = lastservice
		self.wallbw = False
		self.plugin_liste = []
		self.skin_path = mp_globals.pluginPath + mp_globals.skinsPath

		self.images_path = "%s/%s/images" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(self.images_path):
			self.images_path = self.skin_path + mp_globals.skinFallback + "/images"

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
				for x in root:
					if x.tag == "plugin":
						if x.get("type") == "mod":
							modfile = x.get("modfile")
							confcat = x.get("confcat")
							if not config_mp.mediaportal.showporn.value and confcat == "porn":
								pass
							else:
								gz = x.get("gz")
								if not config_mp.mediaportal.showuseradditions.value and gz == "1":
									pass
								else:
									mod = eval("config_mp.mediaportal." + x.get("confopt") + ".value")
									if mod:
										y = eval("self.plugin_liste.append((\"" + x.get("name").replace("&amp;","&") + "\", \"" + x.get("icon") + "\", \"" + x.get("filter") + "\"))")

		xmlpath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/additions/")
		for file in os.listdir(xmlpath):
			if file.endswith(".xml") and file != "additions.xml":
				useraddition = xmlpath + file

				conf = xml.etree.cElementTree.parse(useraddition)
				for x in conf.getroot():
					if x.tag == "set" and x.get("name") == 'additions_user':
						root =  x
						for x in root:
							if x.tag == "plugin":
								if x.get("type") == "mod":
									try:
										modfile = x.get("modfile")
										confcat = x.get("confcat")
										if not config_mp.mediaportal.showporn.value and confcat == "porn":
											pass
										else:
											gz = x.get("gz")
											if not config_mp.mediaportal.showuseradditions.value and gz == "1":
												pass
											else:
												mod = eval("config_mp.mediaportal." + x.get("confopt") + ".value")
												if mod:
													y = eval("self.plugin_liste.append((\"" + x.get("name").replace("&amp;","&") + "\", \"" + x.get("icon") + "\", \"" + x.get("filter") + "\"))")
									except Exception as e:
										printl(e,self,"E")

		if len(self.plugin_liste) == 0:
			self.plugin_liste.append(("","","Mediathek"))

		# Porn
		if (config_mp.mediaportal.showporn.value == False and config_mp.mediaportal.filter.value == 'Porn'):
			config_mp.mediaportal.filter.value = 'ALL'

		# User-additions
		if (config_mp.mediaportal.showuseradditions.value == False and config_mp.mediaportal.filter.value == 'User-additions'):
			config_mp.mediaportal.filter.value = 'ALL'

		# Plugin Sortierung
		if config_mp.mediaportal.sortplugins != "default":

			# Erstelle Pluginliste falls keine vorhanden ist.
			self.sort_plugins_file = "/etc/enigma2/mp_pluginliste"
			if not fileExists(self.sort_plugins_file):
				open(self.sort_plugins_file,"w").close()

			pluginliste_leer = os.path.getsize(self.sort_plugins_file)
			if pluginliste_leer == 0:
				first_count = 0
				read_pluginliste = open(self.sort_plugins_file,"a")
				for name,picname,genre in self.plugin_liste:
					read_pluginliste.write('"%s" "%s" "%s" "%s" "%s"\n' % (name, picname, genre, "0", str(first_count)))
					first_count += 1
				read_pluginliste.close()

			# Lese Pluginliste ein.
			if fileExists(self.sort_plugins_file):
				read_pluginliste_tmp = open(self.sort_plugins_file+".tmp","w")
				read_pluginliste = open(self.sort_plugins_file,"r")
				p_dupeliste = []

				for rawData in read_pluginliste.readlines():
					data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)

					if data:
						(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
						pop_count = 0
						for pname, ppic, pgenre in self.plugin_liste:
							if p_name not in p_dupeliste:
								if p_name == pname:
									read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, pgenre, p_hits, p_sort))
									p_dupeliste.append((p_name))
									self.plugin_liste.pop(int(pop_count))

								pop_count += 1

				if len(self.plugin_liste) != 0:
					for pname, ppic, pgenre in self.plugin_liste:
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (pname, ppic, pgenre, "0", "99"))

				read_pluginliste.close()
				read_pluginliste_tmp.close()
				shutil.move(self.sort_plugins_file+".tmp", self.sort_plugins_file)

				self.new_pluginliste = []
				read_pluginliste = open(self.sort_plugins_file,"r")
				for rawData in read_pluginliste.readlines():
					data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
					if data:
						(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
						self.new_pluginliste.append((p_name, p_picname, p_genre, p_hits, p_sort))
				read_pluginliste.close()

			# Sortieren nach hits
			if config_mp.mediaportal.sortplugins.value == "hits":
				self.new_pluginliste.sort(key=lambda x: int(x[3]))
				self.new_pluginliste.reverse()

			# Sortieren nach abcde..
			elif config_mp.mediaportal.sortplugins.value == "abc":
				self.new_pluginliste.sort(key=lambda x: str(x[0]).lower())

			elif config_mp.mediaportal.sortplugins.value == "user":
				self.new_pluginliste.sort(key=lambda x: int(x[4]))

			self.plugin_liste = self.new_pluginliste

		if config_mp.mediaportal.wall2mode.value == "bw":
			self.wallbw = True

		if mp_globals.videomode == 2:
			self.perpage = 48
			pageiconwidth = 36
			pageicondist = 8
			screenwidth = 1920
			screenheight = 1080
		else:
			self.perpage = 48
			pageiconwidth = 24
			pageicondist = 4
			screenwidth = 1280
			screenheight = 720

		if mp_globals.covercollection:
			path = "%s/%s/MP_Wall2.xml" % (self.skin_path, mp_globals.currentskin)
		else:
			path = "%s/%s/MP_WallVTi.xml" % (self.skin_path, mp_globals.currentskin)
		if not fileExists(path):
			if mp_globals.covercollection:
				path = self.skin_path + mp_globals.skinFallback + "/MP_Wall2.xml"
			else:
				path = self.skin_path + mp_globals.skinFallback + "/MP_WallVTi.xml"
		with open(path, "r") as f:
			self.skin = f.read()
			f.close()

		self.dump_liste_page_tmp = self.plugin_liste
		if config_mp.mediaportal.filter.value != "ALL":
			self.plugin_liste_page_tmp = []
			self.plugin_liste_page_tmp = [x for x in self.dump_liste_page_tmp if re.search(config_mp.mediaportal.filter.value, x[2])]
		else:
			self.plugin_liste_page_tmp = self.plugin_liste

		if len(self.plugin_liste_page_tmp) != 0:
			self.counting_pages = int(round(float((len(self.plugin_liste_page_tmp)-1) / self.perpage) + 0.5))

		# Page Style
		if config_mp.mediaportal.pagestyle.value == "Graphic":
			skincontent = ""
			self.skin = self.skin.replace('</screen>', '')

			if len(self.plugin_liste_page_tmp) != 0:
				pagebar_size = self.counting_pages * pageiconwidth + (self.counting_pages-1) * pageicondist
				start_pagebar = int(screenwidth / 2 - pagebar_size / 2)

				for x in range(1,self.counting_pages+1):
					normal = mp_globals.pagebar_posy
					skincontent += "<widget name=\"page_empty" + str(x) + "\" position=\"" + str(start_pagebar) + "," + str(normal) + "\" size=\"" + str(pageiconwidth) + "," + str(pageiconwidth) + "\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
					skincontent += "<widget name=\"page_sel" + str(x) + "\" position=\"" + str(start_pagebar) + "," + str(normal) + "\" size=\"" + str(pageiconwidth) + "," + str(pageiconwidth) + "\" zPosition=\"2\" transparent=\"1\" alphatest=\"blend\" />"
					start_pagebar += pageiconwidth + pageicondist

			self.skin += skincontent
			self.skin += "</screen>"

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)

		Screen.__init__(self, session)

		addFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal1.ttf", "mediaportal", 100, False)

		if config_mp.mediaportal.backgroundtv.value:
			config_mp.mediaportal.minitv.value = True
			config_mp.mediaportal.minitv.save()
			config_mp.mediaportal.restorelastservice.value = "2"
			config_mp.mediaportal.restorelastservice.save()
			configfile_mp.save()
			session.nav.stopService()
			session.nav.playService(lastservice)
			session.nav.stopService()

		self["actions"] = ActionMap(["MP_Actions"], {
			"up"    : self.keyUp,
			"down"  : self.keyDown,
			"left"  : self.keyLeft,
			"right" : self.keyRight,
			"info"  : self.showPorn,
			"0": boundFunction(self.gotFilter, (_('ALL'),"all")),
			"1": boundFunction(self.gotFilter, (_('Libraries'),"Mediathek")),
			"2": boundFunction(self.gotFilter, (_('Tech & Fun'),"Fun")),
			"3": boundFunction(self.gotFilter, (_('Music'),"Music")),
			"4": boundFunction(self.gotFilter, (_('Sports'),"Sport")),
			"5": boundFunction(self.gotFilter, (_('News & Documentary'),"NewsDoku")),
			"6": boundFunction(self.gotFilter, (_('Porn'),"Porn")),
			"7": boundFunction(self.gotFilter, (_('User-additions'),"User-additions"))
		}, -1)
		self["MP_Actions"] = HelpableActionMap(self, "MP_Actions", {
			"blue"  : (self.startChoose, _("Change filter")),
			"green" : (self.chSort, _("Change sort order")),
			"yellow": (self.manuelleSortierung, _("Manual sorting")),
			"red"   : (self.keySimpleList, _("Open SimpleList")),
			"ok"    : (self.keyOK, _("Open selected Plugin")),
			"cancel": (self.keyCancel, _("Exit MediaPortal")),
			"nextBouquet" :	(self.page_next, _("Next page")),
			"prevBouquet" :	(self.page_back, _("Previous page")),
			"menu" : (self.keySetup, _("MediaPortal Setup")),
		}, -1)

		self['name'] = Label("")
		self['version'] = Label(config_mp.mediaportal.version.value[0:8])
		self['F1'] = Label("SimpleList")
		self['F2'] = Label("")
		self['F3'] = Label(_("Sort"))
		self['F4'] = Label("")
		self['CH+'] = Label(_("CH+"))
		self['CH-'] = Label(_("CH-"))
		self['Exit'] = Label(_("Exit"))
		self['Help'] = Label(_("Help"))
		self['Menu'] = Label(_("Menu"))
		self['page'] = Label("")
		if mp_globals.covercollection:
			self["covercollection"] = CoverCollection()
		else:
			self['list'] = CoverWall()
			self['list'].l.setViewMode(eWallPythonMultiContent.MODE_WALL)

		# Apple Page Style
		if config_mp.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			for x in range(1,self.counting_pages+1):
				self["page_empty"+str(x)] = Pixmap()
				self["page_empty"+str(x)].show()
				self["page_sel"+str(x)] = Pixmap()
				self["page_sel"+str(x)].show()

		HelpableScreen.__init__(self)
		self.onFirstExecBegin.append(self._onFirstExecBegin)
		self.onFirstExecBegin.append(self.checkPathes)
		self.onFirstExecBegin.append(self.status)
		self.onFirstExecBegin.append(self.loadDisplayCover)

	def loadDisplayCover(self):
		self.summaries.updateCover('file:///usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/default_cover.png')

	def checkPathes(self):
		CheckPathes(self.session).checkPathes(self.cb_checkPathes)

	def cb_checkPathes(self):
		self.session.openWithCallback(self.restart, MPSetup)

	def status(self):
		update_agent = getUserAgent()
		update_url = getUpdateUrl()
		twAgentGetPage(update_url, agent=update_agent, timeout=30).addCallback(self.checkstatus)

	def checkstatus(self, html):
		if re.search(".*?<html", html):
			return
		self.html = html
		tmp_infolines = html.splitlines()
		statusurl = tmp_infolines[4]
		update_agent = getUserAgent()
		twAgentGetPage(statusurl, agent=update_agent, timeout=30).addCallback(_status)

	def manuelleSortierung(self):
		if config_mp.mediaportal.filter.value == 'ALL':
			self.session.openWithCallback(self.restart, MPSort)
		else:
			self.session.open(MessageBoxExt, _('Ordering is only possible with filter "ALL".'), MessageBoxExt.TYPE_INFO, timeout=3)

	def hit_plugin(self, pname):
		if fileExists(self.sort_plugins_file):
			read_pluginliste = open(self.sort_plugins_file,"r")
			read_pluginliste_tmp = open(self.sort_plugins_file+".tmp","w")
			for rawData in read_pluginliste.readlines():
				data = re.findall('"(.*?)" "(.*?)" "(.*?)" "(.*?)" "(.*?)"', rawData, re.S)
				if data:
					(p_name, p_picname, p_genre, p_hits, p_sort) = data[0]
					if pname == p_name:
						new_hits = int(p_hits)+1
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, p_genre, str(new_hits), p_sort))
					else:
						read_pluginliste_tmp.write('"%s" "%s" "%s" "%s" "%s"\n' % (p_name, p_picname, p_genre, p_hits, p_sort))
			read_pluginliste.close()
			read_pluginliste_tmp.close()
			shutil.move(self.sort_plugins_file+".tmp", self.sort_plugins_file)

	def _onFirstExecBegin(self):
		_hosters()
		if not mp_globals.start:
			self.close(self.session, True, self.lastservice)
		if config_mp.mediaportal.autoupdate.value:
			checkupdate(self.session).checkforupdate()

		# load plugin icons
		if config_mp.mediaportal.filter.value == "ALL":
			name = _("ALL")
		elif config_mp.mediaportal.filter.value == "Mediathek":
			name = _("Libraries")
		elif config_mp.mediaportal.filter.value == "User-additions":
			name = _("User-additions")
		elif config_mp.mediaportal.filter.value == "Fun":
			name = _("Tech & Fun")
		elif config_mp.mediaportal.filter.value == "NewsDoku":
			name = _("News & Documentary")
		elif config_mp.mediaportal.filter.value == "Music":
			name = _("Music")
		elif config_mp.mediaportal.filter.value == "Sport":
			name = _("Sports")
		elif config_mp.mediaportal.filter.value == "Porn":
			name = _("Porn")
		self['F4'].setText(name)
		self.sortplugin = config_mp.mediaportal.sortplugins.value
		if self.sortplugin == "hits":
			self.sortplugin = "Hits"
		elif self.sortplugin == "abc":
			self.sortplugin = "ABC"
		elif self.sortplugin == "user":
			self.sortplugin = "User"
		self['F2'].setText(self.sortplugin)
		self.dump_liste = self.plugin_liste
		if config_mp.mediaportal.filter.value != "ALL":
			self.plugin_liste = []
			self.plugin_liste = [x for x in self.dump_liste if re.search(config_mp.mediaportal.filter.value, x[2])]
		if len(self.plugin_liste) == 0:
			self.chFilter()
			if config_mp.mediaportal.filter.value == "ALL":
				name = _("ALL")
			elif config_mp.mediaportal.filter.value == "Mediathek":
				name = _("Libraries")
			elif config_mp.mediaportal.filter.value == "User-additions":
				name = _("User-additions")
			elif config_mp.mediaportal.filter.value == "Fun":
				name = _("Tech & Fun")
			elif config_mp.mediaportal.filter.value == "NewsDoku":
				name = _("News & Documentary")
			elif config_mp.mediaportal.filter.value == "Music":
				name = _("Music")
			elif config_mp.mediaportal.filter.value == "Sport":
				name = _("Sports")
			elif config_mp.mediaportal.filter.value == "Porn":
				name = _("Porn")
			self['F4'].setText(name)

		if config_mp.mediaportal.sortplugins.value == "hits":
			self.plugin_liste.sort(key=lambda x: int(x[3]))
			self.plugin_liste.reverse()

		# Sortieren nach abcde..
		elif config_mp.mediaportal.sortplugins.value == "abc":
			self.plugin_liste.sort(key=lambda t : t[0].lower())

		elif config_mp.mediaportal.sortplugins.value == "user":
			self.plugin_liste.sort(key=lambda x: int(x[4]))

		itemList = []
		posterlist = []
		icon_url = getIconUrl()
		if self.wallbw:
			icons_hashes = grabpage(icon_url+"icons_bw/hashes")
		else:
			icons_hashes = grabpage(icon_url+"icons/hashes")
		if icons_hashes:
			icons_data = re.findall('(.*?)\s\*(.*?\.png)', icons_hashes)
		else:
			icons_data = None

		logo_hashes = grabpage(icon_url+"logos/hashes")
		if logo_hashes:
			logo_data = re.findall('(.*?)\s\*(.*?\.png)', logo_hashes)
		else:
			logo_data = None

		for p_name, p_picname, p_genre, p_hits, p_sort in self.plugin_liste:
			remote_hash = ""
			ds = defer.DeferredSemaphore(tokens=5)
			row = []
			itemList.append(((row),))
			if self.wallbw:
				poster_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "icons_bw", p_picname)
				url = icon_url+"icons_bw/" + p_picname + ".png"
				if not fileExists(poster_path):
					if icons_data:
						for x,y in icons_data:
							if y == p_picname+'.png':
								d = ds.run(downloadPage, url, poster_path)
					poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath
				else:
					if icons_data:
						for x,y in icons_data:
							if y == p_picname+'.png':
								remote_hash = x
								local_hash = hashlib.md5(open(poster_path, 'rb').read()).hexdigest()
								if remote_hash != local_hash:
									d = ds.run(downloadPage, url, poster_path)
									poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath
			else:
				poster_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "icons", p_picname)
				url = icon_url+"icons/" + p_picname + ".png"
				if not fileExists(poster_path):
					if icons_data:
						for x,y in icons_data:
							if y == p_picname+'.png':
								d = ds.run(downloadPage, url, poster_path)
					poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath
				else:
					if icons_data:
						for x,y in icons_data:
							if y == p_picname+'.png':
								remote_hash = x
								local_hash = hashlib.md5(open(poster_path, 'rb').read()).hexdigest()
								if remote_hash != local_hash:
									d = ds.run(downloadPage, url, poster_path)
									poster_path = "%s/images/comingsoon.png" % mp_globals.pluginPath

			logo_path = "%s/%s.png" % (config_mp.mediaportal.iconcachepath.value + "logos", p_picname)
			url = icon_url+"logos/" + p_picname + ".png"
			if not fileExists(logo_path):
				if logo_data:
					for x,y in logo_data:
						if y == p_picname+'.png':
							d = ds.run(downloadPage, url, logo_path)
			else:
				if logo_data:
					for x,y in logo_data:
						if y == p_picname+'.png':
							remote_hash = x
							local_hash = hashlib.md5(open(logo_path, 'rb').read()).hexdigest()
							if remote_hash != local_hash:
								d = ds.run(downloadPage, url, logo_path)

			if mp_globals.covercollection:
				row.append((p_name, p_picname, poster_path, p_genre, p_hits, p_sort))
				posterlist.append(poster_path)
			else:
				row.append(((p_name, p_picname, poster_path, p_genre, p_hits, p_sort),))
				posterlist.append(((p_name, p_picname, poster_path, p_genre, p_hits, p_sort),))

		if mp_globals.covercollection:
			self["covercollection"].setList(itemList,posterlist)
		else:
			self['list'].setlist(posterlist)

		if config_mp.mediaportal.pagestyle.value == "Graphic" and len(self.plugin_liste_page_tmp) != 0:
			for x in range(1,self.counting_pages+1):
				poster_path = "%s/page_select.png" % (self.images_path)
				self["page_sel"+str(x)].instance.setPixmap(gPixmapPtr())
				self["page_sel"+str(x)].hide()
				pic = LoadPixmap(cached=True, path=poster_path)
				if pic != None:
					self["page_sel"+str(x)].instance.setPixmap(pic)
					if x == 1:
						self["page_sel"+str(x)].show()

			for x in range(1,self.counting_pages+1):
				poster_path = "%s/page.png" % (self.images_path)
				self["page_empty"+str(x)].instance.setPixmap(gPixmapPtr())
				self["page_empty"+str(x)].hide()
				pic = LoadPixmap(cached=True, path=poster_path)
				if pic != None:
					self["page_empty"+str(x)].instance.setPixmap(pic)
					if x > 1:
						self["page_empty"+str(x)].show()
		self.setInfo()

	def keyOK(self):
		if not testWebConnection():
			self.session.open(MessageBoxExt, _('No connection to the Internet available.'), MessageBoxExt.TYPE_INFO, timeout=3)
			return

		if mp_globals.covercollection:
			if self["covercollection"].getCurrentIndex() >=0:
				item = self["covercollection"].getCurrent()
				(p_name, p_picname, p_picpath, p_genre, p_hits, p_sort) = item[0]
		else:
			if self["list"].getCurrentIndex() >=0:
				item = self['list'].getcurrentselection()
				(p_name, p_picname, p_picpath, p_genre, p_hits, p_sort) = item

		mp_globals.activeIcon = p_picname

		self.pornscreen = None
		self.par1 = ""
		self.par2 = ""
		self.hit_plugin(p_name)

		conf = xml.etree.cElementTree.parse(CONFIG)
		for x in conf.getroot():
			if x.tag == "set" and x.get("name") == 'additions':
				root =  x
				for x in root:
					if x.tag == "plugin":
						if x.get("type") == "mod":
							confcat = x.get("confcat")
							if p_name ==  x.get("name").replace("&amp;","&"):
								status = [item for item in mp_globals.status if item[0] == x.get("modfile")]
								if status:
									if int(config_mp.mediaportal.version.value) < int(status[0][1]):
										if status[0][1] == "9999":
											self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"\n\nIf someone else is willing to provide a fix for this Plugin then please get in contact with us.") % status[0][2], MessageBoxExt.TYPE_INFO)
										else:
											self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"") % status[0][2], MessageBoxExt.TYPE_INFO)
										return
								param = ""
								param1 = x.get("param1")
								param2 = x.get("param2")
								kids = x.get("kids")
								if param1 != "":
									param = ", \"" + param1 + "\""
									self.par1 = param1
								if param2 != "":
									param = param + ", \"" + param2 + "\""
									self.par2 = param2
								if confcat == "porn":
									exec("self.pornscreen = " + x.get("screen") + "")
								elif kids != "1" and config_mp.mediaportal.kidspin.value:
									exec("self.pornscreen = " + x.get("screen") + "")
								else:
									exec("self.session.open(" + x.get("screen") + param + ")")

		xmlpath = resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/additions/")
		for file in os.listdir(xmlpath):
			if file.endswith(".xml") and file != "additions.xml":
				useraddition = xmlpath + file

				conf = xml.etree.cElementTree.parse(useraddition)
				for x in conf.getroot():
					if x.tag == "set" and x.get("name") == 'additions_user':
						root =  x
						for x in root:
							if x.tag == "plugin":
								if x.get("type") == "mod":
									confcat = x.get("confcat")
									if p_name ==  x.get("name").replace("&amp;","&"):
										status = [item for item in mp_globals.status if item[0] == x.get("modfile")]
										if status:
											if int(config_mp.mediaportal.version.value) < int(status[0][1]):
												if status[0][1] == "9999":
													self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"\n\nIf someone else is willing to provide a fix for this Plugin then please get in contact with us.") % status[0][2], MessageBoxExt.TYPE_INFO)
												else:
													self.session.open(MessageBoxExt, _("This Plugin has been marked as \"not working\" by the developers.\n\nCurrent developer status of this Plugin is:\n\"%s\"") % status[0][2], MessageBoxExt.TYPE_INFO)
												return
										param = ""
										param1 = x.get("param1")
										param2 = x.get("param2")
										kids = x.get("kids")
										if param1 != "":
											param = ", \"" + param1 + "\""
											self.par1 = param1
										if param2 != "":
											param = param + ", \"" + param2 + "\""
											self.par2 = param2
										if confcat == "porn":
											exec("self.pornscreen = " + x.get("screen") + "")
										elif kids != "1" and config_mp.mediaportal.kidspin.value:
											exec("self.pornscreen = " + x.get("screen") + "")
										else:
											exec("self.session.open(" + x.get("screen") + param + ")")

		if self.pornscreen:
			if config_mp.mediaportal.pornpin.value:
				if pincheck.pin_entered == False:
					self.session.openWithCallback(self.pincheckok, PinInputExt, pinList = [(config_mp.mediaportal.adultpincode.value)], triesEntry = config_mp.mediaportal.retries.adultpin, title = _("Please enter the correct PIN"), windowTitle = _("Enter adult PIN"))
				else:
					if self.par1 == "":
						self.session.open(self.pornscreen)
					elif self.par2 == "":
						self.session.open(self.pornscreen, self.par1)
					else:
						self.session.open(self.pornscreen, self.par1, self.par2)
			else:
				if self.par1 == "":
					self.session.open(self.pornscreen)
				elif self.par2 == "":
					self.session.open(self.pornscreen, self.par1)
				else:
					self.session.open(self.pornscreen, self.par1, self.par2)

	def pincheckok(self, pincode):
		if pincode:
			pincheck.pinEntered()
			if self.par1 == "":
				self.session.open(self.pornscreen)
			elif self.par2 == "":
				self.session.open(self.pornscreen, self.par1)
			else:
				self.session.open(self.pornscreen, self.par1, self.par2)

	def setInfo(self):
		if mp_globals.covercollection:
			if self["covercollection"].getCurrentIndex() >=0:
				totalPages = self["covercollection"].getTotalPages()

				if totalPages != self.counting_pages:
					msg = "Fatal MP_Wall2.xml error! Wrong covercollection size!"
					printl(msg,'','E')
					raise Exception(msg)

				item = self["covercollection"].getCurrent()
				(p_name, p_picname, p_picpath, p_genre, p_hits, p_sort) = item[0]
				try:
					self['name'].instance.setShowHideAnimation(config_mp.mediaportal.animation_label.value)
				except:
					pass
				self['name'].setText(p_name)
				if config_mp.mediaportal.pagestyle.value == "Graphic":
					self.refresh_apple_page_bar()
				else:
					currentPage = self["covercollection"].getCurrentPage()
					pageinfo = _("Page") + " %s / %s" % (currentPage, totalPages)
					self['page'].setText(pageinfo)
		else:
			if self["list"].getCurrentIndex() >=0:
				totalPages = self["list"].getPageCount()

				if totalPages != self.counting_pages:
					msg = "Fatal MP_WallVTi.xml error! Wrong coverwall size!"
					printl(msg,'','E')
					raise Exception(msg)

				item = self['list'].getcurrentselection()
				(p_name, p_picname, p_picpath, p_genre, p_hits, p_sort) = item
				self['name'].setText(p_name)
				if config_mp.mediaportal.pagestyle.value == "Graphic":
					self.refresh_apple_page_bar()
				else:
					currentPage = self["list"].getCurrentPage()
					totalPages = self["list"].getPageCount()
					pageinfo = _("Page") + " %s / %s" % (currentPage, totalPages)
					self['page'].setText(pageinfo)

	def keyLeft(self):
		if mp_globals.covercollection:
			self["covercollection"].MoveLeft()
		else:
			self['list'].left()
		self.setInfo()

	def keyRight(self):
		if mp_globals.covercollection:
			self["covercollection"].MoveRight()
		else:
			self['list'].right()
		self.setInfo()

	def keyUp(self):
		if mp_globals.covercollection:
			self["covercollection"].MoveUp()
		else:
			self['list'].up()
		self.setInfo()

	def keyDown(self):
		if mp_globals.covercollection:
			self["covercollection"].MoveDown()
		else:
			self['list'].down()
		self.setInfo()

	def page_next(self):
		if mp_globals.covercollection:
			self["covercollection"].NextPage()
		else:
			self['list'].nextPage()
		self.setInfo()

	def page_back(self):
		if mp_globals.covercollection:
			self["covercollection"].PreviousPage()
		else:
			self['list'].prevPage()
		self.setInfo()

	def check_empty_list(self):
		if len(self.plugin_liste) == 0:
			self['name'].setText('Keine Plugins der Kategorie %s aktiviert!' % config_mp.mediaportal.filter.value)
			return True
		else:
			return False

	# Apple Page Style
	def refresh_apple_page_bar(self):
		if config_mp.mediaportal.pagestyle.value == "Graphic":
			if mp_globals.covercollection:
				if self["covercollection"].getCurrentIndex() >=0:
					currentPage = self["covercollection"].getCurrentPage()
					totalPages = self["covercollection"].getTotalPages()
					for x in range(1,totalPages+1):
						if x == currentPage:
							self["page_empty"+str(x)].hide()
							self["page_sel"+str(x)].show()
						else:
							self["page_sel"+str(x)].hide()
							self["page_empty"+str(x)].show()
			else:
				if self["list"].getCurrentIndex() >=0:
					currentPage = self["list"].getCurrentPage()
					totalPages = self["list"].getPageCount()
					for x in range(1,totalPages+1):
						if x == currentPage:
							self["page_empty"+str(x)].hide()
							self["page_sel"+str(x)].show()
						else:
							self["page_sel"+str(x)].hide()
							self["page_empty"+str(x)].show()

	def keySetup(self):
		if config_mp.mediaportal.setuppin.value:
			self.session.openWithCallback(self.pinok, PinInputExt, pinList = [(config_mp.mediaportal.pincode.value)], triesEntry = config_mp.mediaportal.retries.pincode, title = _("Please enter the correct PIN"), windowTitle = _("Enter setup PIN"))
		else:
			self.session.openWithCallback(self.restart, MPSetup)

	def keySimpleList(self):
		mp_globals.activeIcon = "simplelist"
		self.session.open(simplelistGenreScreen)

	def pinok(self, pincode):
		if pincode:
			self.session.openWithCallback(self.restart, MPSetup)

	def chSort(self):
		if config_mp.mediaportal.sortplugins.value == "hits":
			config_mp.mediaportal.sortplugins.value = "abc"
		elif config_mp.mediaportal.sortplugins.value == "abc":
			config_mp.mediaportal.sortplugins.value = "user"
		elif config_mp.mediaportal.sortplugins.value == "user":
			config_mp.mediaportal.sortplugins.value = "hits"
		self.restart()

	def chFilter(self):
		if config_mp.mediaportal.filter.value == "ALL":
			config_mp.mediaportal.filter.value = "Mediathek"
		elif config_mp.mediaportal.filter.value == "Mediathek":
			config_mp.mediaportal.filter.value = "Fun"
		elif config_mp.mediaportal.filter.value == "Fun":
			config_mp.mediaportal.filter.value = "Music"
		elif config_mp.mediaportal.filter.value == "Music":
			config_mp.mediaportal.filter.value = "Sport"
		elif config_mp.mediaportal.filter.value == "Sport":
			config_mp.mediaportal.filter.value = "NewsDoku"
		elif config_mp.mediaportal.filter.value == "NewsDoku":
			config_mp.mediaportal.filter.value = "Porn"
		elif config_mp.mediaportal.filter.value == "Porn":
			config_mp.mediaportal.filter.value = "User-additions"
		elif config_mp.mediaportal.filter.value == "User-additions":
			config_mp.mediaportal.filter.value = "ALL"
		else:
			config_mp.mediaportal.filter.value = "ALL"
		self.restartAndCheck()

	def restartAndCheck(self):
		if config_mp.mediaportal.filter.value != "ALL":
			dump_liste2 = self.dump_liste
			self.plugin_liste = []
			self.plugin_liste = [x for x in dump_liste2 if re.search(config_mp.mediaportal.filter.value, x[2])]
			if len(self.plugin_liste) == 0:
				self.chFilter()
			else:
				config_mp.mediaportal.filter.save()
				configfile_mp.save()
				self.close(self.session, False, self.lastservice)
		else:
			config_mp.mediaportal.filter.save()
			configfile_mp.save()
			self.close(self.session, False, self.lastservice)

	def showPorn(self):
		if config_mp.mediaportal.showporn.value:
			config_mp.mediaportal.showporn.value = False
			if config_mp.mediaportal.filter.value == "Porn":
				config_mp.mediaportal.filter.value = "ALL"
			config_mp.mediaportal.showporn.save()
			config_mp.mediaportal.filter.save()
			configfile_mp.save()
			self.restart()
		else:
			self.session.openWithCallback(self.showPornOK, PinInputExt, pinList = [(config_mp.mediaportal.adultpincode.value)], triesEntry = config_mp.mediaportal.retries.adultpin, title = _("Please enter the correct PIN"), windowTitle = _("Enter adult PIN"))

	def showPornOK(self, pincode):
		if pincode:
			pincheck.pinEntered()
			config_mp.mediaportal.filter.value = "Porn"
			config_mp.mediaportal.filter.save()
			config_mp.mediaportal.showporn.value = True
			config_mp.mediaportal.showporn.save()
			configfile_mp.save()
			self.restart()

	def keyCancel(self):
		config_mp.mediaportal.filter.save()
		configfile_mp.save()
		self.close(self.session, True, self.lastservice)

	def restart(self):
		config_mp.mediaportal.filter.save()
		config_mp.mediaportal.sortplugins.save()
		configfile_mp.save()
		if autoStartTimer is not None:
			autoStartTimer.update()
		self.close(self.session, False, self.lastservice)

	def startChoose(self):
		if not config_mp.mediaportal.showporn.value:
			xporn = ""
		else:
			xporn = _('Porn')
		if not config_mp.mediaportal.showuseradditions.value:
			useradd = ""
		else:
			useradd = _('User-additions')
		rangelist = [[_('ALL'), 'all'], [_('Libraries'), 'Mediathek'], [_('Tech & Fun'), 'Fun'], [_('Music'), 'Music'], [_('Sports'), 'Sport'], [_('News & Documentary'), 'NewsDoku'], [xporn, 'Porn'], [useradd, 'User-additions']]
		self.session.openWithCallback(self.gotFilter, ChoiceBoxExt, keys=["0", "1", "2", "3", "4", "5", "6", "7"], title=_('Select Filter'), list = rangelist)

	def gotFilter(self, filter):
		if filter:
			if not config_mp.mediaportal.showporn.value and filter[1] == "Porn":
				return
			if not config_mp.mediaportal.showuseradditions.value and filter[1] == "User-additions":
				return
			if filter[0] == "":
				return
			elif filter:
				config_mp.mediaportal.filter.value = filter[1]
				self.restartAndCheck()

	def createSummary(self):
		return MPSummary

class MPSummary(Screen):

	def __init__(self, session, parent):
		try:
			displaysize = getDesktop(1).size()
			if model in ["dm900","dm920"]:
				disp_id = ' id="3"'
				disp_size = str(displaysize.width()-8) + "," + str(displaysize.height())
				disp_pos = "8,0"
			elif model in ["dm7080"]:
				disp_id = ' id="3"'
				disp_size = str(displaysize.width()) + "," + str(displaysize.height()-14)
				disp_pos = "0,0"
			elif model in ["dm820"]:
				disp_id = ' id="2"'
				disp_size = str(displaysize.width()) + "," + str(displaysize.height())
				disp_pos = "0,0"
			else:
				disp_id = ' id="1"'
				disp_size = str(displaysize.width()) + "," + str(displaysize.height())
				disp_pos = "0,0"

		except:
			disp_size = "1,1"
			disp_id = ' id="1"'
			disp_pos = "0,0"

		self["cover"] = Pixmap()

		self.skin = '''<screen name="MPScreenSummary" backgroundColor="#00000000" position="''' + disp_pos + '''" size="''' + disp_size  + '''"''' + disp_id + '''>
				<widget name="cover" position="center,center" size="''' + disp_size + '''" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/images/none.png" transparent="1" alphatest="blend" />
				</screen>'''

		self.skinName = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])
		Screen.__init__(self, session)

	def updateCover(self, filename):
		CoverHelper(self['cover']).getCover(filename)

def exit(session, result, lastservice):
	global lc_stats
	if not result:
		if config_mp.mediaportal.premiumize_use.value:
			if not mp_globals.premium_yt_proxy_host:
				CheckPremiumize(session).premiumizeProxyConfig(False)

		mp_globals.currentskin = config_mp.mediaportal.skin2.value
		mp_globals.font = 'mediaportal'
		_stylemanager(1)

		if config_mp.mediaportal.ansicht.value == "liste":
			session.openWithCallback(exit, MPList, lastservice)
		elif config_mp.mediaportal.ansicht.value == "wall":
			session.openWithCallback(exit, MPWall, lastservice, config_mp.mediaportal.filter.value)
		elif config_mp.mediaportal.ansicht.value == "wall2":
			session.openWithCallback(exit, MPWall2, lastservice, config_mp.mediaportal.filter.value)
	else:
		try:
			if mp_globals.animationfix:
				getDesktop(0).setAnimationsEnabled(False)
				mp_globals.animationfix = False
		except:
			pass

		session.nav.playService(lastservice)

		config_mp.mediaportal.skinfail.value = False
		config_mp.mediaportal.skinfail.save()
		configfile_mp.save()

		_stylemanager(0)

		reactor.callLater(1, export_lru_caches)
		reactor.callLater(5, clearTmpBuffer)
		reactor.callLater(30, clearFileBuffer)
		watcher.stop()
		if SHOW_HANG_STAT:
			lc_stats.stop()
			del lc_stats

def _stylemanager(mode):
	raisemsg = ''
	desktopSize = getDesktop(0).size()
	if desktopSize.height() == 1080:
		mp_globals.videomode = 2
		mp_globals.fontsize = 30
		mp_globals.sizefactor = 3
		mp_globals.pagebar_posy = 985
		mp_globals.sp_seekbar_factor = 10.92
	else:
		mp_globals.videomode = 1
		mp_globals.fontsize = 23
		mp_globals.sizefactor = 1
		mp_globals.pagebar_posy = 655
		mp_globals.sp_seekbar_factor = 7.28
	try:
		from enigma import eWindowStyleManager, eWindowStyleSkinned, eSize, eListboxPythonStringContent, eListboxPythonConfigContent
		try:
			from enigma import eWindowStyleScrollbar
		except:
			pass
		from skin import parseSize, parseFont, parseColor
		try:
			from skin import parseValue
		except:
			pass

		stylemgr = eWindowStyleManager.getInstance()
		desktop = getDesktop(0)
		styleskinned = eWindowStyleSkinned()

		if mode == 0:
			skin_path = resolveFilename(SCOPE_CURRENT_SKIN) + "skin.xml"
			skin_path_font = skin_path
			skin_path_colors = resolveFilename(SCOPE_CURRENT_SKIN) + "skin_user_colors.xml"
			if not fileExists(skin_path_colors):
				skin_path_colors = skin_path
			file_path = resolveFilename(SCOPE_SKIN)
		else:
			skin_path = mp_globals.pluginPath + mp_globals.skinsPath + "/" + mp_globals.currentskin + "/MP_skin.xml"
			if not fileExists(skin_path):
				skin_path = mp_globals.pluginPath + mp_globals.skinsPath + "/" + mp_globals.currentskin + "/skin.xml"
				if not fileExists(skin_path):
					config_mp.mediaportal.skin2.value = ''
					config_mp.mediaportal.skin2.save()
					configfile_mp.save()
					raisemsg = "Missing MP_skin.xml, this file is mandatory!"
				else:
					printl('Obsolete file skin.xml, please use filename MP_skin.xml!','','E')
			skin_path_font = skin_path
			skin_path_colors = skin_path
			file_path = mp_globals.pluginPath + "/"

		if fileExists(skin_path):
			conf = xml.etree.cElementTree.parse(skin_path_font)
			for x in conf.getroot():
				if x.tag == "fonts" and mode == 0:
					fonts = x
					for x in fonts:
						if x.tag == "font":
							replacement = x.get("replacement")
							if replacement == "1":
								filename = x.get("filename")
								name = x.get("name")
								scale = x.get("scale")
								if scale:
									scale = int(scale)
								else:
									scale = 100
								resolved_font = resolveFilename(SCOPE_FONTS, filename, path_prefix='')
								if not fileExists(resolved_font): #when font is not available look at current skin path
									skin_path = resolveFilename(SCOPE_CURRENT_SKIN, filename)
									if fileExists(skin_path):
										resolved_font = skin_path
								addFont(resolved_font, name, scale, True)

			conf = xml.etree.cElementTree.parse(skin_path_colors)
			for x in conf.getroot():
				if x.tag == "windowstylescrollbar":
					try:
						stylescrollbar = eWindowStyleScrollbar()
						skinScrollbar = True
					except:
						skinScrollbar = False
					if skinScrollbar:
						try:
							id = int(x.get("id"))
						except:
							id = 4
						windowstylescrollbar =  x
						for x in windowstylescrollbar:
							if x.tag == "value":
								if x.get("name") in ("BackgroundPixmapTopHeight", "BackgroundPixmapBeginSize"):
									stylescrollbar.setBackgroundPixmapTopHeight(int(x.get("value")))
								elif x.get("name") in ("BackgroundPixmapBottomHeight", "BackgroundPixmapEndSize"):
									stylescrollbar.setBackgroundPixmapBottomHeight(int(x.get("value")))
								elif x.get("name") in ("ValuePixmapTopHeight", "ValuePixmapBeginSize"):
									stylescrollbar.setValuePixmapTopHeight(int(x.get("value")))
								elif x.get("name") in ("ValuePixmapBottomHeight", "ValuePixmapEndSize"):
									stylescrollbar.setValuePixmapBottomHeight(int(x.get("value")))
								elif x.get("name") == "ScrollbarWidth":
									stylescrollbar.setScrollbarWidth(int(x.get("value")))
								elif x.get("name") == "ScrollbarBorderWidth":
									stylescrollbar.setScrollbarBorderWidth(int(x.get("value")))
							if x.tag == "pixmap":
								if x.get("name") == "BackgroundPixmap":
									stylescrollbar.setBackgroundPixmap(LoadPixmap(file_path + x.get("filename"), desktop))
								elif x.get("name") == "ValuePixmap":
									stylescrollbar.setValuePixmap(LoadPixmap(file_path + x.get("filename"), desktop))
						try:
							stylemgr.setStyle(id, stylescrollbar)
						except:
							pass
				elif x.tag == "windowstyle" and x.get("id") == "0":
					font = gFont("Regular", 20)
					offset = eSize(20, 5)
					windowstyle = x
					for x in windowstyle:
						if x.tag == "title":
							font = parseFont(x.get("font"), ((1,1),(1,1)))
							offset = parseSize(x.get("offset"), ((1,1),(1,1)))
						elif x.tag == "color":
							colorType = x.get("name")
							color = parseColor(x.get("color"))
							try:
								styleskinned.setColor(eWindowStyleSkinned.__dict__["col" + colorType], color)
							except:
								pass
						elif x.tag == "borderset":
							bsName = str(x.get("name"))
							borderset =  x
							for x in borderset:
								if x.tag == "pixmap":
									bpName = x.get("pos")
									if "filename" in x.attrib:
										try:
											styleskinned.setPixmap(eWindowStyleSkinned.__dict__[bsName], eWindowStyleSkinned.__dict__[bpName], LoadPixmap(file_path + x.get("filename"), desktop))
										except:
											pass
									elif "color" in x.attrib:
										color = parseColor(x.get("color"))
										size = int(x.get("size"))
										try:
											styleskinned.setColorBorder(eWindowStyleSkinned.__dict__[bsName], eWindowStyleSkinned.__dict__[bpName], color, size)
										except:
											pass
						elif x.tag == "listfont":
							fontType = x.get("type")
							fontSize = int(x.get("size"))
							fontFace = x.get("font")
							try:
								styleskinned.setListFont(eWindowStyleSkinned.__dict__["listFont" + fontType], fontSize, fontFace)
							except:
								pass
					try:
						styleskinned.setTitleFont(font)
						styleskinned.setTitleOffset(offset)
					except:
						pass
				elif x.tag == "listboxcontent":
					listboxcontent = x
					for x in listboxcontent:
						if x.tag == "offset":
							name = x.get("name")
							value = x.get("value")
							if name and value:
								try:
									if name == "left":
											eListboxPythonStringContent.setLeftOffset(parseValue(value))
									elif name == "right":
											eListboxPythonStringContent.setRightOffset(parseValue(value))
								except:
									pass
						elif x.tag == "font":
							name = x.get("name")
							font = x.get("font")
							if name and font:
								try:
									if name == "string":
											eListboxPythonStringContent.setFont(parseFont(font, ((1,1),(1,1))))
									elif name == "config_description":
											eListboxPythonConfigContent.setDescriptionFont(parseFont(font, ((1,1),(1,1))))
									elif name == "config_value":
											eListboxPythonConfigContent.setValueFont(parseFont(font, ((1,1),(1,1))))
								except:
									pass
						elif x.tag == "value":
							name = x.get("name")
							value = x.get("value")
							if name and value:
								try:
									if name == "string_item_height":
											eListboxPythonStringContent.setItemHeight(parseValue(value))
									elif name == "config_item_height":
											eListboxPythonConfigContent.setItemHeight(parseValue(value))
								except:
									pass
				elif x.tag == "mediaportal":
					mediaportal = x
					for x in mediaportal:
						if x.tag == "color":
							colorType = x.get("name")
							exec("mp_globals." + x.get("name") + "=\"" + x.get("color") + "\"")
						elif x.tag == "overridefont":
							mp_globals.font = x.get("font")
						elif x.tag == "overridefontsize":
							mp_globals.fontsize = int(x.get("value"))
						elif x.tag == "overridesizefactor":
							mp_globals.sizefactor = int(x.get("value"))
						elif x.tag == "pagebar_posy":
							mp_globals.pagebar_posy = int(x.get("value"))
						elif x.tag == "sp_seekbar_factor":
							mp_globals.sp_seekbar_factor = float(x.get("value"))
			stylemgr.setStyle(0, styleskinned)
		else:
			pass
	except:
		printl('Fatal MP_skin.xml error!','','E')

	if raisemsg != '':
		raise Exception(raisemsg)

def _hosters():
	hosters_file = "/usr/lib/enigma2/python/Plugins/Extensions/MediaPortal/resources/hosters/hosters.xml"
	open_hosters = open(hosters_file)
	data = open_hosters.read()
	open_hosters.close()
	hosters = re.findall('<hoster>(.*?)</hoster><regex>(.*?)</regex>', data)
	mp_globals.hosters = ["|".join([hoster for hoster,regex in hosters])]
	mp_globals.hosters += ["|".join([regex for hoster,regex in hosters])]

def _status(data):
	statusdata = re.findall('"(.*?)"\s"(.*?)"\s"(.*?)"', data)
	if statusdata:
		mp_globals.status = []
		for (plugin, version, status) in statusdata:
			mp_globals.status.append((plugin,version,status))

from resources.simple_lru_cache import SimpleLRUCache
mp_globals.lruCache = SimpleLRUCache(50, config_mp.mediaportal.watchlistpath.value + 'mp_lru_cache')
mp_globals.yt_lruCache = SimpleLRUCache(100, config_mp.mediaportal.watchlistpath.value + 'mp_yt_lru_cache')

watcher = None
lc_stats = None

def export_lru_caches():
	if config_mp.mediaportal.sp_save_resumecache.value:
		mp_globals.lruCache.saveCache()
		mp_globals.yt_lruCache.saveCache()

def import_lru_caches():
	if config_mp.mediaportal.sp_save_resumecache.value:
		mp_globals.lruCache.readCache()
		mp_globals.yt_lruCache.readCache()

def clearTmpBuffer():
	if mp_globals.yt_tmp_storage_dirty:
		mp_globals.yt_tmp_storage_dirty = False
		BgFileEraser = eBackgroundFileEraser.getInstance()
		path = config_mp.mediaportal.storagepath.value
		if os.path.exists(path):
			for fn in next(os.walk(path))[2]:
				BgFileEraser.erase(os.path.join(path,fn))

def clearFileBuffer():
	def clean(hashes, path):
		BgFileEraser = eBackgroundFileEraser.getInstance()
		if os.path.exists(path):
			for fn in next(os.walk(path))[2]:
				local_hash = hashlib.md5(open(os.path.join(path,fn), 'rb').read()).hexdigest()
				if local_hash not in (item[0] for item in hashes):
					BgFileEraser.erase(os.path.join(path,fn))
	icon_url = getIconUrl()
	path = config_mp.mediaportal.iconcachepath.value + "icons"
	icons_hashes = grabpage(icon_url+"icons/hashes")
	if icons_hashes:
		icons_data = re.findall('(.*?)\s\*(.*?\.png)', icons_hashes)
		clean(icons_data, path)
	path = config_mp.mediaportal.iconcachepath.value + "icons_bw"
	icons_bw_hashes = grabpage(icon_url+"icons_bw/hashes")
	if icons_bw_hashes:
		icons_bw_data = re.findall('(.*?)\s\*(.*?\.png)', icons_bw_hashes)
		clean(icons_bw_data, path)
	path = config_mp.mediaportal.iconcachepath.value + "logos"
	logo_hashes = grabpage(icon_url+"logos/hashes")
	if logo_hashes:
		logo_data = re.findall('(.*?)\s\*(.*?\.png)', logo_hashes)
		clean(logo_data, path)

def MPmain(session, **kwargs):
	mp_globals.start = True
	startMP(session)

def startMP(session):
	try:
		if not getDesktop(0).isAnimationsEnabled():
			getDesktop(0).setAnimationsEnabled(True)
			mp_globals.animationfix = True
	except:
		pass

	from resources.debuglog import printlog as printl
	printl('Starting MediaPortal %s' % config_mp.mediaportal.version.value,None,'H')

	global watcher, lc_stats

	reactor.callLater(2, import_lru_caches)

	addFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal1.ttf", "mediaportal", 100, False)
	addFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "mediaportal_clean.ttf", "mediaportal_clean", 100, False)
	addFont(resolveFilename(SCOPE_PLUGINS, "Extensions/MediaPortal/resources/") + "unifont.otf", "Replacement", 100, True)

	if config_mp.mediaportal.skinfail.value:
		config_mp.mediaportal.skin2.value = ''
		config_mp.mediaportal.skin2.save()
	else:
		config_mp.mediaportal.skinfail.value = True
		config_mp.mediaportal.skinfail.save()
	configfile_mp.save()

	mp_globals.currentskin = config_mp.mediaportal.skin2.value
	_stylemanager(1)

	if watcher == None:
		watcher = HangWatcher()
	watcher.start()
	if SHOW_HANG_STAT:
		lc_stats = task.LoopingCall(watcher.print_stats)
		lc_stats.start(60)

	#if config_mp.mediaportal.epg_enabled.value and not config_mp.mediaportal.epg_runboot.value and not mpepg.has_epg:
	#	def importFini(msg):
	#		session.open(MessageBoxExt, msg, type = MessageBoxExt.TYPE_INFO, timeout=5)
	#	mpepg.importEPGData().addCallback(importFini)

	if config_mp.mediaportal.hideporn_startup.value and config_mp.mediaportal.showporn.value:
		config_mp.mediaportal.showporn.value = False
		if config_mp.mediaportal.filter.value == "Porn":
			config_mp.mediaportal.filter.value = "ALL"
		config_mp.mediaportal.showporn.save()
		config_mp.mediaportal.filter.save()
		configfile_mp.save()

	if config_mp.mediaportal.premiumize_use.value:
		if not mp_globals.premium_yt_proxy_host:
			CheckPremiumize(session).premiumizeProxyConfig(False)

	lastservice = session.nav.getCurrentlyPlayingServiceReference()

	if config_mp.mediaportal.ansicht.value == "liste":
		session.openWithCallback(exit, MPList, lastservice)
	elif config_mp.mediaportal.ansicht.value == "wall":
		session.openWithCallback(exit, MPWall, lastservice, config_mp.mediaportal.filter.value)
	elif config_mp.mediaportal.ansicht.value == "wall2":
		session.openWithCallback(exit, MPWall2, lastservice, config_mp.mediaportal.filter.value)

##################################
# Autostart section
class AutoStartTimer:
	def __init__(self, session):
		import enigma

		self.session = session
		self.timer = enigma.eTimer()
		if mp_globals.isDreamOS:
			self.timer_conn = self.timer.timeout.connect(self.onTimer)
		else:
			self.timer.callback.append(self.onTimer)
		self.update()

	def getWakeTime(self):
		import time
		if config_mp.mediaportal.epg_enabled.value:
			clock = config_mp.mediaportal.epg_wakeup.value
			nowt = time.time()
			now = time.localtime(nowt)
			return int(time.mktime((now.tm_year, now.tm_mon, now.tm_mday,
				clock[0], clock[1], lastMACbyte()/5, 0, now.tm_yday, now.tm_isdst)))
		else:
			return -1

	def update(self, atLeast = 0):
		import time
		self.timer.stop()
		wake = self.getWakeTime()
		now = int(time.time())
		if wake > 0:
			if wake < now + atLeast:
				# Tomorrow.
				wake += 24*3600
			next = wake - now
			self.timer.startLongTimer(next)
		else:
			wake = -1
		print>>log, "[MP EPGImport] WakeUpTime now set to", wake, "(now=%s)" % now
		return wake

	def runImport(self):
		if config_mp.mediaportal.epg_enabled.value:
			mpepg.getEPGData()

	def onTimer(self):
		import time
		self.timer.stop()
		now = int(time.time())
		print>>log, "[MP EPGImport] onTimer occured at", now
		wake = self.getWakeTime()
		# If we're close enough, we're okay...
		atLeast = 0
		if wake - now < 60:
			self.runImport()
			atLeast = 60
		self.update(atLeast)

def onBootStartCheck():
	import time
	global autoStartTimer
	print>>log, "[MP EPGImport] onBootStartCheck"
	now = int(time.time())
	wake = autoStartTimer.update()
	print>>log, "[MP EPGImport] now=%d wake=%d wake-now=%d" % (now, wake, wake-now)
	if (wake < 0) or (wake - now > 600):
		print>>log, "[MP EPGImport] starting import because auto-run on boot is enabled"
		autoStartTimer.runImport()
	else:
		print>>log, "[MP EPGImport] import to start in less than 10 minutes anyway, skipping..."

def autostart(reason, session=None, **kwargs):
	"called with reason=1 to during shutdown, with reason=0 at startup?"
	#global autoStartTimer
	global _session, watcher
	#import time
	#print>>log, "[MP EPGImport] autostart (%s) occured at" % reason, time.time()
	if reason == 0:
		if session is not None:
			_session = session
			CheckPathes(session).checkPathes(cb_checkPathes)
		if watcher == None:
			watcher = HangWatcher()
		#if autoStartTimer is None:
		#	autoStartTimer = AutoStartTimer(session)
		#if config_mp.mediaportal.epg_runboot.value:
		#	# timer isn't reliable here, damn
		#	onBootStartCheck()
		#if config_mp.mediaportal.epg_deepstandby.value == 'wakeup':
		#	if config_mp.mediaportal.epg_wakeupsleep.value:
		#		print>>log, "[MP EPGImport] Returning to standby"
		#		from Tools import Notifications
		#		Notifications.AddNotification(Screens.Standby.Standby)
	#else:
		#print>>log, "[MP EPGImport] Stop"
		#if autoStartTimer:
		#autoStartTimer.stop()

def cb_checkPathes():
	pass

def getNextWakeup():
	"returns timestamp of next time when autostart should be called"
	if autoStartTimer:
		if config_mp.mediaportal.epg_deepstandby.value == 'wakeup':
			print>>log, "[MP EPGImport] Will wake up from deep sleep"
			return autoStartTimer.update()
	return -1

def Plugins(path, **kwargs):
	mp_globals.pluginPath = path
	mp_globals.font = 'mediaportal'

	result = [
		PluginDescriptor(name="MediaPortal", description="MediaPortal - EPG Importer", where = [PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart, wakeupfnc = getNextWakeup),
		PluginDescriptor(name="MediaPortal", description="MediaPortal", where = [PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU], icon="plugin.png", fnc=MPmain)
	]
	return result
