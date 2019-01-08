# -*- coding: utf-8 -*-
from Plugins.Extensions.MediaPortal.plugin import _
from Plugins.Extensions.MediaPortal.resources.imports import *
import Plugins.Extensions.MediaPortal.resources.mp_globals
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage
import random
gLogFile = None

class checkupdate:

	def __init__(self, session):
		self.session = session
		mp_globals.currentskin = config_mp.mediaportal.skin2.value

	def standbyCounterChanged(self, configElement):
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.leaveStandby)

	def leaveStandby(self):
		self.checkforupdate()

	def checkforupdate(self):
		update_agent = getUserAgent()
		update_url = "http://feed.newnigma2.to/mpgz/version.txt"
		twAgentGetPage(update_url, agent=update_agent, timeout=60).addCallback(self.gotUpdateInfo).addErrback(self.gotError)

	def gotError(self, error=""):
		printl(error,self,"E")
		return

	def gotUpdateInfo(self, html):
		if re.search(".*?<html", html):
			return
		self.html = html
		tmp_infolines = html.splitlines()
		remoteversion_ipk = re.sub('\D', '', tmp_infolines[0])
		remoteversion_deb = re.sub('\D', '', tmp_infolines[2])
		remote_mp_version = re.sub('\D', '', tmp_infolines[4])
		if mp_globals.isDreamOS:
			self.updateurl = tmp_infolines[3]
			remoteversion = remoteversion_deb
		else:
			self.updateurl = tmp_infolines[1]
			remoteversion = remoteversion_ipk

		if int(config.mpgz.version.value) < int(remoteversion) and int(config_mp.mediaportal.version.value) >= int(remote_mp_version):
			self.session.openWithCallback(self.startUpdate,MessageBoxExt,_("An update is available for the %s Plugin!\nDo you want to download and install it now?" % "mpgz"), MessageBoxExt.TYPE_YESNO, timeout=15, default=False)
			return
		else:
			return

	def startUpdate(self,answer):
		if answer is True:
			self.session.open(MPUpdateScreen,self.updateurl)
		else:
			return

class MPUpdateScreen(MPScreen):

	def __init__(self, session, updateurl):
		MPScreen.__init__(self, session, skin='MP_Update')
		self.session = session
		self.updateurl = updateurl

		self.ml = MenuList([], enableWrapAround=False, content=eListboxPythonMultiContent)
		self['mplog'] = self.ml
		self.list = []

		self['title'] = Label("mpgz Update")
		self.setTitle("mpgz Update")

		self.onLayoutFinish.append(self.__onLayoutFinished)

	def __onLayoutFinished(self):
		self.list.append((_("Starting update, please wait..."),))
		self.ml.setList(map(self.MPLog, self.list))
		self.ml.moveToIndex(len(self.list)-1)
		self.ml.selectionEnabled(False)
		self.startPluginUpdate()

	def startPluginUpdate(self):
		self.container=eConsoleAppContainer()
		if mp_globals.isDreamOS:
			self.container.appClosed_conn = self.container.appClosed.connect(self.finishedPluginUpdate)
			self.container.stdoutAvail_conn = self.container.stdoutAvail.connect(self.mplog)
			self.container.execute("apt-get update ; wget -q -O /tmp/foobar %s ; dpkg --install --force-overwrite /tmp/foobar ; apt-get -y -f install" % str(self.updateurl))
		else:
			self.container.appClosed.append(self.finishedPluginUpdate)
			self.container.stdoutAvail.append(self.mplog)
			self.container.execute("opkg update ; opkg install --force-overwrite " + str(self.updateurl))

	def finishedPluginUpdate(self,retval):
		self.container.kill()
		if retval == 0:
			config_mp.mediaportal.filter.value = "ALL"
			config_mp.mediaportal.filter.save()
			configfile_mp.save()
			self.session.openWithCallback(self.restartGUI, MessageBoxExt, _("%s successfully updated!\nDo you want to restart the Enigma2 GUI now?" % "mpgz"), MessageBoxExt.TYPE_YESNO)
		else:
			self.session.openWithCallback(self.returnGUI, MessageBoxExt, _("%s update failed! Check the update log carefully!" % "mpgz"), MessageBoxExt.TYPE_ERROR)

	def restartGUI(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
		self.close()

	def returnGUI(self, answer):
		self.close()

	def mplog(self,str):
		if "\n" in str:
			lines = str.split('\n')
			for line in lines:
				if line != "" and not "porn" in line:
					self.list.append((line,))
		else:
			self.list.append((str,))
		self.ml.setList(map(self.MPLog, self.list))
		self.ml.moveToIndex(len(self.list)-1)
		self.ml.selectionEnabled(False)
		self.writeToLog(str)

	def writeToLog(self, log):
		global gLogFile

		if gLogFile is None:
			self.openLogFile()

		now = datetime.datetime.now()
		gLogFile.write(str(log) + "\n")
		gLogFile.flush()

	def openLogFile(self):
		global gLogFile
		baseDir = "/tmp"
		logDir = baseDir + "/mpgz"

		now = datetime.datetime.now()

		try:
			os.makedirs(baseDir)
		except OSError, e:
			pass

		try:
			os.makedirs(logDir)
		except OSError, e:
			pass

		gLogFile = open(logDir + "/mpgz_update_%04d%02d%02d_%02d%02d.log" % (now.year, now.month, now.day, now.hour, now.minute, ), "w")