#!/usr/bin/env python

import logging
import socket
import time
import traceback
import xmlrpclib
from logging import DEBUG, INFO, WARN, WARNING, ERROR, FATAL, CRITICAL

class Logger(object):
    def __init__(self, server='localhost', port=1415, category='NONE', local_logger=None):
        url = 'http://%s:%d' % (server, port)
        self.proxy = xmlrpclib.ServerProxy(url)
        self.category = category
        self.hostname = socket.gethostname()
        self.local_logger = local_logger

    def log(self, level, msg, tags=[], title=''):
        try:
            entry = {
                    'ver': '0.3',
                    't':time.time(),
                    'c':self.category,
                    'l':level,
                    'm':msg,
                    'a':tags,
                    'host': self.hostname,
                }
            if title:
                entry['title'] = title

            self.proxy.log(entry)
            if self.local_logger:
                self.local_logger.log(level, msg)
        except Exception, e:
            traceback.print_exc()

    def debug(self, msg, tags=[], title=''):
        self.log(DEBUG, msg, tags, title)

    def info(self, msg, tags=[], title=''):
        self.log(INFO, msg, tags, title)

    def warn(self, msg, tags=[], title=''):
        self.log(WARN, msg, tags, title)

    def warning(self, msg, tags=[], title=''):
        self.log(WARNING, msg, tags, title)

    def error(self, msg, tags=[], title=''):
        self.log(ERROR, msg, tags, title)

    def fatal(self, msg, tags=[], title=''):
        self.log(FATAL, msg, tags, title)

    def critical(self, msg, tags=[], title=''):
        self.log(CRITICAL, msg, tags, title)

class PaperboyHandler(logging.Handler):
    def __init__(self, server='localhost', port=1415, category='NONE'):
        self.lock = None
        self.err_count = 0
        self.paperboy = Logger(server, port, category)
        self.setLevel(WARN)

    def filter(self, record):
        return record.levelno >= self.level

    def emit(self, record):
        try:
            has_tags = hasattr(record, 'tags')
            tags = record.tags if has_tags else []
            lv = record.levelno
            formatted_msg = "[%s] (%s:%s) %s %s" % (record.threadName, record.filename, record.lineno, record.funcName, record.message)
            self.paperboy.log(lv, formatted_msg, tags)
        except Exception:
            if self.err_count % 100 == 0:
                traceback.print_exc()
            self.err_count += 1

def test():
    logger = Logger(category='test')
    logger.debug('this is a debug message', ['dddebug'])
    logger.info('this is a info message', ['testtag'])
    logger.warn('this is a warning message', ['hadouken'])
    logger.error('this is a error message', ['shouryuuken', 'paah'])
    logger.critical('something bad happened!', ['ddd'])

if __name__ == '__main__':
    test()

