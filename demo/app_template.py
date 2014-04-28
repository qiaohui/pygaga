#!/usr/bin/env python
# coding: utf-8

import os
import sys

import daemon
import gflags
import logging

from pygaga.helpers.logger import log_init
from pygaga.helpers.dbutils import get_db_engine

logger = logging.getLogger('AppLogger')

FLAGS = gflags.FLAGS

def main():
    pass

if __name__ == "__main__":
    # usage: ${prog} ip:port --daemon --stderr ...
    gflags.DEFINE_boolean('daemon', False, "is start in daemon mode?")
    log_init('AppLogger', "sqlalchemy.*")
    #if FLAGS.daemon:
    #    file_path = os.path.split(os.path.abspath(__file__))[0]
    #    daemon.daemonize(os.path.join(file_path, 'app.pid'))
    main()

