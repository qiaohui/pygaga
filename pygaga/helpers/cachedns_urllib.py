import cookielib
import httplib
import socket
try: # for python 2.5
    import ssl
except:
    pass
import urllib2
from gzip import GzipFile
from cStringIO import StringIO
import gflags
import zlib

from pygaga.helpers.cache import lru_cache
from pygaga.helpers.keepalive import HTTPHandler as KeepAliveHttpHandler

FLAGS = gflags.FLAGS

gflags.DEFINE_integer("timeout", 5, "url socket time")
gflags.DEFINE_integer("dnscache_size", 500, "max cache size of dns cache")
gflags.DEFINE_integer("dnscache_dura", 3600, "seconds dns cache will last")
gflags.DEFINE_integer("dnscache_retry_per_exception", 100, "counts that dns query exception cache last, then retry")

globalCookieJar = cookielib.CookieJar()

@lru_cache(maxsize=FLAGS.dnscache_size, maxsec=FLAGS.dnscache_dura, hold_exception=FLAGS.dnscache_retry_per_exception)
def CustomDnsResolver(host):
    return socket.gethostbyname(host)

class CustomDnsHTTPConnection(httplib.HTTPConnection):
    def connect(self):
        try:
            self.sock = socket.create_connection((CustomDnsResolver(self.host), self.port), FLAGS.timeout)
        except:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(FLAGS.timeout)
            self.sock.connect((CustomDnsResolver(self.host), self.port))

class CustomDnsHTTPSConnection(httplib.HTTPSConnection):
    def connect(self):
        try:
            sock = socket.create_connection((CustomDnsResolver(self.host), self.port), FLAGS.timeout)
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file)
        except:
            pass

class CustomDnsHTTPHandler(urllib2.HTTPHandler):
    def http_open(self,req):
        return self.do_open(CustomDnsHTTPConnection,req)

class CustomDnsHTTPSHandler(urllib2.HTTPSHandler):
    def https_open(self,req):
        return self.do_open(CustomDnsHTTPSConnection,req)

class ContentEncodingProcessor(urllib2.BaseHandler):
    """A handler to add gzip capabilities to urllib2 requests """

    # add headers to requests
    def http_request(self, req):
        req.add_header("Accept-Encoding", "gzip, deflate")
        return req

    # decode
    def http_response(self, req, resp):
        old_resp = resp
        # gzip
        if resp.headers.get("content-encoding") == "gzip":
            gz = GzipFile(
                    fileobj=StringIO(resp.read()),
                    mode="r"
                  )
            resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        # deflate
        if resp.headers.get("content-encoding") == "deflate":
            gz = StringIO( deflate(resp.read()) )
            resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)  # 'class to add info() and
            resp.msg = old_resp.msg
        return resp

# deflate support
def deflate(data):   # zlib only provides the zlib compress format, not the deflate format;
    try:               # so on top of all there's this workaround:
        return zlib.decompress(data, -zlib.MAX_WBITS)
    except zlib.error:
        return zlib.decompress(data)

def custom_dns_opener(cj=globalCookieJar, is_accept_ending=True, is_keepalive=False, ext_handlers=[]):
    handlers = [CustomDnsHTTPHandler,
            CustomDnsHTTPSHandler,
            urllib2.HTTPCookieProcessor(cj)]
    if is_accept_ending:
        handlers.append(ContentEncodingProcessor)
    if is_keepalive:
        handlers.append(KeepAliveHttpHandler())
    handlers.extend(ext_handlers)
    return urllib2.build_opener(*handlers)
