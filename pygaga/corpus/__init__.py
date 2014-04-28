import cPickle, os

# load ch2pop.pickle from current module's path
_mod_path = os.path.split(__file__)[0]
ch2pop = cPickle.load(open(os.path.join(_mod_path, 'ch2pop.pickle')))
ipblk_rgn_code_foreign2china_path = os.path.join(_mod_path, 'ipblk_rgn_code_foreign2china.txt')
income_data_path = os.path.join(_mod_path, 'income2009.txt')
area_path = os.path.join(_mod_path, 'area.dat')
sogou_dict_path = os.path.join(_mod_path, 'SogouLabDic.dic')
country_path = os.path.join(_mod_path, 'country.txt')
province_path = os.path.join(_mod_path, 'province.txt')
city_path = os.path.join(_mod_path, 'city.txt')
college_path = os.path.join(_mod_path, 'college.txt')
qqwry_path = os.path.join(_mod_path, 'qqwry.dat')
