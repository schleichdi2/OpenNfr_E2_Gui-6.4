# -*- coding: utf-8 -*-
import os
from enigma import eTimer
from Components.config import config
from Components.Element import cached
from Tools.Directories import fileExists
from twisted.web.client import downloadPage
from Components.Converter.Converter import Converter

TMP_FILE = '/tmp/NFRversion.txt'
URL = 'http://dev.nachtfalke.biz/nfr/feeds/lastrelease.txt'

class NFRUpdate(Converter, object):
	def __init__(self, type):
		Converter.__init__(self, type)
                
                if type == 'Update':
                   self.type = 1

                self.check_timer = eTimer()
                self.check_timer.callback.append(self.get)
                self.check_timer.start(30000)
	
	@cached
	def getText(self):
            self.info = self.look('1')
            return str(self.info)

	text = property(getText)

        @cached
	def getBoolean(self):
	    self.info = self.look('2')
            return self.info

	boolean = property(getBoolean)

        def get(self):        
            downloadPage(URL, TMP_FILE).addErrback(self.error)

        def look(self, what):
            #box_version = config.plugins.SevenHD.version.value
            version = os.popen("cat /etc/version").read()
            box_version = version.rstrip()
            
            if not fileExists(TMP_FILE):
               self.get()
            
            try:
               content = os.popen("cat %s" % TMP_FILE).read()
	    except IOError:
	       content = box_version
	       
            version = box_version
            new_version = content

            version = version.rstrip()
            online_version = content.rstrip()
	    
            if int(version) < int(online_version):
                if str(what) == str('1'):   
                   self.update_available = 'Last Version on Server ' + str(new_version)
                else:
                   self.update_available = True
            else:
                if str(what) == str('1'):   
                   self.update_available = 'Last Version on Server ' + str(box_version)
                else:
                   self.update_available = False

            return self.update_available
        
        def error(self, error):
            box_version = config.plugins.SevenHD.version.value
            os.system('echo "' + box_version + '" > ' + TMP_FILE)

        def changed(self, what):
	    Converter.changed(self, (self.CHANGED_POLL,))
