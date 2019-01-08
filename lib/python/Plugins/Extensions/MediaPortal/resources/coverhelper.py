# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.resources.imports import *
from twagenthelper import twDownloadPage

glob_screensaver_num = 0
glob_icon_num = 0
glob_last_cover = [None, None]

class CoverHelper:

	def __init__(self, cover, callback=None, nc_callback=None):
		self._cover = cover
		self.picload = ePicLoad()
		self._callback = callback
		self._nc_callback = nc_callback
		self.downloadPath = None
		self.err_nocover = True
		self.logofix = False

	def downloadPage(self, url, path, agent=None, cookieJar=None, headers=None):
		if not agent:
			agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
		return twDownloadPage(url, path, timeout=20, agent=agent, cookieJar=cookieJar, headers=headers)

	def closeFile(self, result, f):
		f.close()
		return result

	def checkFilesize(self, data):
		if not data:
			raise Exception("Size error")
		else:
			return data

	def getCover(self, url, download_cb=None, agent=None, cookieJar=None, screensaver=False, bgcover=False, headers=None):
		self.bgcover = bgcover
		self.screensaver = screensaver
		if self.screensaver:
			self.COVER_PIC_PATH = "/tmp/.Screensaver%d.jpg"
			self.NO_COVER_PIC_PATH = "/images/none.png"
			self._no_picPath = "%s%s" % (mp_globals.pluginPath, self.NO_COVER_PIC_PATH)
		else:
			self.COVER_PIC_PATH = "/tmp/.Icon%d.jpg"
			if self.bgcover:
				self.NO_COVER_PIC_PATH = "/images/none.png"
				self._no_picPath = "%s%s" % (mp_globals.pluginPath, self.NO_COVER_PIC_PATH)
			else:
				self.NO_COVER_PIC_PATH = "/images/default_cover.png"
				self._no_picPath = "%s%s" % (mp_globals.pluginPath, self.NO_COVER_PIC_PATH)
		global glob_screensaver_num
		global glob_icon_num
		global glob_last_cover
		self.logofix = False
		if url:
			if url.startswith('http'):
				if glob_last_cover[0] == url and glob_last_cover[1] and not self.screensaver:
					self.showCoverFile(glob_last_cover[1])
					if download_cb:
						download_cb(glob_last_cover[1])
				else:
					if self.screensaver:
						glob_screensaver_num = (glob_screensaver_num + 1) % 2
						self.downloadPath = self.COVER_PIC_PATH % glob_screensaver_num
					else:
						glob_icon_num = (glob_icon_num + 1) % 2
						glob_last_cover[0] = url
						glob_last_cover[1] = None
						self.downloadPath = self.COVER_PIC_PATH % glob_icon_num
					d = self.downloadPage(url, self.downloadPath, agent=agent, cookieJar=cookieJar, headers=headers)
					d.addCallback(self.showCover)
					if download_cb:
						d.addCallback(self.cb_getCover, download_cb)
					d.addErrback(self.dataErrorP)
			elif url.startswith('file://'):
				logopath = (config_mp.mediaportal.iconcachepath.value + "logos")
				if logopath in url:
					self.logofix = True
				self.showCoverFile(url[7:])
				if download_cb:
					download_cb(url[7:])
			else:
				self.showCoverNone()
				if download_cb:
					download_cb(self._no_picPath)
		else:
			self.showCoverNone()
			if download_cb:
				download_cb(self._no_picPath)

	def cb_getCover(self, result, download_cb):
		download_cb(result)

	def dataErrorP(self, error):
		printl(error,self,'E')
		self.showCoverNone()

	def showCover(self, picfile):
		if picfile == 'cancelled':
			return self.dataErrorP(picfile)
		else:
			self.showCoverFile(picfile)
		if not self.screensaver:
			glob_last_cover[1] = picfile
		return picfile

	def showCoverNone(self):
		if not self.err_nocover:
			return
		else:
			self.err_nocover = False

		if self._nc_callback:
			self._cover.hide()
			self._nc_callback()
		else:
			self.showCoverFile(self._no_picPath)

		return(self._no_picPath)

	def showCoverFile(self, picPath, showNoCoverart=True):
		if self.logofix and not mp_globals.isDreamOS:
			try:
				conv_path = '/tmp/mediaportal/conv'
				try:
					os.makedirs(conv_path)
				except OSError, e:
					pass
				cover_file = conv_path + '/' + picPath.split('/')[-1]
				if not fileExists(cover_file):
					from PIL import Image
					im = Image.open(picPath)
					im.load()
					size = self._cover.instance.size()
					basewidth = size.width()
					wpercent = (basewidth / float(im.size[0]))
					hsize = int((float(im.size[1]) * float(wpercent)))
					im = im.resize((basewidth, hsize), Image.ANTIALIAS)
					alpha = im.split()[-1]
					im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
					mask = Image.eval(alpha, lambda a: 255 if a <=128 else 0)
					im.paste(255, mask)
					im.save(cover_file, transparency=255, optimize=True)
					picPath = cover_file
				else:
					picPath = cover_file
			except Exception as e:
				printl(e,self,"E")
		if fileExists(picPath):
			try:
				self._cover.instance.setPixmap(gPixmapPtr())
				scale = AVSwitch().getFramebufferScale()
				size = self._cover.instance.size()
				if mp_globals.fakeScale and not self.logofix:
					self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, "#00000000"))
				else:
					self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, "#FF000000"))
				self.updateCover(picPath)
			except AttributeError:
				pass
		else:
			printl("Coverfile not found: %s" % picPath, self, "E")
			if showNoCoverart and picPath != self._no_picPath:
				self.showCoverFile(self._no_picPath)

		if self._callback:
			self._callback()

	def updateCover(self, picPath):
		if mp_globals.isDreamOS:
			res = self.picload.startDecode(picPath, False)
		else:
			res = self.picload.startDecode(picPath, 0, 0, False)

		if not res:
			ptr = self.picload.getData()
			if ptr != None:
				w = ptr.size().width()
				h = ptr.size().height()
				ratio = float(w) / float(h)
				if self._nc_callback and ratio > 1.05:
					self.showCoverNone()
				else:
					self._cover.instance.setPixmap(ptr)
					if not self.bgcover:
						self._cover.show()
				return

		self.showCoverNone()