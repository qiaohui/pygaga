
import simplejson
import urllib2

def call_rest(url):
    return simplejson.load(urllib2.urlopen(url))
