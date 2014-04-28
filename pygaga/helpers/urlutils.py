# coding: utf-8
import logging
import socket
import urllib2
import time
import cookielib
from urllib2 import urlparse
from urllib2 import HTTPError, URLError
from lxml import etree
from lxml.html import soupparser, HTMLParser
from cookielib import MozillaCookieJar
from cStringIO import StringIO

from pygaga.helpers.cachedns_urllib import custom_dns_opener

DEFAULT_UA="Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)"

urllib2.install_opener(custom_dns_opener())

logger = logging.getLogger("urlutils")

def safe_get(d, k):
    try:
        return d[k][0]
    except:
        return ""

def get_qs(url):
    """
    >>> get_qs("http://abc.com/a?a=123&b=%2b9")
    {'a': ['123'], 'b': ['+9']}
    """
    try:
        return urlparse.parse_qs(urlparse.urlparse(url).query)
    except:
        return {}

def get_url_arg(url, arg):
    """
    >>> get_url_arg("http://abc.com/a?a=123&b=%2b9", "b")
    '+9'
    """
    try:
        return safe_get(get_qs(url), arg)
    except:
        return ""

def get_query_arg(qs, arg):
    """
    >>> get_query_arg("a=123&b=%2b9", "b")
    '+9'
    """
    try:
        return safe_get(urlparse.parse_qs(qs), arg)
    except:
        return ""

def get_cookie_value(cookies_path, key):
    content = open(cookies_path).readlines()
    for line in content:
        values = line.strip().split()
        if values[-2] == key:
            return values[-1]
    return None

class SessionCookiePolicy(cookielib.DefaultCookiePolicy):

    def return_ok_expires(self, cookie, request):
        if cookie.is_expired(self._now) and cookie.expires != 0:
            #_debug("   cookie expired")
            return False
        return True

class FirefoxCookieJar(MozillaCookieJar):
    magic_re = ".*"

    def load(self, filename=None, ignore_discard=False, ignore_expires=False):
        """Load cookies from a file."""
        if filename is None:
            if self.filename is not None: filename = self.filename
            else: raise ValueError("Cookie filename is None")

        f = open(filename)
        f = StringIO("#\n" + f.read().replace('\r\n', '\n'))
        try:
            self._really_load(f, filename, ignore_discard, ignore_expires)
        finally:
            f.close()

def get_cookie_opener(cookiefile=None, is_accept_ending=False, is_keepalive=False, ext_handlers=[]):
    cj = FirefoxCookieJar(policy=SessionCookiePolicy())
    if cookiefile:
        cj.load(cookiefile, ignore_expires=True, ignore_discard=True)
    return custom_dns_opener(cj, is_accept_ending=is_accept_ending, is_keepalive=is_keepalive, ext_handlers=ext_handlers)

def post(url, data, headers = {'User-Agent' : DEFAULT_UA}, cookiefile=None, is_accept_ending=False, is_keepalive=False, ext_handlers=[]):
    u = None
    result = None
    req = urllib2.Request(url, data, headers=headers)
    if cookiefile:
        opener = get_cookie_opener(cookiefile, is_accept_ending=is_accept_ending, is_keepalive=is_keepalive, ext_handlers=ext_handlers)
        u = opener.open(req)
    else:
        u = urllib2.urlopen(req)
    result = u.read()
    u.close()
    return result

class BannedException(Exception):
    def __init__(self, value):
        self.value = value

def download(url, headers = {'User-Agent' : DEFAULT_UA}, rethrow=False,
            max_retry=0, fn_is_banned=lambda x:False, cookiefile=None, throw_on_banned=False):
    retry = 0
    done = False
    data = None
    if not url:
        return data
    while retry <= max_retry and not done:
        try:
            logger.debug("downloading %s", url)
            req = urllib2.Request(url, headers=headers)
            u = None
            if cookiefile:
                opener = get_cookie_opener(cookiefile)
                u = opener.open(req)
            else:
                u = urllib2.urlopen(req)
            data = u.read()
            u.close()
            if not fn_is_banned(data):
                done = True
            else:
                if throw_on_banned:
                    raise BannedException(data)
                retry += 1
                wait_time = (retry*2) * 10
                logger.warn("Banned len %s, waiting %s", len(data), wait_time)
                time.sleep(wait_time)
        except ValueError, e:
            logger.info("download %s url value error %s", url, e.message)
            done = True
            if rethrow:
                raise e
        except HTTPError, e1:
            logger.info("download %s failed http code: %s", url, e1.code)
            done = True
            if rethrow:
                raise e1
        except URLError, e2:
            logger.info("download %s failed url error: %s", url, e2.reason)
            done = True
            if rethrow:
                raise e2
        except socket.timeout, e3:
            logger.info("download %s failed socket timeout", url)
            retry += 1
            time.sleep(min(1.0*retry, 10.0))
            if rethrow:
                raise e3
    return data

def parse_html(html, encoding='utf8'):
    if not html:
        return html
    if type(html) != unicode:
        html = html.decode(encoding)
    try:
        html_obj = etree.XML(html)
    except:
        try:
            parser = HTMLParser()
            parser.feed(html)
            html_obj = parser.close()
        except:
            try:
                html_obj = etree.HTML(html)
            except:
                html_obj = soupparser.fromstring(html)
    return html_obj

def download_and_parse(url, headers = {'User-Agent' : DEFAULT_UA}, encoding='utf8'):
    return parse_html(download(url, headers), encoding)
