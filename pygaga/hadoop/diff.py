#!/usr/bin/env python
# coding=utf8

import os
import gflags
import sys

FLAGS = gflags.FLAGS

gflags.DEFINE_string('srcpath', "", "Source path", short_name = 's')
gflags.DEFINE_string('dstpath', "", "Destination path", short_name = 'd')
gflags.DEFINE_string('srcpre', "hftp://job4:50070", "Source path", short_name = 'p')
gflags.DEFINE_string('dstpre', "hdfs://sdl-job1", "Destination path", short_name = 'q')

class PathItem:
    is_file = False
    length = 0
    ts = 0
    path = ""

    def __init__(self):
        self.subdir = []

def parse_ls_item(item):
    p = PathItem()
    try:
        result = [i for i in item.split(" ") if i]
        p.is_file = result[1].isdigit()
        p.length = int(result[4])
        p.path = result[-1]
        p.ts = int(time.mktime(time.strptime(result[5] + result[6], "%Y-%m-%d%H:%M")))
    except:
        pass
    return p

def parse_ls_result(result):
    results = result.split("\n")
    head = results[0]
    return [parse_ls_item(r) for r in results[1:] if r]

def ls_hdfs(pre, p, pathitem):
    result = os.popen("hadoop fs -ls %s%s" % (pre, p)).read()
    pathitem.subdir = parse_ls_result(result)
    for item in pathitem.subdir:
        if not item.is_file:
            ls_hdfs(pre, item.path, item)

def diff_path(src, dst):
    pos = 0
    for item in src.subdir:
        if len(dst.subdir) <= pos:
            print "only in src", item.path
            continue
        while len(dst.subdir) >= pos:
            if item.path == dst.subdir[pos].path:
                if item.is_file and dst.subdir[pos].is_file:
                    if item.length == dst.subdir[pos].length:
                        print "file match", item.path, item.length
                    else:
                        print "file size not match", item.path, item.length, dst.subdir[pos].length
                else:
                    diff_path(item, dst.subdir[pos])
                pos += 1
                break # matched
            elif item.path < dst.subdir[pos].path:
                print "only in src", item.path, item.length
                break
            else:
                print "only in dst", dst.subdir[pos].path, dst.subdir[pos].length
                pos += 1
    while len(dst.subdir) > pos:
        print "only in dst", dst.subdir[pos].path, dst.subdir[pos].length
        pos += 1

def diff_hdfs():
    src = PathItem()
    dst = PathItem()
    ls_hdfs(FLAGS.srcpre, FLAGS.srcpath, src)
    ls_hdfs(FLAGS.dstpre, FLAGS.dstpath, dst)
    diff_path(src, dst)

if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)  # parse flags
    except gflags.FlagsError, e:
        print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
        sys.exit(1)
    diff_hdfs()

