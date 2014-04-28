import usertrac_pb2
import time
import urllib
import base64
from pygaga.helpers import urlutils, utils
import sys

def parse_request(req):
    idx = req.find('?')
    if (-1 == idx):
        return
    req = req[idx+1:]
    args = req.split('&')
    uv, ur, ucs, usr, uco, ula, uj, uf, ut, ure, uh, up = ("",) *12
    for arg in args:
        if arg.startswith("uv="):
            uv = arg[3:]
        elif arg.startswith("ur="):
            ur = arg[3:]
        elif arg.startswith("ucs="):
            ucs = arg[4:]
        elif arg.startswith("usr="):
            usr = arg[4:]
        elif arg.startswith("uco="):
            uco = arg[4:]
        elif arg.startswith("ula="):
            ula = arg[4:]
        elif arg.startswith("uj="):
            uj = arg[3:]
        elif arg.startswith("uf="):
            uf = arg[3:]
        elif arg.startswith("ut="):
            ut = arg[3:]
        elif arg.startswith("ure="):
            ure = arg[4:]
        elif arg.startswith("uh="):
            uh = arg[3:]
        elif arg.startswith("up="):
            up = arg[3:]

    up = urllib.unquote(up).decode("utf8")
    #up = urllib.unquote(up)
    return (uv, ur, ucs, usr, uco, ula, uj, uf, ut, ure, uh, up)

def get_click_hash(upqs):
    return urlutils.safe_get(upqs, "uctrac_clk")

def get_utrac_id(upqs):
    utrac_id    = urlutils.safe_get(upqs, "uctrac_eid_1")
    is_landing  = False
    if "" == utrac_id:
        utrac_id = urlutils.safe_get(upqs, "uctrac_eid")
        is_landing = True if utrac_id != "" else False

    return utils.toint(utrac_id), is_landing

def parse_apache_log(line):
    usertrac = usertrac_pb2.UserTrac()

    parts = line[:-1].split('"')
    
    if len(parts) < 10:
        print >>sys.stderr, line, "tc apache log less than 10 fields"
        return

    row     = parts[0].split(' ')
    ipstr   = row[0]

    ts = int(time.mktime(time.strptime(row[3][1:], "%d/%b/%Y:%H:%M:%S")))

    row         = parts[1].split(' ')
    request     = row[1]

    refer       = parts[3]
    user_agent  = parts[5]
    cookies     = parts[9]

    request_args = parse_request(request)

    if request_args == None:
        return

    uv, ur, ucs, usr, uco, ula, uj, uf, \
        ut, ure, uh, up = request_args

    muid, xxid = "", ""
    for cookie in cookies.split("; "):
        if cookie.startswith("MUID="):
            muid = cookie[5:-2]
        elif cookie.startswith("YYID="):
            xxid = cookie[5:]

    #usertrac.click_id      = ""
    usertrac.muid           = muid    
    usertrac.xxid           = xxid
    #usertrac.utrac_eid     = 
    #usertrac.is_landing    = 
    #usertrac.is_from_ad    = 
    #print ipstr
    usertrac.ip             = utils.ipstr2int(ipstr)
    usertrac.time           = ts
    usertrac.char_code      = ucs
    usertrac.resolution     = usr
    usertrac.color_depth    = uco
    usertrac.page_title     = ut
    usertrac.page_url       = ure
    usertrac.page_host      = uh
    usertrac.page_path      = up

    upqs = urlutils.get_qs(up)
    usertrac.utrac_eid, usertrac.is_landing = get_utrac_id(upqs)
    usertrac.click_hash     = get_click_hash(upqs)

    return usertrac


def to_base64(usertrac):
    return base64.b64encode(usertrac.SerializeToString())

def from_base64(line):
    usertrac = usertrac_pb2.UserTrac()
    usertrac.ParseFromString(base64.b64decode(line))
    return usertrac

def test():
    for line in open(sys.argv[1], "r"):
        usertrac = parse_apache_log(line)
        print line
        print usertrac.muid,usertrac.xxid,usertrac.ip,usertrac.time,usertrac.resolution,usertrac.page_path,usertrac.utrac_eid,usertrac.is_landing

if __name__ == "__main__":
    test()



