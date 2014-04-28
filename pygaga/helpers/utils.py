import socket
import struct
import os
import traceback
import simplejson
import re
from itertools import dropwhile
try:
    from subprocess import Popen, PIPE
    use_subprocess = True
except:
    import popen2
    use_subprocess = False

def all_matched(fn, iterable):
    for i in iterable:
        if not fn(i):
            return False
    return True

def takelastn(data_points, n, filter_fn=lambda x: not x[0]):
    pos = 0
    for dp in dropwhile(filter_fn, reversed(data_points)):
        pos += 1
        if pos > n:
            return
        yield dp

def get_num_val(s, key):
    """
    Search key from string, find value, format a=b,'a'='b','a':'b',a:\"b\"
    """
    r = re.compile(r'(?=\b)\\?(\'|")?' + key + r'\\?(\'|")?\s*(:|=)\s*\\?(\'|")?([0-9\.]+)\\?(\'|")?\b', re.M|re.S)
    m = r.search(s)
    if m:
        return m.group(5)
    else:
        return None

def get_val(s, key):
    """
    Search key from string, find value, format a=b,'a'='b','a':'b',a:\"b\"
    """
    r = re.compile(r'(?=\b)\\?(\'|")?' + key + r'\\?(\'|")?\s*(:|=)\s*\\?(\'|")?([^\'"; ]+)\\?(\'|")?\b', re.M|re.S)
    m = r.search(s)
    if m:
        return m.group(5)
    else:
        return None

def extract_jsonstr_from_html(html, lead):
    jsonp = html[html.find(lead):]
    jsonstr = re.compile('([^\(]+\()([^\)]*)(\).*)', re.M|re.S).sub(r'\g<2>', jsonp)
    return jsonstr

def extract_jsonstr_from_jsonp(jsonp):
    return re.compile('([^\(]+\()(.*)(\)\s*)', re.M|re.S).sub(r'\g<2>', jsonp)

def extract_json_from_html(html, lead):
    jsonstr = extract_jsonstr_from_html(html, lead)
    return simplejson.loads(jsonstr)

def extract_json_from_jsonp(jsonp):
    """
    >>> extract_json_from_jsonp('TOP.io.jsonpCbs.t326b246538def({"item":3})')
    {'item': 3}
    """
    jsonstr = extract_jsonstr_from_jsonp(jsonp)
    return simplejson.loads(jsonstr)

def pid_exists(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False

def get_pid_running_seconds(pid):
    proc = Popen(['ps','-eo','pid,etime'], stdout=PIPE)
    proc.wait()
    results = proc.stdout.readlines()
    for result in results:
        try:
            result.strip()
            if result.split()[0] == pid:
                pidInfo = result.split()[1]
                break
        except IndexError:
            pass
    else:
        return None
    pidInfo = [result.split()[1] for result in results
               if result.split()[0] == pid][0]
    pidInfo = pidInfo.partition("-")
    if pidInfo[1] == '-':
        days = int(pidInfo[0])
        rest = pidInfo[2].split(":")
        hours = int(rest[0])
        minutes = int(rest[1])
        seconds = int(rest[2])
    else:
        days = 0
        rest = pidInfo[0].split(":")
        if len(rest) == 3:
            hours = int(rest[0])
            minutes = int(rest[1])
            seconds = int(rest[2])
        elif len(rest) == 2:
            hours = 0
            minutes = int(rest[0])
            seconds = int(rest[1])
        else:
            hours = 0
            minutes = 0
            seconds = int(rest[0])
    return days*24*3600 + hours*3600 + minutes*60 + seconds

def readcmd(cmd,stdin=''):
    fout = fin = ferr = None
    try:
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        (fin, fout, ferr) = (p.stdin, p.stdout, p.stderr)
    except:
        if not use_subprocess:
            fout, fin, ferr = popen2.popen3(cmd)
    print >> fin, stdin
    fin.close()
    out = fout.read()
    err = ferr.read()
    return out,err

class mydict:
    def __init__(self,dict):
        self.value = dict
    def toplst(self,n,func=None):
        if not func:
            func = lambda x:x
        ba = [(func(b),a) for a,b in self.value.items()]
        ba.sort()
        ba.reverse()
        return [(a,self.value[a]) for b,a in ba[:n]]
    def top(self,n,func=None):
        return dict(self.toplst(n,func))

def toint(idstr, default = -1):
    try:
        return int(idstr)
    except:
        return default

def ipstr2int(ip):
    """
    >>> ipstr2int("218.247.22.34")
    3673626146
    """
    try:
        return struct.unpack('>I', socket.inet_aton(ip))[0]
    except:
        return 0

def round_data(data):
    """
    >>> round_data({'a':1./7, 0.9299999:12, 'es':[1, 0.2399, {1.21111:[1, 0.92323]}]})
    {'a': 0.14, 0.93: 12, 'es': [1, 0.24, {1.21: [1, 0.92]}]}
    """
    if type(data) == dict:
        result = {}
        for k, v in data.items():
            result[round_data(k)] = round_data(v)
        return result
    elif type(data) == tuple:
        result = list()
        for i in data:
            result.append(round_data(i))
        return tuple(result)
    elif type(data) == list:
        result = list()
        for i in data:
            result.append(round_data(i))
        return result
    elif type(data) == float:
        return round(data, 2)
    else:
        return data

def convert_n_bytes(n, b):
    bits = b*8
    return (n + 2**(bits-1)) % 2**bits - 2**(bits-1)

def convert_4_bytes(n):
    return convert_n_bytes(n, 4)

def java_string_hashcode(s):
    h = 0
    n = len(s)
    for i, c in enumerate(s):
        h = h + ord(c)*31**(n-1-i)
    return convert_4_bytes(h)

def make_dirs_for_file(filename):
    filepath = "/".join(filename.split("/")[:-1])
    if not os.path.exists(filepath):
        try:
            #print "try make", filepath
            os.makedirs(filepath)
        except:
            #print traceback.format_exc()
            pass
    return filepath
