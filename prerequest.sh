#!/bin/sh

apt-get install -y --force-yes libxml2-dev libxslt1-dev libjpeg-dev libpng-dev python-mysqldb
easy_install pip
pip install dateutils requests urllib3 pycrypto
#easy_install pytst

