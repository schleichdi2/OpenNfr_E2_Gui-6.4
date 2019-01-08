# -*- coding: utf-8 -*-

class SimpleEvent:
	def __init__(self):
		self._ev_callback = None
		self._ev_on = False
		self._fini_callback = None

	def genEvent(self, fini_cb=None):
		#print "genEvent:"
		self._fini_callback = fini_cb
		if self._ev_callback:
			self._ev_on = False
			self._ev_callback()
		else:
			self._ev_on = True

	def addCallback(self, cb):
		#print "addCallback:"
		self._ev_callback=cb
		if self._ev_on:
			self._ev_on = False
			cb()

	def reset(self):
		#print "reset"
		self._ev_callback = None
		self._ev_on = False
		cb = self._fini_callback
		self._fini_callback = None
		if cb:
			cb()