# -*- coding: utf-8 -*-
import json
import requests

operations = {'funk':'f058a27469d8b709c3b9db648cae47c2','spiegeltv':'dd070e3baf94dc2de0940e08291c6075'}
channelId = {'funk':'741','spiegeltv':'748'}
origin = {'funk':'https://www.funk.net','spiegeltv':'http://www.spiegel.tv'}

base_url = 'https://api.nexx.cloud/v3/'

def getVideoUrl(id, downld, operation='funk'):
	try:
		cid = str(getSession(operation))
		s = requests.session()
		page = s.get(base_url + channelId[operation] + '/videos/byid/' + id + '?additionalfields=language%2Cchannel%2Cactors%2Cstudio%2Clicenseby%2Cslug%2Csubtitle%2Cteaser%2Cdescription&addInteractionOptions=1&addStatusDetails=1&addStreamDetails=1&addCaptions=1&addScenes=1&addHotSpots=1&addBumpers=1&captionFormat=data', headers=_header(operation,cid))
		response = page.content
		j = json.loads(response)
		stream_data = j["result"]['streamdata']
		cdn = j["result"]['streamdata']['cdnType']
		if cdn == "azure":
			azure_locator = stream_data['azureLocator']
			AZURE_URL = 'http://nx%s%02d.akamaized.net/'
			def get_cdn_shield_base(shield_type='', prefix='-p'):
				for secure in ('', 's'):
					cdn_shield = stream_data.get('cdnShield%sHTTP%s' % (shield_type, secure.upper()))
					if cdn_shield:
						return 'http%s://%s' % (secure, cdn_shield)
				else:
					return
			azure_progressive_base = get_cdn_shield_base('Prog', '-d')
			if not azure_progressive_base and not j['result']['protectiondata'].has_key('tokenHLS'):
				azure_progressive_base = get_cdn_shield_base()
			if azure_progressive_base:
				azure_file_distribution = stream_data.get('azureFileDistribution')
				streams = []
				if azure_file_distribution:
					afd = azure_file_distribution.split(',')
					if afd:
						for fd in afd:
							ss = fd.split(':')
							if len(ss) == 2:
								bw = int(ss[0])
								if bw:
									f = ('%s%s/%s_src_%s_%d.mp4' % (str(azure_progressive_base), str(azure_locator), id, str(ss[1]), bw), bw)
									if not "_src_2560x" in f[0]:
										if not "_src_3840x" in f[0]:
											streams.append(f)
				streams.sort(key=lambda x: x[1])
				return streams[-1][0]
			elif downld:
				return downld
			else:
				try:
					tokenHLS = '?hdnts=' + str(j['result']['protectiondata']['tokenHLS'])
					HLS = 'http://' + str(j['result']['streamdata']['cdnShieldHTTP']) + str(j['result']['streamdata']['azureLocator']) + '/' + str(j['result']['general']['ID']) + '_src.ism/Manifest(format=m3u8-aapl)' + tokenHLS
					return HLS
				except:
					return None
		else:
			streams = []
			hash = str(j['result']['general']['hash'])
			ps = str(stream_data['originalDomain'])
			if str(stream_data['applyFolderHierarchy']) == '1':
				s = ('%04d' % int(id))[::-1]
				ps += '/%s/%s' % (s[0:2], s[2:4])
			ps += '/%s/%s_' % (id, hash)
			afd = stream_data.get('azureFileDistribution').split(',')
			if str(stream_data['cdnProvider']) == 'ce':
				urlbase = 'http://' + str(stream_data['cdnPathHTTP']) + ps
				for fd in afd:
					ss = fd.split(':')
					if len(ss) == 2:
						bw = int(ss[0])
						if bw:
							f = ('%s%s_%s.mp4' % (urlbase, str(ss[1]), bw), bw)
							streams.append(f)
			if len(streams) > 0:
				streams.sort(key=lambda x: x[1])
				return streams[-1][0]
			else:
				return None
	except:
		return None

def getSession(operation):
	try:
		s = requests.session()
		page = s.get(base_url + channelId[operation] + '/session/init?nxp_devh=1%3A1498445517%3A395527', headers=_header())
		response = page.content
		j = json.loads(response)
		return j['result']['general']['cid']
	except:
		return None

def _header(operation=False,c=False):
	header = {}
	header['Accept'] = '*/*'
	header['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
	header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
	header['Accept-Encoding'] = 'gzip, deflate'
	header['Host'] = 'api.nexx.cloud'
	if operation:
		header['Origin'] = origin[operation]
		if not c:
			c = cid
		header['X-Request-CID'] = c
		header['X-Request-Token'] = operations[operation]
	else:
		header['X-Request-Enable-Auth-Fallback'] = '1'
	return header