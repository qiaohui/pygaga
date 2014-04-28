#!/usr/bin/env python
#coding : utf8

import os
import sys

import gflags
import logging
import simplejson

from pygaga.helpers.logger import log_init
from pygaga.helpers.urlutils import download
from pygaga.helpers.utils import all_matched, takelastn

logger = logging.getLogger('AlertLogger')

FLAGS = gflags.FLAGS

gflags.DEFINE_string('server', "graphite.jcndev.com", "Server name")
gflags.DEFINE_string('target', "", "Which graphite target to alert?")
gflags.DEFINE_integer('lastn', 3, "Alert if all of last n datapoint match")
gflags.DEFINE_boolean('gt', True, "Alert if lager than/smaller than")
gflags.DEFINE_float('warnv', 0.0, "Warning thredshold")
gflags.DEFINE_float('errorv', 0.0, "Error thredshold")
gflags.DEFINE_string('since', "-1days", "From time")
gflags.DEFINE_string('until', "-", "Until time")

def check_graphite(server, target, n, warnv=0.0, errorv=0.0, gt=True, since="-1days", until="-"):
    url = "http://%s/render?format=json&from=%s&until=%s&target=%s" % (server, since, until, target)
    logger.debug("Fetching %s", url)
    data = download(url)
    json_data = simplejson.loads(data)
    data_points = json_data[0]['datapoints']
    lastn_datapoints = list(takelastn(data_points, FLAGS.lastn, lambda x:not x[0]))
    logger.debug("Last n data point %s", lastn_datapoints)
    is_warn = all_matched(lambda x:not ((x[0]>warnv) ^ gt), lastn_datapoints)
    is_error = all_matched(lambda x:not ((x[0]>errorv) ^ gt), lastn_datapoints)
    return is_warn, is_error, lastn_datapoints

def alert_main():
    is_warn, is_error, lastn_datapoints = check_graphite(FLAGS.server, FLAGS.target, FLAGS.lastn, FLAGS.warnv, FLAGS.errorv, FLAGS.gt, FLAGS.since, FLAGS.until)
    if is_error:
        logger.error("Alert %s is_gt %s:%s error %s!", FLAGS.target, FLAGS.gt, FLAGS.errorv, lastn_datapoints)
    elif is_warn:
        logger.warn("Alert %s is_gt %s:%s warning %s!", FLAGS.target, FLAGS.gt, FLAGS.warnv, lastn_datapoints)

if __name__ == "__main__":
    # usage: graphite_alert.py --pbverbose warn --use_paperboy --target xxx.xxx --warnv w --errorv e --since -1hours:%s
    log_init('AlertLogger', "sqlalchemy.*")
    alert_main()

