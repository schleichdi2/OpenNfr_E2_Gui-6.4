# -*- coding: utf-8 -*-

from os.path import isfile
import glob
import sys
import mp_globals
from Plugins.Extensions.MediaPortal.plugin import _
from imports import *
from simpleplayer import SimplePlayer, SimplePlaylistIO
from Components.FileList import FileList
from debuglog import printlog as printl
from configlistext import ConfigListScreenExt
from choiceboxext import ChoiceBoxExt
from twisted.internet import task
from twagenthelper import twAgentGetPage, twDownloadPage

if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/SerienFilm/MovieSelection.pyo'):
	from Plugins.Extensions.SerienFilm.MovieSelection import MovieSelection
else:
	from Screens.MovieSelection import MovieSelection
from Plugins.Extensions.MediaPortal.resources.mp_hlsp import *
from sepg.mp_epg import SimpleEPG, mpepg, mutex

try:
	from Plugins.Extensions.MediaInfo.plugin import MediaInfo
	MediaInfoPresent = True
except:
	MediaInfoPresent = False

TVG_LOGO_BASE = "http://logo.tvip.ga/"
TVG_INK_LOGO_BASE = "http://logo.iptv.ink/"
TVG_WOW_LOGO_BASE = "http://wownet.ro/logo/"
global colors
colors = {
		'orange': '0xFFA500',
		'orangered': '0xFF4500',
		'lightgrey': '0xD3D3D3',
		'gold': '0xFFD700',
		'goldenrod': '0xDAA520',
		'olivedrab': '0x6B8E23',
		'deeppink': '0xFF1493',
		'red': '0xFF0000',
	}
DEFAULT_COLOR = '0xD3D3D3' # lightgrey

tvg_conv = {
	"AlJazeeraArabe.nws":"aljazeera.uk",
	"AlJazeera.nws":"aljazeera.uk",
	"AnixeHD.de":"anixe.de",
	"ATV.de":"atv.at",
	"mdrhd.de":"mdr.de",
	"ORF1.de":"orfeins.at",
	"ORF2.de":"orf2.at",
	"ORF1.at":"orfeins.at",
	"Nickelodeon.de":"nick.de",
	"ARD.de":"daserste.de",
	"BBC3.uk":"bbc3cbbc.uk",
	"BBCWorldNews.nws":"bbcworld.uk",
	"CanalAlpha":"canalalpha.fr",
	"CHTVHD":"chtv.ch",
	"CNN.nws":"cnn.uk",
	"CNBC.nws":"cnbc.uk",
	"DeLuxeMusic.de":"deluxe.de",
	"DeutscheWelle.de":"dw.de",
	"Euronews.nws":"euronews",
	"FamilyTV.de":"family.de",
	"ITV1London.uk":"itv.uk",
	"EuSp":"eurosport.de",
	"Kabel.de":"kabeleins.ch",
	"MDRSachsen.de":"mdrsa.de",
	"MTVit":"mtv.it",
	"MTV":"mtv.de",
	"Nickelodeon.de":"nick.de",
	"Pro7.de":"prosieben.ch",
	"TSI1.ch":"rsila1.it",
	"TSI2.ch":"rsila2.it",
	"RTL2.de":"rtl2.ch",
	"RTL.de":"rtl.ch",
	"TSR1.ch":"rts1.fr",
	"TSR2.ch":"rts2.fr",
	"SuperRTL.de":"superrtl.ch",
	"SRTL.de":"superrtl.ch",
	"Sat1.de":"sat1.ch",
	"ServusHD.de":"servustv.de",
	"Sport1HD.de":"sport1.de",
	"SF1.ch":"srf1.ch",
	"SF2.ch":"srfzwei.ch",
	"SRF2.ch":"srfzwei.ch",
	"TBasel":"telebasel.ch",
	"TBärn":"telebarn.ch",
	"Tele1":"tele1.ch",
	"Tele5.at":"tele5.de",
	"TeleBielingue":"telebielingue.ch",
	"TeleTicino":"teleticino.it",
	"TeleTop":"teletop.ch",
	"TeleZurich.ch":"telezuri.ch",
	"TRT1":"trt1.tr",
	"TSO":"tso.ch",
	"TV5":"tv5monde.fr",
	"TV24":"tv24.ch",
	"TZüri":"telezuri.ch",
	"VIVA":"viva.ch",
	"ComedyCentral/VIVA.de":"viva.de",
	"VOXchHD":"vox.ch",
	"Vox.de":"vox.ch",
	"W9.ch":"w9.fr",
	"ZDFtheater.de":"zdfkultur.de",
	"TVO":"tvo.ch",
	"ndr.de":"ndrns.de",
	"MTV":"mtv.ch",
	"MTVit":"mtv.it",
	"disneychannel.de":"disney.de",
	"3sat":"3sat.de",
	"ard.de":"daserste.de",
	"disneychannel":"disney.de",
	"kabel.de":"kabeleins.ch",
	"mdr":"mdrsa.de",
	"ndr":"ndrns.de",
	"nick":"nick.de",
	"pro7.de":"prosieben.ch",
	"ProSieben.Maxx":"prosiebenmaxx.de",
	"rtl.de":"rtl.ch",
	"rtl2.de":"rtl2.ch",
	"sat1.de":"sat1.ch",
	"sixx":"sixx.de",
	"sport.1":"sport1.de",
	"srtl.de":"superrtl.ch",
	"vox.de":"vox.ch",
	"zdfinfo":"zdfinfo.de",
	"mtv":"mtv.ch",
	"puls8":"puls8.ch",
	"sf1.ch":"srf1.ch",
	"sf2.ch":"srfzwei.ch",
	"atv.de":"atv.at",
	"orf1.de":"orfeins.at",
	"orf2.de":"orf2.at",
}

