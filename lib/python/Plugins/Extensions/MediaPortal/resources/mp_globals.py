# -*- coding: utf-8 -*-
start = False
pluginPath = ""
skinsPath = ""
skinFallback = ""
currentskin = ""
activeIcon = ""
premiumize = False
realdebrid = False
isDreamOS = False
isVTi = False
animations = False
fakeScale = False
covercollection = False
ddlme_sortOrder = 0
skto_sortOrder = 0
streamit_sortOrder = 0
premium_hosters_prz = '(streamclou|openload|oload|uploaded|ul.to|filefactory|rg.to|rapidgator|turbobit|1fichier|uptobox|depfile|flashx|rapidvideo|thevideo|vidto)'
premium_hosters_rdb = '(openload|oload|uploaded|ul.to|filefactory|rapidgator|rg.to|turbobit|1fichier|uptobox|oboom|depfile|rapidvideo|thevideo)'
premium_yt_proxy_host = ''
premium_yt_proxy_port = 0
hosters = []
status = []
player_agent = None
font = ""
videomode = 1
fontsize = 23
sizefactor = 1
pagebar_posy = 655
sp_seekbar_factor = 7.28
hls_proxy_port = 0
ThumbViewTextForeground = '#00ffffff'
ThumbViewTextBackground = '#20000000'
bsp = None
bdmt = None
requests = False

std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
}

from simple_lru_cache import SimpleLRUCache
lruCache = None
yt_dwnld_agent = None
yt_download_runs = False
yt_tmp_storage_dirty = False
yt_dwnld_lastnum = 0
yt_bytes_downloaded = 0
yt_download_progress_widget = None
yt_lruCache = None
yt_a = None
yt_s = None
yt_i = None
animationfix = False
lastservice = None
stateinfo = False