#!/usr/bin/env python
# coding: utf-8

import os
import sys

import web
import daemon
import gflags
import logging

from pygaga.helpers.logger import log_init
from pygaga.helpers.webutils import file_env, render_to_string, render_html

logger = logging.getLogger('WebLogger')

FLAGS = gflags.FLAGS

file_path = os.path.split(os.path.abspath(__file__))[0]

ENV = file_env(file_path)

urls = (
    '/', 'home',
)
def my_filter(input):
    return input

ENV.filters['my_filter'] = my_filter

class home:
    def GET(self):
        return 'test'

if __name__ == "__main__":
    # usage: ${prog} ip:port --daemon --stderr ...
    gflags.DEFINE_boolean('daemon', False, "is start in daemon mode?")
    gflags.DEFINE_boolean('webdebug', False, "is web.py debug")
    gflags.DEFINE_boolean('reload', False, "is web.py reload app")
    backup_args = []
    backup_args.extend(sys.argv)
    sys.argv = [sys.argv[0],] + sys.argv[2:]
    log_init('WebLogger', "sqlalchemy.*")
    sys.argv = backup_args[:2]
    web.config.debug = FLAGS.webdebug
    if len(sys.argv) == 1:
        web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    if FLAGS.daemon:
        daemon.daemonize(os.path.join(file_path, 'web.pid'))
    #render = web.template.render('templates/', base='layout')
    app = web.application(urls, globals(), autoreload=FLAGS.reload)
    app.run()

