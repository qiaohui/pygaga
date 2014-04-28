import math
import time
import logging
from pygaga.helpers.utils import round_data

logger = logging.getLogger('nlp')

class lazyncache:
    def __init__(self,func,cacheage=10):
        self.data = None
        self.func = func
        self.update = 0
        self.cacheage = cacheage

    def load(self):
        if self.update < time.time()-self.cacheage:
            self.data = self.func()
            self.update = time.time()
        return self.data

def loaddict(iter_wd2freq):
    '''
    >>> d = {'ok':10000,'failed':988,'no':2032}
    >>> round_data(loaddict(d.items())())
    ({'fa': {'failed': 31.9}, 'ok': {'ok': 8.95}, 'no': {'no': 5.76}}, {'a': -2.58, 'e': -2.58, 'd': -2.58, 'f': -2.58, 'i': -2.58, 'k': -0.26, 'l': -2.58, 'o': -0.08, 'n': -1.86})
    '''
    def doload():
        pref2wd2f = {}
        ch2f = {}
        total = 0
        for wd,freq in iter_wd2freq:
            if freq <= 1:
                logger.debug("loaddict skip %s %s" % (wd, freq))
                continue
            total += freq
            pref2wd2f.setdefault(wd[:2],{})[wd] = freq
            for ch in wd:
                ch2f[ch] = ch2f.get(ch,0)+freq
        logtotal = math.log(total)
        for _,wd2f in pref2wd2f.items():
            for wd,f in wd2f.items():
                wd2f[wd] = len(wd)*math.log(f)-logtotal # log(freq^len/total) ?
        for ch,f in ch2f.items():
            ch2f[ch] = math.log(f)-logtotal  # log(freq/total)
        logger.debug('pref2wd2f-size %s ch2f-size %s' % (len(pref2wd2f), len(ch2f)))
        return pref2wd2f,ch2f
    return doload

def lazy_dict(d):
    return lazyncache(loaddict(d),10000000)

def ngram(kw, encoding='utf-8', limit=0):
    '''
    >>> ngram('abcde abc')
    {u'abcd': 1, u'cde': 1, u'ab': 2, u'bc': 2, u'bcd': 1, u'de': 1, u'abcde': 1, u'bcde': 1, u'cd': 1, u'abc': 2}
    '''
    worddict = {}
    if not type(kw) is unicode:
        kw = kw.decode(encoding)
    kws = kw.split()
    for kw in kws:
        if len(kw) <= 2:
            worddict[kw] = worddict.get(kw, 0) + 1
            continue
        for l in range(2, len(kw) + 1):
            for i in range(len(kw) - l + 1):
                seg = kw[i:i + l]
                if limit > 0 and len(seg) > limit:
                    continue
                worddict[seg] = worddict.get(seg, 0) + 1
    return worddict

if __name__ == "__main__":
    import doctest
    doctest.testmod()
