#!/usr/bin/env python
#This tool allow users to plot ROC curve from data
import gflags
import os
import sys
import math
from sys import argv, platform
from os import path, popen
from random import randrange , seed
from operator import itemgetter
from time import sleep

FLAGS = gflags.FLAGS
gflags.DEFINE_string('inputfile', '', 'convert data file')
gflags.DEFINE_string('outputfile', '', 'roc curve image')
gflags.DEFINE_string('type', 'roc', 'roc curve image')
gflags.DEFINE_string('gnuplot_path', '/usr/bin/gnuplot', 'gnuplot path')

#a simple gnuplot object
class gnuplot:
    def __init__(self, term='ps', cmdline=FLAGS.gnuplot_path):
        # -persists leave plot window on screen after gnuplot terminates
        if platform == 'win32':
            self.__dict__['screen_term'] = 'windows'
        else:
            self.__dict__['screen_term'] = 'x11'
        self.__dict__['iface'] = popen(cmdline,'w')
        self.set_term(term)

    def set_term(self, term):
        if term=='onscreen':
            self.writeln("set term %s" % self.screen_term)
        else:
            #term must be either x.ps or x.png
            self.writeln('set term postscript eps color 22')
        self.output = term

    def writeln(self,cmdline):
        self.iface.write(cmdline + '\n')

    def __setattr__(self, attr, val):
        if type(val) == str:
            self.writeln('set %s \"%s\"' % (attr, val))
        else:
            print("Unsupport format:", attr, val)
            raise SystemExit

    #terminate gnuplot
    def __del__(self):
        self.writeln("quit")
        self.iface.flush()
        self.iface.close()

    def __repr__(self):
        return "<gnuplot instance: output=%s>" % term

    #data is a list of [x,y]
    def plotline(self, data):
        self.writeln(" set size 2, 2")
        self.writeln(" set grid")
        cmd = " plot "
        for i in range(0,len(data)):
            if i == len(data) -1:
                cmd += "\"-\" title \"%s\" w l  lw 5"% (i)
            else:
                cmd += "\"-\" title \"%s\" w l  lw 5 ,"% (i)

        self.writeln(cmd)
        for i in range(0, len(data)):
            for j in range(0, len(data[i]['xy_arr'])):
                self.writeln("%f %f" % (data[i]['xy_arr'][j][0], data[i]['xy_arr'][j][1]))
            self.writeln("e")
            sleep(0) #delay

        if platform=='win32':
            sleep(3)

def plot_roc(inputfile, output, title):
    data_set = {}
    inputfile = inputfile.split(',')
    col_num = len(inputfile)

    i = 0
    for f in inputfile:
        try:
            fin = open(f, 'r')
        except:
            print "%s is not exist!"% f
            continue

        for line in fin.readlines():
            cols = line.split("\t")

            if len(cols) < 2:
                continue

            item = data_set.setdefault(i, {})
            item.setdefault('pos', 0.0)
            item.setdefault('neg', 0.0)
            item.setdefault('data', [])
            item['pos'] += float(cols[1])
            if float(cols[1]) < 1:
                item['neg'] += 1 - float(cols[1])
            item['data'].append([cols[0], float(cols[1])])

        fin.close()
        i += 1

    #order by convert rate desc
    for i in range(0, col_num):
        data_set[i]['data'] = sorted(data_set[i]['data'], key=itemgetter(0), reverse=True)

        #calculate ROC
        tp, fp = 0., 0.
        xy_arr  = []
        for j in data_set[i]['data']:
            tp += j[1]
            if j[1] < 1:
                fp += 1 - j[1]
            if data_set[i]['neg']:
                x = fp/data_set[i]['neg']
            else:
                x = 0
            if data_set[i]['pos']:
                y = tp/data_set[i]['pos']
            else:
                y = 0
            xy_arr.append([x, y])
        data_set[i]['xy_arr'] = xy_arr

        #area under curve
        auc = 0.
        prev_x = 0
        prev_y = 0
        for x,y in data_set[i]['xy_arr']:
            if x != prev_x:
                auc += (x - prev_x) * (y + prev_y) / 2
                prev_x = x
                prev_y = y
        data_set[i]['auc'] = auc

    #begin gnuplot
    if title == None:
        title = output
    #plot roc and save to image file
    g = gnuplot(output)
    g.xlabel = "False Positive Rate"
    g.ylabel = "True Positive Rate"
    aoc = ",".join(['%.4f'%data_set[i]['auc'] for i in range(0, col_num)])
    g.title = "ROC curve of %s (AUC = %s)" % (title,aoc)
    g.plotline(data_set)

    return aoc

def plot_line(inputfile, output, title):
    data_set = {}
    inputfile = inputfile.split(',')
    col_num = len(inputfile)

    i = 0
    for f in inputfile:
        try:
            fin = open(f, 'r')
        except:
            print "%s is not exist!"% f
            continue

        data_set.setdefault(i, {})
        xy_arr  = []
        sum = 0.0
        for line in fin.readlines():
            cols = line.split("\t")

            if len(cols) < 2:
                continue

            xy_arr.append([float(cols[1]), float(cols[0])])
            sum += math.fabs(float(cols[0]) - float(cols[1]))
        data_set[i]['xy_arr'] = xy_arr
        data_set[i]['sub'] = sum
        fin.close()
        i += 1

    #order by convert rate desc
    for i in range(0, col_num):
        data_set[i]['xy_arr'] = sorted(data_set[i]['xy_arr'], key=itemgetter(0), reverse=False)

    #begin gnuplot
    if title == None:
        title = output
    #plot roc and save to image file
    g = gnuplot(output)
    g.xlabel = "Bayes"
    g.ylabel = "Predict"
    sub = ",".join(['%.4f'%data_set[i]['sub'] for i in range(0, col_num)])
    g.title = "Sub curve of %s (sub = %s)" % (title,sub)
    g.plotline(data_set)

    return sub

def main():
    try:
        argv = FLAGS(sys.argv)[1:]  # parse flags
    except gflags.FlagsError, e:
        sys.exit(1)

    if FLAGS.inputfile and FLAGS.outputfile and FLAGS.type == 'roc':
        auc = plot_roc(FLAGS.inputfile, FLAGS.outputfile, "PPC Model Train Roc Curve")
        cmd = 'convert %s %s.jpg;rm %s'% (FLAGS.outputfile, FLAGS.outputfile, FLAGS.outputfile)
        os.system(cmd)
        print >> open('%s' % FLAGS.outputfile + '.auc', 'w'), auc
    elif FLAGS.inputfile and FLAGS.outputfile and FLAGS.type == 'sub':
        var = plot_line(FLAGS.inputfile, FLAGS.outputfile, "PPC Model Train Sub Curve")
        print >> open('%s' % FLAGS.outputfile + '.var', 'w'), var
        #cmd = 'convert %s %s.jpg;rm %s'% (FLAGS.outputfile, FLAGS.outputfile, FLAGS.outputfile)
        #os.system(cmd)

if __name__ == '__main__':
    main()