class simplelistGenreScreen(MPScreen, ThumbsHelper):

	def __init__(self, session):

		MPScreen.__init__(self, session, skin='MP_Plugin')

		self["hidePig"] = Boolean()
		self["hidePig"].setBoolean(config_mp.mediaportal.minitv.value)
		ThumbsHelper.__init__(self)

		self["actions"] = ActionMap(["MP_Actions"], {
			"0"		: self.closeAll,
			"5"		: self._keyShowThumb,
			"ok"    : self.keyOK,
			"cancel": self.wait_keyCancel,
			"menu": self.keyMenu,
			"red": self.wait_keyCancel,
			"green": self.overwriteM3U,
			"yellow": self.handleGroups,
			"blue": self.deleteEntry
		}, -1)

		if MediaInfoPresent:
			self.filelist_path = config.plugins.mediainfo.savetopath.value
		else:
			self.filelist_path = "/media/hdd/movie/"

		self.keyLocked = True
		self['title'] = Label("SimpleList")
		self['name'] = Label(_("Selection:"))
		self['F2'] = Label(_("Update PL"))
		self['F2'].hide()
		self['F3'] = Label(_("IPTV Genre"))
		self['F3'].hide()
		self['F4'] = Label(_("Delete PL"))
		self['F4'].hide()

		self.last_pl_number = config_mp.mediaportal.sp_pl_number.value
		self.last_videodir = config.movielist.last_videodir.value
		config.movielist.last_videodir.value = self.filelist_path
		self.last_selection = None
		self.filelist = []
		self.genreliste = None
		self.playlist_num = 1
		self.menu_level = 0
		self.last_menu_idx = 0
		self.ltype = ''
		self.m3u_title = None
		self.lastservice = None
		self.sp_option = ""
		self.logos = False
		self.group_list = None
		self.group_set = set()
		self.m3u_list = {}
		self.group_stype = 'all'
		self.m3u_file = None
		self.m3u_update_fn = None
		self.logo_base = None
		self.enableThumbs = None
		self.do_update = False
		self._update_task = task.LoopingCall(self.updateChanList)

		self.ml = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self['liste'] = self.ml

		self.onClose.append(self._onClose)

		self.onLayoutFinish.append(self.buildMenulist)

	def buildMenulist(self):
		self['F1'].setText(_("Exit"))
		self['ContentTitle'].setText(_('List overview'))
		self.genreliste = []
		self.genreliste.append(('1', _('Video List'), ''))
		path = config_mp.mediaportal.watchlistpath.value + 'mp_global_pl_*'
		list = glob.glob(path)
		for fn in list:
			n = int(re.search('mp_global_pl_(\d+)', fn).group(1))
			self.genreliste.append(('2', 'Global Playlist-%02d' % n, fn))

		self.m3u_list.clear()
		path = mp_globals.pluginPath + "/resources/"
		list = glob.glob(path + '*.m3u')
		for upath in list:
			fn = upath.split('/')[-1]
			self.m3u_list[fn] = upath
			wpath = config_mp.mediaportal.watchlistpath.value + fn
			if not fileExists(wpath) and not fileExists(wpath+'.del'):
				try:
					shutil.copyfile(upath, wpath)
				except:
					pass

		path = config_mp.mediaportal.watchlistpath.value + '*.m3u'
		list = glob.glob(path)
		for fn in list:
			if "_MP_Adult.m3u" in fn or "_XX" in fn:
				if config_mp.mediaportal.showporn.value:
					self.genreliste.append(('3', fn.split('/')[-1], fn))
				else:
					pass
			else:
				self.genreliste.append(('3', fn.split('/')[-1], fn))

		self.genreliste.sort(key=lambda t : t[0]+t[1].lower())

		if config_mp.mediaportal.showuseradditions.value:
			dpath = config_mp.mediaportal.watchlistpath.value

		self.ml.setList(map(self.simplelistListEntry, self.genreliste))
		self.keyLocked = False
		self['F2'].show()
		self['F4'].show()

	def loadFileList(self):
		self.ltype = 'sl_movies'
		self.session.openWithCallback(self.getSelection, MovieSelection, selectedmovie=self.last_selection)

	def getSelection(self, current):
		from ServiceReference import ServiceReference
		if current:
			if type(current) == tuple:
				current = current[0]
			sref = ServiceReference(current)
			self.last_selection = current
			url = sref.getPath()
			fn = sref.getServiceName()
			self.session.openWithCallback(self.loadFileList, SimplePlayer, [(fn, url)], showPlaylist=False, ltype=self.ltype, googleCoverSupp=config_mp.mediaportal.simplelist_gcoversupp.value, embeddedCoverArt=True)
		else:
			self.keyCancel()

	def globalList(self):
		self._stopUpdateLoop()
		self.ltype = 'sl_glob_playlist'
		self['ContentTitle'].setText("Global Playlist-%02d" % self.playlist_num)
		self.filelist = SimplePlaylistIO.getPL('mp_global_pl_%02d' % self.playlist_num)
		if self.filelist == []:
			self.keyLocked = True
			self.filelist.append((_("No entries found!"), "", "dump", None))
		else:
			self.keyLocked = False
		self.ml.setList(map(self._defaultlistleft, self.filelist))
		self['liste'].moveToIndex(0)

	def deleteEntry(self):
		if self.menu_level == 1 and self.ltype == 'sl_glob_playlist':
			if not self.filelist:
				self.session.open(MessageBoxExt, _("No playlist found"), MessageBoxExt.TYPE_INFO, timeout=2)
				return
			idx = self['liste'].getSelectedIndex()
			SimplePlaylistIO.delEntry('mp_global_pl_%02d' % self.playlist_num, self.filelist, idx)
			self.ml.setList(map(self._defaultlistleft, self.filelist))
		else:
			sel = self['liste'].getCurrent()[0][0]
			if sel in ('2', '3'):
				self.deletePL()

	def loadM3UList(self, m3ufile):
		self._stopUpdateLoop()
		self.ltype = 'sl_m3ulist'
		self.m3u_file = m3ufile
		self.m3u_title = m3ufile.split('/')[-1]
		ctitle = self.m3u_title + " (\"{0}/\")".format("/".join(m3ufile.split('/')[0:-1]))
		self['ContentTitle'].setText(ctitle)
		self['F3'].hide()
		self.filelist = []
		self.group_set.clear()
		self.group_list = [
				( _('Show all channels'), 'all')
			]
		self.sp_option = "MP3"
		self.logo_base = ""
		extm3u = extinf = tvg_infos = self.logos = False
		title = path = logo = ""
		tvg_data = None
		do_append = True
		first_line = None
		proxy_num = None
		self.do_update = False
		try:
			with open(m3ufile, "rU") as inf:
				for line in inf:
					line = line.strip()
					if not extm3u and '#EXTM3U' in line:
						first_line = line
						extm3u = True
						if '$' in line:
							options = line.split(',')[1:]
							for option in options:
								mode, attr = option.split('=')
								if mode == '$MODE':
									self.sp_option = attr
								elif mode == '$LOGOBASE':
									self.logo_base = attr
								elif mode == '$PROXY':
									proxy_num = attr
					elif  extm3u and not extinf and line.startswith('#EXTINF:'):
						m = re.search('\s*[-]*\d+(,|\s)(.+)', line[8:])
						if m:
							extinf = True
							ls = m.group(2).split(',')
							title = ls[-1]
							tvg = ls[0] if len(ls) > 1 else ''
							if 'tvg-id=' in tvg:
								tid = re.search('tvg-id="(.*?)"', tvg).group(1).replace('.ink','.nix').replace('_','.')
								cid = tvg_conv.get(tid)
								if cid: tid = tid.replace(tid,cid)
								epg_id = format(hash(tid.lower()) & sys.maxint, 'x')
								self.enableThumbs = True
								if 'tvg-logo=' in tvg:
									logo = self.logo_base + re.search('tvg-logo="(.*?)"', tvg).group(1)
								if 'group-title=' in tvg:
									grp = re.search('group-title="(.*?)"', tvg).group(1)
									self.do_update = True
									tvg_data = ('TVG','tvg-id',) + (epg_id, grp, logo)
									k = grp.lower()
									if k != self.group_stype and 'all' != self.group_stype:
										do_append = False

									if not k in self.group_set:
										self.group_set.add(k)
										self.group_list.append((_("Show \"{0}\" channels").format(grp.title()), k))
									tvg_infos = True
									m2 = re.search('\[COLOR\s(.*?)\]', title)
									tvg_data += (colors.get(m2.group(1), DEFAULT_COLOR),) if m2 else (DEFAULT_COLOR,)
									title = re.sub('(\[/*.*?\])', '', title)
								else: # Senderliste
									self.do_update = True
									tvg_data = ('TVG-LIST','tvg-id') + (epg_id, logo)
									if logo: logo = self.logo_base + logo
									m2 = re.search('\[COLOR\s(.*?)\]', title)
									tvg_data += (colors.get(m2.group(1), DEFAULT_COLOR),) if m2 else (DEFAULT_COLOR,)
									title = re.sub('(\[/*.*?\])', '', title)
									k = title.lower()
									if k != self.group_stype and 'all' != self.group_stype:
										do_append = False
							elif 'group-title=' in tvg: # other tvg pl typ
								k = re.search('group-title="(.*?)"', tvg).group(1).lower()
								if k != self.group_stype and 'all' != self.group_stype:
									do_append = False

								if not k in self.group_set:
									self.group_set.add(k)
									self.group_list.append((_("Show \"{0}\" channels").format(k.title()), k))
								tvg_infos = True
								m2 = re.search('\[COLOR\s(.*?)\]', title)
								tvg_data = (colors.get(m2.group(1), DEFAULT_COLOR),) if m2 else (DEFAULT_COLOR,)
								title = re.sub('(\[/*.*?\])', '', title)
							else:
								title = re.sub('(\[/*.*?\])', '', title)
								tvg_data = (DEFAULT_COLOR,)
						else:
							title = path = logo = ""
							extinf = False
							tvg_data = None
							do_append = True
							continue

					elif extm3u and extinf and line:
						if not config_mp.mediaportal.hlsp_enable.value:
							path = line.replace('|', '#')
						else:
							path = line
						if path.endswith('#m3u#'):
							path = path.replace('#m3u#', '')
							options = first_line.strip()
							return self.getPL(path, m3ufile, options)

					if extinf and path:
						if do_append:
							if logo:
								self.logos = True
								if not logo[:4] in ('http', 'file'):
									logo_base = TVG_LOGO_BASE if not 'iptv.ink' in path else TVG_INK_LOGO_BASE
									logo = logo_base + logo
							event = ""
							if proxy_num:
								ps = path.rsplit('|X-For',1)
								if proxy_num == '1':
									path = ps[0] + ' PROXY'
								elif proxy_num == '2' and len(ps) > 1:
									path = ps[0] + ' PROXY'
							self.filelist.append((title, path, logo, tvg_data, event))
						title = path = logo = ""
						extinf = False
						tvg_data = None
						do_append = True

		except IOError, e:
			printl(e,self,'E')

		if self.filelist == []:
			self.keyLocked = True
			self.filelist.append((_("No entries found!"), "", "", (DEFAULT_COLOR,), ''))
		else:
			self.keyLocked = False

		if not tvg_infos:
			self.group_stype = 'all'
		if len(self.group_set) > 0:
			self['F3'].show()

		self.updateChanList(True)
		self['liste'].moveToIndex(0)
		if self.logos:
			self.th_ThumbsQuery(self.filelist, 0, 1, 2, None, None, 1, 1, mode=0)
		if self.do_update:
			self._update_task.start(60, False)

	def updateChanList(self, blocking=False):
		if mutex.acquire(blocking):
			try:
				self.ml.setList(map(self.simpleListTVGListEntry, self.filelist))
			except:
				printl('Unexpected exception',self,'E')
			finally:
				mutex.release()

	def getPL(self, path, m3u_file, options):
		import urlparse, urllib
		from imports import InsensitiveDict
		self.keyLocked = True
		self.ml.setList(map(self._defaultlistleft, [(_("Please wait..."), "", "", None)]))
		headers = InsensitiveDict({
			'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'Accept-Language':'de,en-US;q=0.7,en;q=0.3'
			})
		def updateHeaders(headers, hs):
			if hs.startswith('{'):
				headers.update(eval(urllib.unquote(hs)))
			else:
				headers.update(dict(urlparse.parse_qsl(hs)))

		if ' headers=' in path:
			path, hs = path.rsplit(' headers=',1)
			try:
				updateHeaders(headers, hs)
			except Exception, e:
				return self.gotPLError(e)
		if '$HEADERS=' in options:
			soptions = options.split(',')
			options = [soptions[0]]
			for option in soptions[1:]:
				if option.startswith('$HEADERS='):
					hs = urllib.unquote(option.split('$HEADERS=')[-1])
					try:
						updateHeaders(headers, hs)
					except Exception, e:
						return self.gotPLError(e)
				else:
					options.append(option)
			options = ",".join(options)
		agent = headers.pop('user-agent', 'Enigma2 MediaPlayer')
		r_getPage(path, agent=agent, timeout=10, headers=headers.copy()).addCallback(self.gotPL, m3u_file, options).addErrback(self.gotPLError)

	def gotPL(self, pl, m3u_file, options):
		if '$NOCACHE=' in options:
			soptions = options.split(',')
			options = [soptions[0]]
			for option in soptions[1:]:
				if option.startswith('$NOCACHE='):
					fn = m3u_file.split('/')[-1]
					m3u_file = '/tmp/'+fn
				else:
					options.append(option)
			options = ",".join(options)

		def convBouquetToM3U(b):
			def get_lines_iter(c):
				for l in c.splitlines():
					if l.startswith('#NAME'):
						pass
					elif l.startswith('#'):
						yield l
					else:
						pass

			nm = url = None
			data = options + '\n'
			for l in get_lines_iter(b):
				if not nm and l.startswith('#SERV'):
					s = l.split(':')
					url = unquote(s[10]) if s and s[10] else 'None'
					nm = s[11].strip() if s and len(s) > 11 else None
				elif url and l.startswith('#DESC'):
					m = re.search('#DESCRIPTION:\s(.+)', l)
					nm = m.group(1).strip() if m else None

				if nm and url:
					data += '#EXTINF:0,'+nm+'\n'
					data += url+'\n'
					nm = url = None
			return data

		if '$CONV=' in options:
			opts = options.split(',')
			conv = grp = None
			if len(opts) > 1:
				options = (opts[0],)
				for opt in opts[1:]:
					if opt.startswith('$CONV'):
						conv = opt.split('=')[-1].strip()
					elif opt.startswith('$GROUP'):
						grp = opt.split('=')[-1].strip()
					else:
						options += (opt,)
				options = ",".join(options)

			if conv == 'FILMON':
				grp = grp or 'FilmOn'
				f = open(m3u_file, 'w')
				f.write(options+'\n')
				for m in re.finditer('channel_id="(.*?)">.*?<img.*?src="(.*?)".*? title="(.*?)"', re.search('<ul id="channels_ul"(.*?)</ul>', pl, re.S).group(1), re.S):
					cid, img, t = m.groups()
					f.write('#EXTINF:-1 tvg-id="-1" group-title="%s" tvg-logo="%s", [COLOR lightgrey]%s[/COLOR]\n' % (grp, img, t))
					f.write('http://www.filmon.tv/api-v2/channel/%s#filmon-stream#\n' % cid)
				f.close()
				self.loadM3UList(m3u_file)
			else:
				self.gotPLError(_('Error: No valid option in playlist'))
		elif '#EXTM3U' in pl[:10]:
			pl = re.sub('#EXTM3U.*', options, pl)
			f = open(m3u_file, 'wb')
			f.write(pl)
			f.close()
			self.loadM3UList(m3u_file)
		elif '#NAME' in pl[:10]:
			data = convBouquetToM3U(pl)
			f = open(m3u_file, 'wb')
			f.write(data)
			f.close()
			self.loadM3UList(m3u_file)
		else:
			self.gotPLError(_('Error: No valid playlist'))

	def gotPLError(self, result):
		printl(str(result),self,'E')
		self.filelist.append((_("Can't download playlist"), "", "", None))
		self.ml.setList(map(self._defaultlistleft, self.filelist))

	def keyMenu(self):
		self.session.open(SimplelistConfig)

	def keyOK(self):
		if self.keyLocked:
			return
		if self.menu_level == 1:
			if self.ltype == 'sl_glob_playlist':
				idx = self['liste'].getSelectedIndex()
				self.session.open(SimplePlayer, [], playIdx=idx, playList2=self.filelist, plType='global', ltype=self.ltype, playAll=True, googleCoverSupp=config_mp.mediaportal.simplelist_gcoversupp.value, useResume=False)
			elif self.ltype == 'sl_m3ulist':
				idx = self['liste'].getSelectedIndex()
				if 'TVG-LIST' in self.filelist[idx][3]: return
				force_hls_player = config_mp.mediaportal.hlsp_enable.value or self.filelist[idx][1].startswith('newtopia-stream')
				if self.filelist[idx][1] not in ('', 'None'):
					if force_hls_player and ('.m3u8' in self.filelist[idx][1])>0:
						if not config_mp.mediaportal.hlsp_enable.value:
							self.session.open(MessageBoxExt, _("If you want to play this stream, you have to activate the HLS-Player in the MP-Setup"), MessageBoxExt.TYPE_INFO)
							return
					if any(x in self.filelist[idx][1] for x in ('|', '={')):
						if not config_mp.mediaportal.hlsp_enable.value:
							self.session.open(MessageBoxExt, _("If you want to play this stream, you have to activate the HLS-Player in the MP-Setup"), MessageBoxExt.TYPE_INFO)
							return

					if self.do_update:
						self._update_task.stop()
					if config_mp.mediaportal.restorelastservice.value == "1" and not config_mp.mediaportal.backgroundtv.value:
						self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
					else:
						self.lastservice = None
					self.session.openWithCallback(self.restoreLastService, SimplePlayer, self.filelist, playIdx=idx, ltype=self.ltype, playAll=True, googleCoverSupp=config_mp.mediaportal.simplelist_gcoversupp.value, useResume=False, listTitle=self.m3u_title, playerMode=self.sp_option, cover=self.logos)
			elif self.ltype == 'sl_dm3ulist':
				self.keyLocked = True
				idx = self['liste'].getSelectedIndex()
				nm = self.filelist[idx][0]
				dpath = self.filelist[idx][1][1]
				if fileExists(dpath):
					list = (
							( _('Yes'), "1"),
							( _('No'), "0")
						)
					self.session.openWithCallback(self.cb_copyPL, ChoiceBoxExt, title=_("OK to overwrite \"{0}\" playlist?").format(nm), list = list)
				else:
					self.cb_copyPL((None,'1'))
		else:
			self['F1'].setText(_("Return"))
			self.last_menu_idx = self['liste'].getSelectedIndex()
			sel = self['liste'].getCurrent()[0][0]
			title = self['liste'].getCurrent()[0][1]
			self['ContentTitle'].setText(title)
			self.menu_level = 1
			self.group_stype = 'all'
			self.enableThumbs = None
			if sel == '1':
				self.loadFileList()
			elif sel == '3':
				self['F2'].hide()
				self['F4'].hide()
				fpath = self['liste'].getCurrent()[0][2]
				self.loadM3UList(fpath)
			elif sel in ('4', '5', '6', '7', '8', '9'):
				self.keyLocked = True
				self.ltype = 'sl_dm3ulist'
				ctitle = self['liste'].getCurrent()[0][2][3]
				self['ContentTitle'].setText(ctitle)
				self['F2'].hide()
				self['F3'].hide()
				self['F4'].hide()
				base_url = self['liste'].getCurrent()[0][2][0]
				path = base_url + self['liste'].getCurrent()[0][2][1]
				dpath = self['liste'].getCurrent()[0][2][2]
				self.ml.setList(map(self._defaultlistleft, [(_("Please wait..."), "", "", None)]))
				self.getExtPLList(path, base_url, ('/tmp/.hasbahca.de.txt', dpath), sel)
			else:
				self['F2'].hide()
				self.playlist_num = int(re.search('mp_global_pl_(\d+)', self['liste'].getCurrent()[0][2]).group(1))
				self.globalList()

	def getExtPLList(self, path, base_url, dpath, sel):
		if isfile(dpath[0]):
			f = open(dpath[0])
			data = f.read()
			f.close()
			self.downloadPLList(data, base_url, dpath[1], sel)
		else:
			twDownloadPage(path, dpath[0], timeout=10).addCallback(lambda ign: self.getExtPLList(path, base_url, dpath, sel)).addErrback(self.gotPLError)

	def cb_copyPL(self, answer):
		stype = answer and answer[1]
		if stype and stype == "1":
			try:
				idx = self['liste'].getSelectedIndex()
				dpath = self.filelist[idx][1][1]
				url = self.filelist[idx][1][0]
				nm = self.filelist[idx][0]
				mode = self.filelist[idx][1][2]
				m3u = "#EXTM3U%s\n#EXTINF:-1,Ext. Playlist\n%s#m3u#" % (mode, url)
				f = open(dpath, 'wb')
				f.write(m3u)
				f.close()
				self.session.open(MessageBoxExt, _("Playlist \"{0}\" copied.").format(nm), MessageBoxExt.TYPE_INFO, timeout=3)
			except:
				self.session.open(MessageBoxExt, _("Can't copy \"{0}\" playlist").format(nm), MessageBoxExt.TYPE_ERROR)
		self.keyLocked = False

	def downloadPLList(self, data, base_url, dpath, sel):
		self.filelist = []
		if data:
			tvg_data = (DEFAULT_COLOR,)
			if sel == '4':
				pass
			elif int(sel) in range(5, 9+1):
				def get_lines_iter(c):
					for l in c.splitlines():
						if l.startswith('#'):
							pass
						elif l.startswith('XXX') and not config_mp.mediaportal.showporn.value:
							pass
						else:
							yield l

				if sel == '5':
					m=re.search('(#\s+HasBahCa TV Listen)', data, re.S|re.I)
					a = m.start(1) if m else 0
				elif sel == '6':
					m=re.search('(#\s+HasBahCa Movie Listen)', data, re.S|re.I)
					a = m.start(1) if m else 0
				elif sel == '7':
					m=re.search('(#\s+HasBahCa Radio Listen)', data, re.S|re.I)
					a = m.start(1) if m else 0
				else: a = 0
				if a:
					b = data.find('##################\n', a)
					b = data.find('http', b) if b > 0 else -1
					b = data.find('##################\n', b) if b > 0 else -1
					lines = get_lines_iter(data[a:b])
					for l in lines:
						x, t, f, n = l.split(' ')[:4]
						mode = ',$MODE=IPTV' if t == 'TV' else ''
						self.filelist.append((n, (f, dpath+'_'+t+'_'+n+'.m3u', mode), "playlist.png", tvg_data))

		if self.filelist == []:
			self.filelist.append((_("No entries found!"), "", "", (DEFAULT_COLOR,)))
		else:
			self.keyLocked = False
		self.ml.setList(map(self.simpleListTVGListEntry, self.filelist))
		self['liste'].moveToIndex(0)

	def _onClose(self):
		config.movielist.last_videodir.value = self.last_videodir
		self._stopUpdateLoop()

	def _stopUpdateLoop(self):
		self.do_update = False
		self._update_task.stop()

	def _keyShowThumb(self):
		if self.enableThumbs:
			self.keyShowThumb()

	def wait_keyCancel(self):
		self._stopUpdateLoop()
		if not mpepg.isImporting:
			with mutex as locked:
				self.keyCancel()

	def keyCancel(self):
		if self.menu_level == 0:
			self.close()
		else:
			self['F1'].setText(_("Exit"))
			self.menu_level = 0
			self.keyLocked = False
			self['F2'].show()
			self['F3'].hide()
			self['F4'].show()
			self['ContentTitle'].setText(_('List overview'))
			if self.ltype == 'sl_dm3ulist':
				self.ltype = ''
				self.buildMenulist()
			else:
				self.ml.setList(map(self.simplelistListEntry, self.genreliste))
				self['liste'].moveToIndex(self.last_menu_idx)

	def restoreLastService(self):
		if config_mp.mediaportal.restorelastservice.value == "1" and not config_mp.mediaportal.backgroundtv.value:
			self.session.nav.playService(self.lastservice)
		else:
			self.session.nav.stopService()
		if self.do_update:
			self._update_task.start(60)

	def handleGroups(self):
		if not len(self.group_set): return
		sel = 0
		if not self.group_stype: self.group_stype = 'all'
		for me in self.group_list:
			if me[1] == self.group_stype: break
			sel += 1

		self.session.openWithCallback(self.cb_handleGroups, ChoiceBoxExt, title=_("IPTV Genre Selection"), list = self.group_list, selection=sel)

	def cb_handleGroups(self, answer):
		stype = answer and answer[1]
		if stype and self.group_stype != stype:
			self.group_stype = stype
			self.loadM3UList(self.m3u_file)

	def overwriteM3U(self):
		if not self.keyLocked and self.menu_level == 0:
			sel = self['liste'].getCurrent()[0][0]
			title = self['liste'].getCurrent()[0][1].split('/')[-1]
			if sel == '3':
				if title in self.m3u_list:
					list = (
							( _('Yes'), "1"),
							( _('No'), "0")
						)
					self.m3u_update_fn = title
					self.session.openWithCallback(self.cb_overwriteM3U, ChoiceBoxExt, title=_("Overwrite \"{0}\" with the MP playlist?").format(title), list = list)
				else:
					self.session.open(MessageBoxExt, _("No MP playlist \"{0}\" found").format(title), MessageBoxExt.TYPE_INFO, timeout=3)

	def cb_overwriteM3U(self, answer):
		stype = answer and answer[1]
		if stype and stype == "1":
			wpath = config_mp.mediaportal.watchlistpath.value + self.m3u_update_fn
			try:
				shutil.copyfile(self.m3u_list[self.m3u_update_fn], wpath)
				self.session.open(MessageBoxExt, _("Playlist \"{0}\" successfully updated").format(self.m3u_update_fn), MessageBoxExt.TYPE_INFO, timeout=3)
			except:
				self.session.open(MessageBoxExt, _("Can't update \"{0}\" playlist").format(self.m3u_update_fn), MessageBoxExt.TYPE_ERROR)

	def deletePL(self):
		if not self.keyLocked and self.menu_level == 0:
			sel = self['liste'].getCurrent()[0][0]
			title = self['liste'].getCurrent()[0][1].split('/')[-1]
			if sel in ('2', '3'):
				list = (
						( _('Yes'), "1"),
						( _('No'), "0")
					)
				self.m3u_update_fn = title
				self.session.openWithCallback(self.cb_deletePL, ChoiceBoxExt, title=_("OK to delete \"{0}\" playlist?").format(title), list = list)

	def cb_deletePL(self, answer):
		stype = answer and answer[1]
		if stype and stype == "1":
			try:
				path = self['liste'].getCurrent()[0][2]
				if self.m3u_list.has_key(path.split('/')[-1]):
					os.rename(path, path+'.del')
				else:
					os.remove(path)
			except:
				self.session.open(MessageBoxExt, _("Can't delete \"{0}\" playlist").format(self.m3u_update_fn), MessageBoxExt.TYPE_ERROR)
			else:
				self.buildMenulist()

