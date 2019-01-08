from Plugins.Plugin import PluginDescriptor
from Components.PluginComponent import plugins
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from enigma import iPlayableService, eServiceCenter, iServiceInformation
from Components.Label import Label
import ServiceReference
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from traceback import print_exc
from Tools.Import import my_import
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_PLUGIN
from Screens.MessageBox import MessageBox
from threading import Thread
from enigma import *
from Components.Console import Console
from os import popen, system, remove, listdir, chdir, getcwd, statvfs, mkdir, path, walk  
import sys
import os

sys.path.append('/usr/lib/python2.7')
sys.path.append('/usr/lib/python2.7/site-packages')
print '[PLUGINRELOAD] Python searchpath: ', sys.path
doit = True
PluginReLoadInstance = None

class PluginReLoadConfig(Screen):

    def __init__(self, session):
        try:
            Screen.__init__(self, session)
            self.session = session
            self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'green': self.cancel,
             'red': self.cancel,
             'cancel': self.cancel,
             'ok': self.keyOK}, -1)
            self['text'] = Label(_('Press OK to reload the plugins!\nPress EXIT to cancel!'))
            skin = '<screen position="center,center" size="400,75" title="OpenNFRWizard_PluginReLoad" >\n\t\t\t<widget name="text" position="0,0" zPosition="1" size="400,75" font="Regular;20" valign="center" halign="center" transparent="1" />\n\t\t\t</screen>'
            self.skin = skin
        except:
            print_exc()
            self.close(None)

        return

    def cancel(self):
        self.close()

    def keyOK(self):
              print 'OpenNFRWizard_PluginReLoad is loading Plugins'
              plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))                          
              self.session.open(MessageBox, _('The plugins were reloaded successfully!'), MessageBox.TYPE_INFO, timeout=5)
              self.close()
              print_exc()                                
             
class PluginReLoad:

    def __init__(self, session):
        try:
            self.session = session
            self.service = None
            self.onClose = []
            self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evUpdatedInfo: self.__evUpdatedInfo})
        except:
            print_exc()

        return

    def __evUpdatedInfo(self):
        global doit
        try:
            if doit is True:
                doit = False
                service = self.session.nav.getCurrentService()
                if service is not None:
                    print 'OpenNFRWizard_PluginReLoad is loading Plugins'
                    ret.start()
        except:
            print_exc()

        return


def main(session, **kwargs):
    global PluginReLoadInstance
    if PluginReLoadInstance is None:
        PluginReLoadInstance = PluginReLoad(session)
    return


def openconfig(session, **kwargs):
    session.open(PluginReLoadConfig)
