# -*- coding: utf-8 -*-

from twisted import __version__
tmp = tuple([x for x in __version__.split('.')])
__TW_VER__ = []
for x in tmp:
	__TW_VER__.append(int(''.join([i for i in x if i.isdigit()])))
del tmp

import mp_globals
import sys
try:
	from enigma import eMediaDatabase
	mp_globals.isDreamOS = True
except:
	mp_globals.isDreamOS = False
if __TW_VER__ >= [14, 0, 0]:
	if mp_globals.isDreamOS:
		mp_globals.requests = False
	elif sys.version_info[:3] >= (2,7,9):
		mp_globals.requests = False
	else:
		mp_globals.requests = True
else:
	mp_globals.requests = True

if __TW_VER__ > [13, 0, 0]:
	from twisted.web import client
	from twisted.internet import endpoints
	from twisted.web.iweb import IBodyProducer

elif __TW_VER__ >= [11, 1, 0]:
	import tx
	from tx import client
	from tx import endpoints
	from tx.iweb import IBodyProducer
else:
	raise Exception("No HTTP 1.1 Support")

try:
	from OpenSSL import SSL
	from twisted.internet.ssl import ClientContextFactory
except:
	twAgent = False
	raise Exception("No SSL Support")
else:
	twAgent = True

try:
	from urlparse import urlunparse, urljoin, urldefrag
	from urllib import splithost, splittype
except ImportError:
	from urllib.parse import splithost, splittype, urljoin, urldefrag
	from urllib.parse import urlunparse as _urlunparse

	def urlunparse(parts):
		result = _urlunparse(tuple([p.decode("charmap") for p in parts]))
		return result.encode("charmap")

try:
	# available since twisted 14.0
	from twisted.internet._sslverify import ClientTLSOptions
except ImportError:
	ClientTLSOptions = None

import twisted
from twisted.web import http
from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred, succeed, fail
from twisted.web.http_headers import Headers
from twisted.web.http import PotentialDataLoss
from twisted.web.client import downloadPage, getPage
from twisted.internet.error import TimeoutError
from twisted.python import failure
from zope.interface import implements

def to_bytes(text, encoding=None, errors='strict'):
    """Return the binary representation of `text`. If `text`
    is already a bytes object, return it as-is."""
    if isinstance(text, bytes):
        return text
    if not isinstance(text, six.string_types):
        raise TypeError('to_bytes must receive a unicode, str or bytes '
                        'object, got %s' % type(text).__name__)
    if encoding is None:
        encoding = 'utf-8'
    return text.encode(encoding, errors)

def _parse(url, defaultPort=None):
	from urlparse import urlunparse
	url = url.strip()
	parsed = http.urlparse(url)
	scheme = parsed[0]
	path = urlunparse(('', '') + parsed[2:])

	if defaultPort is None:
		if scheme == 'https':
			defaultPort = 443
		else:
			defaultPort = 80

	host, port = parsed[1], defaultPort
	if ':' in host:
		host, port = host.split(':')
		try:
			port = int(port)
		except ValueError:
			port = defaultPort

	if path == '':
		path = '/'

	return scheme, '', host, port, path

class TwClientContextFactory(ClientContextFactory):
	"A SSL context factory which is more permissive against SSL bugs."

	def __init__(self):
		self.method = SSL.SSLv23_METHOD

	def getContext(self, hostname=None, port=None):
		ctx = ClientContextFactory.getContext(self)
		# Enable all workarounds to SSL bugs as documented by
		# http://www.openssl.org/docs/ssl/SSL_CTX_set_options.html
		ctx.set_options(SSL.OP_ALL)
		if hostname and ClientTLSOptions is not None: # workaround for TLS SNI
			ClientTLSOptions(hostname, ctx)
		return ctx

Agent = client.Agent
ProxyAgent = client.ProxyAgent
CookieAgent = client.CookieAgent
ResponseDone = client.ResponseDone
TCP4ClientEndpoint = endpoints.TCP4ClientEndpoint
downloadPage = twisted.web.client.downloadPage
getPage = twisted.web.client.getPage
HTTPConnectionPool = client.HTTPConnectionPool
BrowserLikeRedirectAgent = client.BrowserLikeRedirectAgent
ContentDecoderAgent = client.ContentDecoderAgent
GzipDecoder = client.GzipDecoder