class SimplelistConfig(MPSetupScreen, ConfigListScreenExt):

	def __init__(self, session):
		MPSetupScreen.__init__(self, session, skin='MP_PluginSetup')

		self['title'] = Label(_("SimpleList Configuration"))
		self['F4'] = Label('')
		self.list = []
		self.list.append(getConfigListEntry(_('Global playlist number'), config_mp.mediaportal.sp_pl_number))
		self.list.append(getConfigListEntry(_('Google coversupport'), config_mp.mediaportal.simplelist_gcoversupp))

		ConfigListScreenExt.__init__(self, self.list)
		self['setupActions'] = ActionMap(['MP_Actions'],
		{
			'ok': 		self.keySave,
			'cancel': 	self.keyCancel,
			"blue": 	self.importEPG,
		},-2)

		if config_mp.mediaportal.epg_enabled.value:
			self['F4'] = Label(_('Import EPG'))

	def importEPG(self):
		if config_mp.mediaportal.epg_enabled.value:
			self['F4'].setText(_('EPG import started'))
			mpepg.getEPGData().addCallback(self.importFini, self.session).addErrback(self.importFini, self.session, True)

	def importFini(self, msg, session, err=False):
		self['F4'].setText(_('EPG import finished'))
		printl(str(msg),self)
		msg = msg.replace('[MP EPG] ', '')
		session.open(MessageBoxExt, str(msg), type = MessageBoxExt.TYPE_INFO)