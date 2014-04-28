#!/usr/bin/env python

import glob
from distutils.core import setup
from pygaga import __version__ as version
from setuptools import find_packages

try:
    long_description = open("README").read()
except IOError:
    long_description = ""

#PRE REQUIRED
# sudo apt-get install -y --force-yes libxml2-dev libxslt1-dev libjpeg-dev libpng-dev python-mysqldb
# sudo easy_install dateutils requests urllib3

setup(
    name = 'pygaga',
    version = version,
    description = 'adgaga common python libs',
    long_description = long_description,
    author = 'Chris Song',
    author_email = 'chuansheng.song@langtaojin.com',
    url = 'ssh://chuansheng.song@review.jcndev.com:29418/pygaga',
    packages = find_packages(exclude=[]),
    exclude_package_data={'': []},
    data_files=[('pygaga/corpus', glob.glob('pygaga/corpus/*')),
                ('pygaga/model/r', glob.glob("pygaga/model/r/*.r")),
               ],
    scripts = ['py_baby_sitter',
               'bin/pname_coef.sh',
               'bin/tailc',
               'bin/echosleep',
               'bin/sshforward',
               'bin/show_coef.sh',
               'bin/plot_validation.sh',
               'bin/r2liblinear.rb',
               'pygaga/model/plotroc.py',
               'pygaga/helpers/ip2.py',
               'pygaga/helpers/graphite_alert.py',
               'pygaga/helpers/scribe_log.py',
               ],
    license = "langtaojin.com",
    dependency_links = ['http://github.com/fakechris/squawk/tarball/master#egg=squawk-0.3',
                        "http://www.jcndev.com/hadoop/protobuf-2.3.0-py2.5.egg#egg=protobuf-2.3.0"],
    install_requires = ["sqlalchemy",
                        "redis",
                        "daemon",
                        "python-gflags",
                        "simplejson",
                        "jinja2",
                        "protobuf",
                        "squawk",
                        "pymongo",
                        "zc-zookeeper-static",
                        "pykeeper",
                        "PIL",
                        "lxml",
                        "poster",
                        "ssh",
                        #"thrift",
                        #"paramiko",
                        #"python-daemon",
                        "BeautifulSoup"],
    classifiers = [
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: langtaojin.com',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
