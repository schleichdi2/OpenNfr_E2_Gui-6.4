# -*- coding: utf-8 -*-
#
#    Copyright (c) 2015-2016 Billy2011, MediaPortal Team
#

import os
from os.path import isfile
import sys
import time
import gzip
import threading
import twisted
from twisted.internet import task, reactor
from twisted.internet.defer import Deferred, succeed
from twisted.web.client import downloadPage, getPage
from .xmltvconverter import XMLTVConverter
import log

channelEPGCache = {}
mutex = threading.Lock()
DEFAULT_URLS = ("http://epg.iptv.ink/iptv.epg.gz",)

class ImportThread(threading.Thread):

	def __init__(self, threadID, name, import_func, callback=None, finiback=None):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.import_func = import_func
		self.callback = callback
		self.finiback = finiback

	def run(self):
		print>>log, "[MP EPG] Starting " + self.name
		self.import_func()
		if self.callback: self.callback()
		print>>log, "[MP EPG] Exiting " + self.name
		if self.finiback: reactor.callFromThread(self.finiback)

class SimpleEPG(object):

	EPG_TMP_NAME = 'mp-iptv.epg_new.gz'
	EPG_DAT_NAME = 'mp-iptv.epg.dat'

	def __init__(self, epg_storage_path=None, epg_urls=DEFAULT_URLS):
		self.epg_path = epg_storage_path
		self.epg_urls = epg_urls
		self.has_epg = False
		self.ismodified = False
		path = '/tmp'
		if self.checkPath('/media/cf'):
			path='/media/cf'
		if self.checkPath('/media/usb'):
			path='/media/usb'
		if self.checkPath('/media/hdd'):
			path='/media/hdd'
		self.epg_tmp_file = os.path.join(path, self.EPG_TMP_NAME)
		self.epg_dat_file = os.path.join(path, self.EPG_DAT_NAME)
		self.isImporting = self.hasImported = False
		self.d_done = None
		self.d_msgs = []
		self.ev_count = self.ch_count = 0

	def checkUpdateTm(self, h=6):
		tm = int(time.time() - self.getLastImportTm())
		self.hasImported = False if tm > (3600 * h) and not self.isImporting else True

	def importEPGData(self):
		if not self.isImporting and isfile(self.epg_dat_file):
			ImportThread(1, "MP-EPGDAT-ImportThread-1", self.readEPG).start()
			self.d_done = Deferred()
			return self.d_done
		else:
			return succeed("[MP EPG] Nothing to import.")

	def getEPGData(self, u_idx=0):
		if not self.isImporting:
			self.checkUpdateTm(4)
			if self.hasImported:
				return succeed("[MP EPG] Recently ran an import already.")
		elif not u_idx:
			return succeed("[MP EPG] Currently an import is in progress.")

		self.isImporting = True
		self.url_idx = u_idx
		self.ev_count = self.ch_count = 0
		downloadPage(self.epg_urls[u_idx], self.epg_tmp_file, timeout=60).addCallback(lambda x: self.storeEPGData()).addErrback(self.importThreadFini)
		if not u_idx:
			self.d_done = Deferred()
			return self.d_done

	def importThreadFini(self, err=None):
		if err != None:
			msg = "[MP EPG] Import error:\n" + self.epg_urls[self.url_idx]
			msg += "\n[MP EPG] Can't download epg data:\n%s" % err
			print>>log, msg
			self.d_msgs.append(msg)
		else:
			msg = "[MP EPG] Import successfull finished:\n" + self.epg_urls[self.url_idx]
			msg += "\nNumber of imported channels: %d, events: %d" % (self.ch_count, self.ev_count)
			print>>log, msg
			self.d_msgs.append(msg)
		if (self.url_idx+1) < len(self.epg_urls):
			self.getEPGData(self.url_idx+1)
		else:
			self.saveEPG()
			self.isImporting = False
			self.has_epg = True if len(channelEPGCache) > 10 else False
			if self.has_epg: self.hasImported = True
			self.getLastImportTm()
			reactor.callFromThread(self.d_done.callback, "\n".join(self.d_msgs))
			self.d_msgs = []

	def getLastImportTm(self):
		if not self.isImporting and mutex.acquire(False):
			tm = channelEPGCache.get('last_update_tm', 0)
			mutex.release()
		else:
			tm = int(time.time())
		print>>log, '[MP EPG] Last update time:', time.strftime('%a %b %d %H:%M',time.localtime(tm))
		return tm

	def storeEPGData(self):
		ImportThread(1, "MP-EPG-ImportThread-1", self.importEPG, self.importThreadFini).start()

	def importEPG(self, deleteFile=True):
		if isfile(self.epg_tmp_file):
			mutex.acquire()
			try:
				file = gzip.open(self.epg_tmp_file, 'rb')
				conv = XMLTVConverter()
				if not self.ismodified: channelEPGCache.clear()
				now = int(time.time())
				now -= 7200
				for program in conv.enumFile(file):
					ch, event = program
					if not event[1] >= now: continue
					ch = format(hash(ch.lower()) & sys.maxint, 'x')
					if not channelEPGCache.has_key(ch):
						channelEPGCache[ch] = []
						channelEPGCache[ch].append(event)
						self.ev_count += 1
						self.ch_count += 1
					elif event[1] >= channelEPGCache[ch][-1][1]:
						channelEPGCache[ch].append(event)
						self.ev_count += 1
				file.close()
				if deleteFile:
					try:
						os.unlink(self.epg_tmp_file)
					except Exception, e:
						msg = "[MP EPG] Warning: Could not remove '%s' intermediate:\n%s" % (self.epg_tmp_file, str(e))
						print>>log, msg
						self.d_msgs.append(msg)
				self.ismodified = True
			except Exception, e:
				msg = 'EPG import error:',e
				print>>log, msg
				self.d_msgs.append(msg)
			finally:
				mutex.release()

	def getEvent(self, id, now=None):
		result = None
		try:
			p = channelEPGCache[id]
		except:
			pass
		else:
			if not now:
				now = int(time.time())

			def iter_events(p):
				for e in p:
					try:
						yield e
					except StopIteration:
						yield None
						break

			events = iter_events(p)
			for event in events:
				if event[1] >= now and now >= event[0]:
					#result = (id,event,events.next())
					result = (id,event,None)
					break

		return result

	def checkPath(self,path):
		f = os.popen('mount', "r")
		for l in f.xreadlines():
			if l.find(path)!=-1:
				return True
		return False

	def close(self):
		pass

	def saveEPG(self):
		global channelEPGCache
		if not self.ismodified: return
		mutex.acquire()
		now = int(time.time())
		channelEPGCache['last_update_tm'] = now
		print>>log, "[MP EPG] Saving EPG Data: " + self.epg_dat_file
		try:
			import cPickle as pickle
			picklefile = open(self.epg_dat_file, 'wb')
			pickle.dump(channelEPGCache, picklefile)
			picklefile.close()
			self.ismodified = False
		except Exception, e:
			msg = '[MP EPG] Error: saving EPG "%s":\n' % self.epg_dat_file, e
			print>>log, msg
			self.d_msgs.append(msg)
		finally:
			mutex.release()

	def readEPG(self):
		global channelEPGCache
		mutex.acquire()
		self.has_epg = False
		try:
			import cPickle as pickle
			picklefile = open(self.epg_dat_file, 'rb')
			channelEPGCache = pickle.load(picklefile)
			picklefile.close()
			self.ismodified = False
		except Exception, e:
			msg = '[MP EPG] Error: reading EPG "%s":\n' % self.epg_dat_file + e
			print>>log, msg
			self.d_msgs.append(msg)
			self.channelEPGCache.clear()
		else:
			msg = '[MP EPG] "%s" successfull read.' % self.epg_dat_file
			print>>log, msg
			self.d_msgs.append(msg)
		finally:
			self.has_epg = True if len(channelEPGCache) > 10 else False
			mutex.release()
			reactor.callFromThread(self.d_done.callback, "\n".join(self.d_msgs))
			self.d_msgs = []

mpepg = SimpleEPG()
