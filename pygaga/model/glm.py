#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import os
import math
import logging
from pygaga.helpers.utils import readcmd

logger = logging.getLogger('PygagaModel')

def get_tmpfile(prefix="file"):
    return os.tempnam("tmp", prefix)

def dump_signallst(signallst, pname_filename, data_filename):
    for signal in signallst:
        assert('result' in signal)

    allcols = list(set(itertools.chain(*[signal.keys() for signal in signallst])))
    allcols.remove('result')
    allcols.append('result')

    p2r,r2p = {},{}
    pfp = open(pname_filename,'w')
    for i,col in enumerate(allcols):
        p2r[col] = 'input_%s'%i
        r2p['input_%s'%i] = col
        if col != 'result':
            print >> pfp, i+1,col
    p2r['result'] = 'result'
    r2p['result'] = 'result'
    logger.debug('signal number %s' % len(allcols))
    if len(allcols) < 2:
        return p2r, r2p, {}

    datafp = open(data_filename,'w')
    #dongfp = open('%sdong.txt' % prefix,'w')
    #csvfp = open('%sdata.csv' % prefix,'w')
    print >> datafp, ' '.join([p2r[col] for col in allcols])
    #print >> csvfp, ','.join(allcols)
    for signal in signallst:
        print >> datafp, ' '.join(['"%s"'%signal.get(col,0) for col in allcols])
        #print >> dongfp,signal['result'],' '.join(['%s:%s'%(int(p2r[col].split('_')[-1])+1,signal.get(col,0)) for col in allcols if signal.get(col,0)!=0 and col!='result'])
        #print >> csvfp, ','.join(['"%s"'%signal.get(col,0) for col in allcols])
    datafp.close()
    #dongfp.close()
    #csvfp.close()
    return p2r, r2p, allcols

def glm_train(signallst, pname_filename, data_filename, model_filename, summary_filename, print_r_output = False):
    if not os.path.exists('r'):
        os.mkdir('r')

    p2r, r2p, allcols = dump_signallst(signallst, pname_filename, data_filename)

    if os.path.exists(model_filename):
        os.system('rm %s' % model_filename)
    logger.debug('starting r')

    rscript = '''
    turnout <- read.csv(file="%s",head=TRUE,sep=" ")
    x=glm(result ~ %s, data=turnout)
    write.table(coef(x),file="%s")
    sink("%s")
    print(summary(x))
    sink()
    '''%(data_filename,
         ' + '.join([p2r[col] for col in allcols if col != 'result']),
         model_filename,
         summary_filename)

    fname = "%s.r" % get_tmpfile("runr0_")
    print >> open(fname, 'w'), rscript
    out,err = readcmd('R --slave --quiet --no-save',rscript)
    if err:
        file("%s.err" % fname,"w").write(err)
    for line in err.splitlines():
        logger.error('R Error: %s' % line)
    if print_r_output:
        for line in out.splitlines():
            logger.info('OUT %s' % line)
    logger.debug('end r')

    coef = {}
    for line in list(open(model_filename))[1:]:
        d = line.split()
        var = d[0][1:-1]
        coef[r2p.get(var,var)] = d[1]
    return coef

def _glm_calc(signal,coef):
    detail = []
    exp = float(coef['(Intercept)'])
    for var,val in coef.items():
        try: val = float(val)
        except: continue
        if var in signal:
            exp += val*signal[var]
            detail.append('%s=(%s*%s)'%(var,signal[var],val))
        else:
            vars = var.split('&')
            match = [v for v in vars if signal.get(v,None)==1]
            if len(match) == len(vars):
                exp += val
                detail.append('%s=(1*%s)'%(var,val))
    return exp,detail

def _logit_calc(signal,coef):
    exp,detail = _glm_calc(signal,coef)
    detail.append("logit_exp=(%s)" % exp)
    if -exp > 100:
        result = 0
    else:
        result = 1/(1+math.exp(-exp))
    return result,detail

def _poisson_calc(signal,coef):
    exp,detail = _glm_calc(signal,coef)
    detail.append("logit_exp=(%s)" % exp)
    result = math.exp(exp)
    return result,detail

def _log_calc(signal, coef):
    exp, detail = _glm_calc(signal, coef)
    detail.append("log_exp=(%s)" % exp)
    if exp < -100:
        result = 0
    else:
        result = math.exp(exp)
    return result, detail

if __name__ == "__main__":
    import doctest
    doctest.testmod()
