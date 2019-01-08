# -*- coding: utf-8 -*-
from Components.Pixmap import Pixmap
from Components.GUIComponent import GUIComponent
from config import config_mp

class PixmapExt(Pixmap):

	def execBegin(self):
		GUIComponent.execBegin(self)
		self.instance.setShowHideAnimation(config_mp.mediaportal.animation_coverart.value)