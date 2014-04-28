import re,sys, math, htmllib
from pygaga.corpus import ch2pop

popnormal = 20.39 # math.exp(20.39) --> sum of all words freq. in samples

RE_NOT_CJK = re.compile("^[\x01-\x7e]+$")

def is_cjk(txt):
    return not RE_NOT_CJK.match(txt)

def ftencode(txt,encoding):
    if not isinstance(txt,unicode): return txt
    while 1:
        try: return txt.encode(encoding)
        except UnicodeEncodeError,e:
            txt = txt[:e.start]+txt[e.end:]

def faulttolerate_decode(txt,codec):
    alllen = len(txt)
    errlen = 0
    while True:
        try:
            return errlen*1.0/alllen,txt.decode(codec),codec
        except UnicodeDecodeError,exc:
            errlen += (exc.end - exc.start)
            txt = txt[:exc.start]+txt[exc.end+1:]
            if exc.end > 10000 and errlen*1.0/exc.end > 0.01:
                return errlen*1.0/exc.end,txt[:exc.start].decode(codec),codec

def autodecode3(txt,codeclst='gbk utf8 big5'):
    if isinstance(txt,unicode): return txt
    if not isinstance(txt,str): return str(txt)
    for codec in codeclst.split():
        try: return txt.decode(codec)
        except: pass
    alltry = sorted([faulttolerate_decode(txt,codec) for codec in 'gbk utf8'.split()])
    if len(txt) > 20:
        print 'autodecode3 error',[(err,codec) for err,ret,codec in alltry],(1,txt[:30])
    return alltry[0]

def autodecode(txt,codeclst='gbk utf8 big5'):
    x = autodecode3(txt,codeclst)
    if isinstance(x,tuple): return x[1]
    return x

def smartdecode2(txt):
    if not txt:
        return txt,'na'
    if isinstance(txt,unicode):
        return txt,'unicode'
    if not isinstance(txt,str):
        return txt,'na'
    if not is_cjk(txt):
        return txt.decode('latin'), 'latin'
    try:
        gbk = txt.decode('gbk')
    except:
        gbk = ''
    try:
        utf = txt.decode('utf8')
    except:
        utf = ''
    if not gbk and not utf:
        return autodecode3(txt)[1:]
    if not gbk:
        return utf,'utf8'
    if not utf:
        return gbk,'gbk'
    popgbk = sum([math.log(ch2pop.get(ch,1))-popnormal for ch in gbk])
    poputf = sum([math.log(ch2pop.get(ch,1))-popnormal for ch in utf])
    if popgbk < poputf:
        return utf,'utf8'
    else:
        return gbk,'gbk'
    return txt,'na'

def smartdecode(txt):
    return smartdecode2(txt)[0]

def decodeuni(txt):
    p = re.compile(r'(?P<unichar>&#\d{4,5};)')
    while True:
        m = p.search(txt)
        if m:
            found = m.group('unichar')
            try:
                uni = eval("u'\u%x'"%int(found[2:-1]))
                txt = txt.replace(found,uni)
            except: pass
        else:
            return txt

def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()

