#coding : gbk
import mmap
import socket
import string
import sys
import tst
from struct import unpack
from pygaga.corpus import *
from pygaga.helpers.cache import lru_cache

def first(arr):
    for x in arr:
        if x:
            return x
    return None

class IpLocater(object):
    def __init__(self, ipdb_file):
        f = open(ipdb_file, 'rb')
        self.ipdb = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        # get index address
        header = self.ipdb.read(8)
        (self.first_index, self.last_index) = unpack('II', header)
        self.index_count = (self.last_index - self.first_index) / 7 + 1

    def getString(self, offset = 0):
        if offset :
            self.ipdb.seek(offset)
        mystr = ''
        if self.ipdb.tell() == 0:
           return ''
        ch = self.ipdb.read(1)
        (byte,) = unpack('B', ch)
        while byte != 0:
            mystr = mystr + ch
            ch = self.ipdb.read(1)
            (byte,) = unpack('B',ch)
        return mystr

    def getLong3(self, offset = 0):
        if offset :
            self.ipdb.seek(offset)
        mystr = self.ipdb.read(3)
        (a,b) = unpack('HB', mystr)
        return (b << 16) + a

    def getAreaAddr(self, offset=0):
        if offset :
            self.ipdb.seek(offset)
        mystr = self.ipdb.read(1)
        (byte,) = unpack('B', mystr)
        if byte == 0x01 or byte == 0x02:
            p = self.getLong3()
            if p:
                return self.getString(p)
            else:
                return ''
        else:
            self.ipdb.seek(self.ipdb.tell() - 1)
            return self.getString()

    def getAddr(self, offset, ip = 0):
        self.ipdb.seek(offset + 4)
        countryAddr = ''
        areaAddr = ''
        mystr = self.ipdb.read(1)
        (byte,) = unpack('B', mystr)
        if byte == 0x01:
            countryOffset = self.getLong3()
            self.ipdb.seek(countryOffset)
            mystr = self.ipdb.read(1)
            (b,) = unpack('B', mystr)
            if b == 0x02:
                countryAddr = self.getString(self.getLong3())
                self.ipdb.seek( countryOffset + 4 )
            else:
                countryAddr = self.getString(countryOffset)
            areaAddr = self.getAreaAddr()
        elif byte == 0x02:
            countryAddr = self.getString(self.getLong3())
            areaAddr = self.getAreaAddr(offset + 8)
        else:
            countryAddr = self.getString(offset + 4)
            areaAddr = self.getAreaAddr()
        return countryAddr + '/' + areaAddr

    def output(self, first, last):
        if last > self.index_count :
            last = self.index_count
        for index in range(first, last):
            offset = self.first_index + index * 7
            self.ipdb.seek(offset)
            buf = self.ipdb.read(7)
            (ip,of1,of2) = unpack('IHB', buf)
            print '%s - %s' % (ip, self.getAddr( of1 + (of2 <<16)))

    def find(self, ip, left, right):
        if right-left == 1:
            return left
        else:
            middle = (left + right) / 2
            offset = self.first_index + middle * 7
            self.ipdb.seek(offset)
            buf = self.ipdb.read(4)
            (new_ip,) = unpack('I', buf)
            if ip <= new_ip :
                return self.find(ip, left, middle)
            else:
                return self.find(ip, middle, right)

    def getIpAddr(self, ip):
        index = self.find(ip, 0, self.index_count - 1)
        ioffset = self.first_index + index * 7
        aoffset = self.getLong3(ioffset + 4)
        address = self.getAddr(aoffset)
        return address

class CityIndex(object):
    def __init__(self):
        self.c_tst = tst.TST()
        c_data = open(college_path)
        c_map_data = dict([x.strip().split(" ") for x in c_data])
        c_data.close()
        for k, v in c_map_data.items():
            self.c_tst.put(k, v)

        self.city_tst = tst.TST()
        self.province_tst = tst.TST()
        city_data = open(city_path)
        city_data2 = [x.strip().split(" ") for x in city_data]
        city_data.close()
        provinces = set([x[0] for x in city_data2])
        province_data = set([l.strip() for l in open(province_path).readlines()])
        provinces = provinces.union(province_data)
        for x in provinces:
            self.province_tst.put(x, x)
        for v in city_data2:
            self.city_tst.put(v[1], v)

        self.country_tst = tst.TST()
        country_data = open(country_path)
        countries = set([l.strip().split(" ")[0] for l in country_data.readlines()])
        country_data.close()
        for c in countries:
            self.country_tst.put(c, c)

    def match(self, addr):
        # process college
        c_results = self.c_tst.scan(addr, tst.ListAction())
        if any(c_results):
            addr = first(c_results)

        # find province
        country_results = self.country_tst.scan(addr, tst.ListAction())
        province_results = self.province_tst.scan(addr, tst.ListAction())
        city_results = self.city_tst.scan(addr, tst.ListAction())
        r_country = first(country_results)
        r_province = first(province_results)
        r_city = first(city_results)

        if not r_province and not r_city:
            return r_country, None, None
        if r_province and not r_city:
            return 'China', r_province, None
        return 'China', r_city[0], r_city[1]


g_ip_locater = IpLocater(qqwry_path)
g_ip_city = CityIndex()

@lru_cache(maxsize=50)
def ip2address(ip):
    """
    >>> ip2address("211.100.48.102")
    """
    return g_ip_locater.getIpAddr(unpack('>I', socket.inet_aton(ip))[0])

def address2city(addr):
    """
    >>> repr(address2city(ip2address("211.100.48.103")))
    "('China', '\\\\xb1\\\\xb1\\\\xbe\\\\xa9', None)"
    """
    return g_ip_city.match(addr)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        input = sys.stdin.readlines()
    else:
        input = sys.argv[1].split("\n")
    for i in input:
        try:
            addr = ip2address(i.strip())
            country, pro, city = address2city(addr)
            print addr, pro, city
        except:
            pass
