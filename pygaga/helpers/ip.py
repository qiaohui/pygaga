# coding: utf-8
import socket
import string
import sys
from struct import unpack
from pygaga.corpus import *

def ipstr2int(ip):
    try:
        return unpack('>I', socket.inet_aton(ip))[0]
    except:
        return -1

class Area:
    def __init__(self, code_name_path = area_path):
        self.load_area_name(code_name_path)

    def load_area_name(self, path):
        self.name = {}
        for line in open(path, "r"):
            row = line[:-1].split('\t')
            self.name[row[0]] = row[1]

    def code2area(self, code):
        if (code == None) or (code not in self.name):
            return
        return self.name[code]

    def code2province(self, code):
        new_code = int(code) / 100 * 100
        return self.code2area("%06d" % new_code)

class Income:
    def __init__(self, data_path = income_data_path):
        self.load_income_data(income_data_path)

    def load_income_data(self, path):
        self.income = {}
        for line in open(path, "r"):
            row = line[:-1].split("\t")
            if row[0] == "HEADER": continue
            code = row[1]
            val = float(row[-2])
            self.income[code] = val

    def code2income(self, code):
        if code in self.income:
            return self.income[code]
        else:
            prov = code[:-2] + "00"
            if prov in self.income:
                return self.income[prov]
        return 0.0

    def test(self):
        for line in open(area_path, "r"):
            row = line[:-1].decode('utf-8').split('\t')
            code = row[0]
            name = row[1]
            inc =   self.code2income(code)
            print code, name, inc

# 新疆 西藏
TZ_WEST = ["016500", "015400"]
# 广东 广西 海南 江西 河南 湖北 湖南 上海 江苏 浙江 安徽 福建 山东 辽宁 吉林 黑龙江 北京 天津 河北 山西
TZ_EAST = ["014400", "014500", "014600", "013600", "014100", "014200", "014300", "013100", "013200", "013300", "013400", "013500", "013700", "012100", "012200", "012300", "011100", "011200", "011300", "011400"]
# 陕西 甘肃 青海 宁夏 内蒙古 重庆 四川 贵州 云南
TZ_MIDDLE = ["016100", "016200", "016300", "016400", "011500", "015000", "015100", "015200", "015300"]

# 陕西 甘肃 青海 宁夏 新疆
NORTH_WEST = ["016100", "016200", "016300", "016400", "016500"]
# 重庆 四川 贵州 云南 西藏
SOUTH_WEST = ["015000", "015100", "015200", "015300", "015400"]
# 广东 广西 海南
SOUTH_EAST = ["014400", "014500", "014600"]
# 江西 河南 湖北 湖南
MIDDLE = ["013600", "014100", "014200", "014300"]
# 上海 江苏 浙江 安徽 福建 山东
MIDDLE_EAST = ["013100", "013200", "013300", "013400", "013500", "013700"]
# 辽宁 吉林 黑龙江
NORTH_EAST = ["012100", "012200", "012300"]
# 北京 天津 河北 山西 内蒙古
NORTH = ["011100", "011200", "011300", "011400", "011500"]

class IP2Area:
    def __init__(self, ipmap_path = ipblk_rgn_code_foreign2china_path, \
            code_name_path = area_path):
        self.load_ip_list(ipmap_path)
        self.area = Area(code_name_path)
        self.load_big_area()
        self.load_tz_area()

    def load_ip_list(self, path):
        self.ips = []
        for line in open(path, "r"):
            row   = line[:-1].split('\t')
            start = int(row[0])
            end   = int(row[1])
            code  = row[2]
            self.ips.append((start, end, code))

    def load_tz_area(self):
        self.tz_area = {}
        for code in TZ_WEST: self.tz_area[code] = 'W'
        for code in TZ_EAST: self.tz_area[code] = 'E'
        for code in TZ_MIDDLE: self.tz_area[code] = 'M'

    def load_big_area(self):
        self.big_area = {}
        for code in NORTH_WEST: self.big_area[code] = 'NW'
        for code in SOUTH_WEST: self.big_area[code] = 'SW'
        for code in SOUTH_EAST: self.big_area[code] = 'SE'
        for code in MIDDLE:     self.big_area[code] = 'M'
        for code in MIDDLE_EAST:self.big_area[code] = 'ME'
        for code in NORTH_EAST: self.big_area[code] = 'NE'
        for code in NORTH:      self.big_area[code] = 'N'

    def code2tz_area(self, code):
        #change to prov code first.
        code = code[:-2] + "00"
        #return big area of the province.
        return (self.tz_area[code] if (code in self.tz_area) else 'N/A')

    def code2big_area(self, code):
        #change to prov code first.
        code = code[:-2] + "00"
        #return big area of the province.
        return (self.big_area[code] if (code in self.big_area) else 'N/A')

    def ipint2big_area(self, ip):
        '''
        >>> i2a = IP2Area()
        >>> i2a.ipint2big_area("218.247.22.34")
        'N'
        >>> i2a.ipint2big_area("219.223.194.194")
        'SE'
        '''
        code = self.ipint2code(ip)
        return self.code2big_area(code)

    def ipint2code(self, ip):
        """
        >>> i2a = IP2Area()
        >>> i2a.ipint2code("211.100.28.227")
        '011100'
        """
        if len(self.ips) == 0:
            return 0
        if type(ip) == str or type(ip) == unicode:
            ip = ipstr2int(ip)
        if ip < self.ips[0][0] or ip > self.ips[-1][1]:
            return 0

        front = 0
        end   = len(self.ips)

        while front + 1 < end :
            mid = (front + end) / 2
            if ip >= self.ips[mid][0]:
                front = mid
            else:
                end = mid

        return self.ips[front][2]

    def ipint2area(self, ip, provice_level=False):
        code = self.ipint2code(ip)
        if provice_level:
            return self.area.code2area(code), self.area.code2province(code), code
        else:
            return self.area.code2area(code)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
