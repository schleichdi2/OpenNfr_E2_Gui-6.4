# -*- coding: utf-8 -*-
from imports import *
from Plugins.Extensions.MediaPortal.resources.messageboxext import MessageBoxExt
from Plugins.Extensions.MediaPortal.resources.twagenthelper import twAgentGetPage, TwAgentHelper
from Screens.Screen import Screen

class realdebrid_oauth2(Screen):

	def __init__(self, session, link , calltype='link'):
		self.link = link
		self.calltype = calltype
		self.raccesstoken = config_mp.mediaportal.realdebrid_accesstoken.value
		self.rrefreshtoken = config_mp.mediaportal.realdebrid_refreshtoken.value
		self.rclient_id = config_mp.mediaportal.realdebrid_rclient_id.value
		self.rclient_secret = config_mp.mediaportal.realdebrid_rclient_secret.value
		self.rAPPid = "2BKDBPNPA4D3U"
		self.rdevicecode = ''
		self.mpversion = config_mp.mediaportal.version.value
		self.agent = None

		Screen.__init__(self, session)
		self.onLayoutFinish.append(self.getRealdebrid)

	def getRealdebrid(self, loop=False):
		self.agent = TwAgentHelper(headers={'User-Agent': 'E2 MediaPortal/%s' % self.mpversion,
											'Content-Type': 'application/x-www-form-urlencoded',
											'Authorization': 'Bearer %s' % self.raccesstoken
											})
		if self.calltype == 'link':
			self.getLink(loop)
		elif self.calltype == 'user':
			self.getUserInfo(loop)
		else:
			self.closeall()

	def getUserInfo(self, loop=False):
		if self.raccesstoken:
			url = "https://api.real-debrid.com/rest/1.0/user"
			self.agent.getWebPage(url).addCallback(self.getUserInfoData, loop).addErrback(self.getTokenError, loop).addErrback(self.noerrorload)
		else:
			url = 'https://api.real-debrid.com/oauth/v2/device/code?client_id=%s&new_credentials=yes' % self.rAPPid
			self.agent.getWebPage(url).addCallback(self.getAuth).addErrback(self.codeerror, 'getAuth code error')

	def getUserInfoData(self, data, loop):
		try:
			result = json.loads(data)
		except:
			self.session.open(MessageBoxExt, _("Real-Debrid: Error getting Userdata!"), MessageBoxExt.TYPE_INFO, timeout=5)
			self.closeall()
		else:
			if not 'error' in result:
				pmsg = "Real-Debrid.com"
				if 'username' in result: pmsg += "\nUser:\t%s" % str(result['username'])
				if 'type' in result: pmsg += "\nType:\t%s" % str(result['type'])
				if 'expiration' in result: pmsg += "\nExpires: \t%s" % str(result['expiration']).replace('T',' ').replace('.000Z','')
				url = "https://api.real-debrid.com/rest/1.0/traffic"
				self.agent.getWebPage(url).addCallback(self.getUserTrafficData, pmsg).addErrback(self.noerrorload)
			else:
				if not loop and result['error_code'] == 8:
					self.getRefreshToken()
				else:
					self.errorResult(result)

	def getUserTrafficData(self, data, pmsg=None):
		try:
			result = json.loads(data)
		except:
			self.session.open(MessageBoxExt, _("Real-Debrid: Error getting Userdata!"), MessageBoxExt.TYPE_INFO, timeout=3)
			self.closeall()
		else:
			if not 'error' in result:
				pmsg += "\nLimits:"
				for item in result:
					if 'type' in result[item] and item != 'remote':
						limittype = str(result[item]['type'])
						pmsg += "\n%s\t" % str(item)
						if limittype == 'links':
							if 'links' in result[item]: pmsg += "Used: %s links" % str(result[item]['links'])
							if 'limit' in result[item]: pmsg += "\tLimit: %s links" % str(result[item]['limit'])
							if 'reset' in result[item]: pmsg += "/%s" % str(result[item]['reset'])
						if limittype == 'gigabytes':
							if 'bytes' in result[item]: pmsg += "Used: %s MB" % str(result[item]['bytes']/1024/1024)
							if 'left' in result[item]: pmsg += " \tLimit: %s GB" % str(result[item]['left']/1024/1024/1024)
							if 'reset' in result[item]: pmsg += "/%s" % str(result[item]['reset'])
				self.session.open(MessageBoxExt, pmsg , MessageBoxExt.TYPE_INFO)
				self.closeall()
			else:
				self.session.open(MessageBoxExt, pmsg , MessageBoxExt.TYPE_INFO, timeout=10)
				self.errorResult(result)

	def errorResult(self, result):
		if 'error_code' in result:
			if result['error_code'] == 8:
				self.session.openWithCallback(self.removetokens, MessageBoxExt, _("Real-Debrid: Error %s. Do you want to remove AuthToken and AccessToken?" % str(result['error'])), MessageBoxExt.TYPE_YESNO)
			else:
				self.session.open(MessageBoxExt, _("Real-Debrid: Error %s" % str(result['error'])), MessageBoxExt.TYPE_INFO)
				self.closeall()
		else:
			self.closeall()

	def removetokens(self, answer):
		if answer is True:
			self.session.open(MessageBoxExt, _("Real-Debrid: AuthToken and AccessToken removed!"), MessageBoxExt.TYPE_INFO, timeout=5)
			config_mp.mediaportal.realdebrid_accesstoken.value = ''
			config_mp.mediaportal.realdebrid_accesstoken.save()
			self.raccesstoken = ''
			config_mp.mediaportal.realdebrid_refreshtoken.value = ''
			config_mp.mediaportal.realdebrid_refreshtoken.save()
		self.closeall()

	def getLink(self, loop=False):
		if self.raccesstoken:
			url = "https://api.real-debrid.com/rest/1.0/unrestrict/link"
			post = {'link': self.link}
			self.agent.getWebPage(url, method='POST', postdata=urlencode(post)).addCallback(self.getLinkData, loop).addErrback(self.getTokenError, loop).addErrback(self.noerrorload)
		else:
			url = 'https://api.real-debrid.com/oauth/v2/device/code?client_id=%s&new_credentials=yes' % self.rAPPid
			self.agent.getWebPage(url).addCallback(self.getAuth).addErrback(self.codeerror, 'getAuth code error')

	def getAuth(self, data):
		result = json.loads(data)
		self.rdevicecode = str(result['device_code'])
		verification_url = str(result['verification_url'])
		user_code = str(result['user_code'])
		self.session.openWithCallback(self.getAuthId, MessageBoxExt, _("Real-Debrid Authentication:\nTake a Browser and go to %(verification_url)s\nand enter the following code %(user_code)s.\nWhen done, press YES" % {'verification_url':verification_url, 'user_code':user_code}), MessageBoxExt.TYPE_YESNO, timeout=600)

	def getAuthId(self, answer, loopcount=0):
		if answer is True:
			url = 'https://api.real-debrid.com/oauth/v2/device/credentials?client_id=%s&code=%s' % (self.rAPPid, self.rdevicecode)
			self.agent.getWebPage(url).addCallback(self.getAuthIdData, loopcount).addErrback(self.getAuthIdDataError, loopcount).addErrback(self.codeerror)
		else:
			self.session.open(MessageBoxExt, _("Real-Debrid: Authentication aborted!"), MessageBoxExt.TYPE_INFO, timeout=3)
			self.closeall()

	def getAuthIdDataError(self, error, loopcount=0):
		loopcount += 1
		self.session.open(MessageBoxExt, _("Real-Debrid: Retry %s/6 to get authentication" % str(loopcount)), MessageBoxExt.TYPE_INFO, timeout=5)
		reactor.callLater(5, self.getAuthId, True, loopcount)
		raise error

	def getAuthIdData(self, data, loopcount=0):
		try:
			result = json.loads(data)
		except:
			result['error']
			self.closeall()
		else:
			if not 'error' in result:
				url = 'https://api.real-debrid.com/oauth/v2/token'
				self.rclient_id = str(result['client_id'])
				self.rclient_secret = str(result['client_secret'])
				config_mp.mediaportal.realdebrid_rclient_id.value = self.rclient_id
				config_mp.mediaportal.realdebrid_rclient_id.save()
				config_mp.mediaportal.realdebrid_rclient_secret.value = self.rclient_secret
				config_mp.mediaportal.realdebrid_rclient_secret.save()
				post = {'client_id': self.rclient_id, 'client_secret': self.rclient_secret, 'code': self.rdevicecode, 'grant_type': 'http://oauth.net/grant_type/device/1.0'}
				self.agent.getWebPage(url, method='POST', postdata=urlencode(post)).addCallback(self.getAuthIdDataToken).addErrback(self.noerrorload) #.addErrback(self.rapiaccesstoken)
			else:
				if loopcount < 6:
					loopcount += 1
					reactor.callLater(5, self.getAuthIdm, True, loopcount)
				else:
					self.session.open(MessageBoxExt, _("Real-Debrid: Error %s" % str(result['error'])), MessageBoxExt.TYPE_INFO, timeout=5)
					self.closeall()

	def getAuthIdDataToken(self, data):
		try:
			result = json.loads(data)
		except:
			self.session.open(MessageBoxExt, _("Real-Debrid: Error getting AuthIdDataToken! Please try again."), MessageBoxExt.TYPE_INFO, timeout=3)
		else:
			self.raccesstoken = str(result['access_token'])
			self.rrefreshtoken = str(result['refresh_token'])
			config_mp.mediaportal.realdebrid_accesstoken.value = self.raccesstoken
			config_mp.mediaportal.realdebrid_accesstoken.save()
			config_mp.mediaportal.realdebrid_refreshtoken.value = self.rrefreshtoken
			config_mp.mediaportal.realdebrid_refreshtoken.save()
			self.getRealdebrid(True)

	def getLinkData(self, data, loop):
		try:
			result = json.loads(data)
		except:
			self.session.open(MessageBoxExt, _("Real-Debrid: Error getting token!"), MessageBoxExt.TYPE_INFO, timeout=3)
			self.closeall()
		else:
			if not 'error' in result:
				if 'download' in result:
					downloadlink = str(result['download'])
				else:
					downloadlink = self.link
				self.closeall(downloadlink)
			else:
				if not loop and result['error_code'] == 8:
					self.getRefreshToken()
				else:
					self.errorResult(result)

	def getTokenError(self, error, loop):
		if not loop and error.value.status == '401':
			self.getRefreshToken()
		else:
			if error.value.status == '503':
				self.session.open(MessageBoxExt, _("Real-Debrid: Generation failed (dead link, limit reached, too many downloads, hoster not supported, ip not allowed)."), MessageBoxExt.TYPE_INFO, timeout=5)
				self.closeall()
			elif error.value.status == '401':
				self.session.open(MessageBoxExt, _("Real-Debrid: Bad token (expired, invalid)."), MessageBoxExt.TYPE_INFO, timeout=5)
				config_mp.mediaportal.realdebrid_accesstoken.value = ''
				config_mp.mediaportal.realdebrid_accesstoken.save()
				self.closeall()
			elif error.value.status == '403':
				self.session.open(MessageBoxExt, _("Real-Debrid: Permission denied (or account locked). Check the account status!"), MessageBoxExt.TYPE_INFO, timeout=5)
				self.closeall()
			else:
				self.codeerror(error)

	def getRefreshToken(self):
		url = 'https://api.real-debrid.com/oauth/v2/token'
		post = {'client_id': self.rclient_id, 'client_secret': self.rclient_secret, 'code': self.rrefreshtoken, 'grant_type': 'http://oauth.net/grant_type/device/1.0'}
		self.agent.getWebPage(url, method='POST', postdata=urlencode(post)).addCallback(self.getRefreshTokenData).addErrback(self.codeerror)

	def getRefreshTokenData(self, data):
		try:
			result = json.loads(data)
		except:
			config_mp.mediaportal.realdebrid_accesstoken.value = ''
			config_mp.mediaportal.realdebrid_accesstoken.save()
			self.codeerror('Realdebrid broken RefreshToken')
		if result.has_key('error_code') and result['error_code'] == 9:
			config_mp.mediaportal.realdebrid_accesstoken.value = ''
			config_mp.mediaportal.realdebrid_accesstoken.save()
			self.codeerror('Realdebrid broken RefreshToken')
		else:
			self.raccesstoken = str(result['access_token'])
			self.rrefreshtoken = str(result['refresh_token'])
			config_mp.mediaportal.realdebrid_accesstoken.value = self.raccesstoken
			config_mp.mediaportal.realdebrid_accesstoken.save()
			config_mp.mediaportal.realdebrid_refreshtoken.value = self.rrefreshtoken
			config_mp.mediaportal.realdebrid_refreshtoken.save()
			self.getRealdebrid(True)

	def closeall(self, downloadlink=None):
		self.close(downloadlink, self.link)

	def noerrorload(self, error):
		printl('[streams]: ' + str(error),'','E')

	def codeerror(self, error):
		printl('[streams]: ' + str(error),'','E')
		message = self.session.open(MessageBoxExt, _("Real-Debrid: Broken authentication, please report to the developers."), MessageBoxExt.TYPE_INFO, timeout=5)
		self.closeall()