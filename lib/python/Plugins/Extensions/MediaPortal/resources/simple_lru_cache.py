# -*- coding: utf-8 -*-

from debuglog import printlog as printl

class SimpleLRUCache:

	def __init__(self, size, cachepath):
		self.cache = []
		self.size = size
		self.cachepath = cachepath
		self.ismodified = False

	def __contains__(self, key):
		for x in self.cache:
			if x[0] == key:
				return True

		return False

	def __getitem__(self, key):
		for i in range(len(self.cache)):
			x = self.cache[i]
			if x[0] == key:
				del self.cache[i]
				self.cache.append(x)
				return x[1]

		raise KeyError

	def __setitem__(self, key, value):
		for i in range(len(self.cache)):
			x = self.cache[i]
			if x[0] == key:
				self.ismodified = True
				if i < (len(self.cache) - 1):
					x[1] = value
					del self.cache[i]
					self.cache.append(x)
				else:
					self.cache[-1][1] = value
				return

		if len(self.cache) == self.size:
			self.cache = self.cache[1:]

		self.cache.append([key, value])
		self.ismodified = True

	def __delitem__(self, key):
		for i in range(len(self.cache)):
			if self.cache[i][0] == key:
				del self.cache[i]
				self.ismodified = True
				return

		raise KeyError

	def resize(self, x=None):
		assert x > 0
		self.size = x
		if x < len(self.cache):
			del self.cache[:len(self.cache) - x]
			self.ismodified = True

	def saveCache(self):
		if not self.ismodified: return
		try:
			import cPickle as pickle
			picklefile = open(self.cachepath, 'w')
			pickle.dump(self.cache, picklefile)
			picklefile.close()
			self.ismodified = False
		except:
			printl('Error: saving cache "%s"' % self.cachepath,self,'E')

	def readCache(self):
		try:
			import cPickle as pickle
			picklefile = open(self.cachepath, 'r')
			self.cache = pickle.load(picklefile)
			picklefile.close()
			self.resize(self.size)
			self.ismodified = False
		except:
			printl('Error: reading cache "%s"' % self.cachepath,self,'E')
			self.cache = []
