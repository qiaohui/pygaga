#!/usr/bin/env python
# coding=utf-8

import cPickle
import traceback
import gflags
import os
import math
import sys
import math
import logging
from operator import itemgetter
from pygaga.model.regression import regression
from pygaga.model.regression import svd_regression
from pygaga.model.regression import lg_regression
from pygaga.helpers.cache import lru_cache
from pygaga.helpers.utils import mydict
from pygaga.helpers.mmseg import lazy_dict
from pygaga.helpers.mmseg import mmseg2

from pygaga.model.glm import _glm_calc
from pygaga.model.glm import _log_calc
from pygaga.model.glm import _logit_calc
from pygaga.model.glm import _poisson_calc
from pygaga.model.glm import dump_signallst
from pygaga.model.glm import glm_train

logger = logging.getLogger("PygagaModel")

FLAGS = gflags.FLAGS
gflags.DEFINE_string('prefix', '', "model file prefix")
gflags.DEFINE_boolean('new_signal', True, "gen new singal for train")
gflags.DEFINE_enum('modelname', 'pca', ['pca', 'lg', 'svd', 'poisson', 'logit', 'old', 'const'], 'Model name')

def numberic2SignalFn(fn_trans, seps):
    """
    >>> fn1 = numberic2SignalFn(float, [50.0, 200.0])
    >>> fn1('61')
    1
    >>> fn1('0')
    0
    >>> fn1('22')
    0
    >>> fn1('201')
    2
    """
    fns = [(lambda x,y=n[1]:x<y, n[0]) for n in enumerate(seps)]
    fns.append((lambda x:x>=seps[-1], len(fns)))
    def _numberic2Signal(input):
        v = fn_trans(input)
        for fn in fns:
            if fn[0](v):
                return fn[1]
    return _numberic2Signal

class stats_model:
    '''
    >>> from pygaga.helpers.utils import round_data
    >>> s = stats_model()
    >>> s._feed([(1, {'a':2})]*10)
    >>> s._get_feature_count()
    0
    >>> s = stats_model()
    >>> s._feed([(1, {'a':2})]*101)
    >>> s._get_feature_count()
    1
    >>> s._feed([(1, {'a':2})]*2001)
    >>> s._get_feature_count()
    15
    >>> s._feed([(1, {'a':2})]*6001)
    >>> s._get_feature_count()
    35
    >>> s._feed([(1, {'a':2})]*60221)
    >>> s._get_feature_count()
    195
    >>> s._feed([(1, {'a':2})]*1000002)
    >>> s._get_feature_count()
    2545
    >>> s._feed([(0.3, {'a':2})]*22 + [(0.6, {'a':1, 'b':9})]*40 + [(0.9,{'c':1}),(0.4,{'b':3,'a':1})]*90)
    >>> round_data(s.stats)
    {'a': [66.6, 152], 'c': [81.0, 90], 'b': [60.0, 130]}
    >>> round_data(s._bayes_train_signals())
    {'a': 0.72, 'c': 1.48, 'b': 0.76}
    >>> len(s._bayes_select())
    242
    >>> s = stats_model()
    >>> s._feed([(0.1, {'a':1,'c':1})]*199 + [(0.5, {'a':1, 'b':1})]*220 + [(0.2,{'c':1})]*201 + [(0.4,{'b':1,'c':1})]*264)
    >>> s._get_feature_count()
    8
    >>> len(s._bayes_select())
    884
    >>> s._train()
    >>> round_data(s._coef_format())
    {'a': -0.1, 'c': -0.2, 'b': 0.2, '(Intercept)': 0.4}
    >>> round_data(s.estimate({'a':1, 'b':1, 'c':1}))
    0.57
    >>> round_data(s.validation([(0.6,{'a':1, 'b':1, 'c':1}), (0.4,{'a':1,'c':1})]))
    [(0.6, 0.57), (0.4, 0.52)]
    '''
    def __init__(self, clientid = 0, modelname = "stats", model_tag = ""):
        #feature -> w  eg. input_1 -> 0.234
        self.coef = {}
        #r column -> feature name eg. input_1 -> 家教
        self.r2p = {}
        self.modelname = modelname
        self.model_tag = model_tag
        self.clientid = clientid
        self.prefix = ''
        #set prefix with clientid, model_tag
        self.set_model_tag(model_tag)

    def set_model_tag(self, model_tag):
        self.model_tag = model_tag
        #兼容多个clientid
        clientids = self.clientid
        if not hasattr(self.clientid, "__iter__"):
            clientids = [self.clientid]

        #prefix for save train data, output model
        if not os.path.exists('r'):
            os.mkdir('r')

        if not model_tag:
            self.prefix = "r/%s." % ('_'.join(map(str, clientids)))
        else:
            self.prefix = "r/%s_%s." % (model_tag, '_'.join(map(str, clientids)))

        if FLAGS.prefix:
            self.prefix += FLAGS.prefix

    # signal集合的collections, depreceted
    # result : { signal:[sum convert,count],... }
    def _signal_stats(self):
        logger.debug('enter sig2stt')
        sig2stt = {}
        for result,sig in self.signallst:
            if result == None:
                continue
            for k,_ in sig.items():
                if k.startswith('hour_') or k.startswith('weekday_'):
                    continue
                stt = sig2stt.setdefault(k,[0,0])
                stt[0] += result
                stt[1] += 1
        logger.info('total signal number %s' % len(sig2stt))
        return sig2stt

    # 每样本转化率归一化 --> 每个feature  ~ 总的convert/样本数/平均转化率 depreceted
    def _bayes_train_signals(self):
        avgconvert = sum([r for r,_ in self.signallst])*1.0/len(self.signallst) # 所有feature平均转化率
        sig2modify = {}
        for k, (sttsum,sttcount) in self.stats.items():
            sig2modify[k] = sttsum*1.0/sttcount/avgconvert
        return sig2modify

    # depreceted
    def _get_feature_count(self, amplify=1):
        size = len(self.signallst)
        count = 0
        #for a,b in [(50,1000),(100,5000),(150,30000),(200,1000000)]: # 个数
        for a,b in [(100,1000),(200,5000),(300,30000),(400,1000000)]: # 个数
            count += min(size,b)/a
            size -= b
            if size < 0:
                break
        count *= amplify
        return int(count)

    # depreceted
    def _bayes_select(self, amplify=1):
        count = self._get_feature_count(amplify)
        sig2modify = self._bayes_train_signals()

        # 样本数 * (1-每样本平均转化率)
        sig2weight = {}
        for k,(_,sttcount) in self.stats.items():
            sig2weight[k] = sttcount*abs(1-sig2modify[k])

        # 取weight最高的signals
        self.sig2pop = mydict(sig2weight).top(count)

        self.training_data = []
        for result,sig in self.signallst:
            self.training_data.append((result,dict([(k,v) for k,v in sig.items() if k in self.sig2pop])))
        return self.training_data

    # depreceted
    def _train(self):
        logger.debug('glm tranning, sample size %s' % len(self.signallst))
        newlst = []
        for result,sig in self.training_data:
            if result > 1.0:
                result = 1.0
            newlst.append(dict([(k,v) for k,v in sig.items()]+[('result',result)]))
        self.coef = glm_train(newlst, self._get_pname_filename(), self._get_data_filename(),
                              self._get_model_filename(), self._get_summary_filename())

    # depreceted
    def old_train(self, signallst):
        self._feed(signallst)
        self._bayes_select()

        for sig,_ in self.sig2pop.items():
            logger.debug("%s %s" % (sig, self.stats[sig]))

        self._train()

    # depreceted
    def _coef_format(self):
        for k, v in self.coef.items():
            self.coef[k] = float(v)
        return self.coef

    def dump(self):
        return cPickle.dumps(self.coef)

    def load(self, s):
        self.coef = cPickle.loads(s)

    def dumptofile(self,):
        if not FLAGS.save:
            filename = self.prefix + '.model'
            cPickle.dump(self.coef, open(filename, 'w'))

    def dump_feature(self,):
        filepath = '%s%s_fw.txt' % (self.prefix, self.modelname)
        logger.info("dump feature weight to %s" % filepath)
        fp = file(filepath, "w")
        feature_weight = sorted(self.coef.items(), key = lambda t : t[1], reverse = True)

        g = lambda x : x.encode('utf-8') if isinstance(x,unicode) else x
        fp.write("\n".join(['%-30s : %+.9f' % (g(k), v) for k, v in feature_weight]))
        fp.close()

    def loadfromfile(self, filename):
        self.coef = cPickle.load(open(filename))

    def stat_coef(self):
        return len(self.coef)

    def _parse_coef(self, output):
        self.coef = {}
        for line in list(open(output))[1 : ]:
            d = line.split()
            var = d[0][1 : -1]
            try:
                f = float(d[1])
                self.coef[self.r2p.get(var, var)] = f
            except ValueError:
                pass

    def _get_summary_filename(self):
        return "%s%s.summary.txt" % (self.prefix, self.modelname)

    def _get_model_filename(self):
        return "%s%s.coef.txt" % (self.prefix, self.modelname)

    def _get_validation_filename(self):
        return "%s%s.validation.txt" % (self.prefix, self.modelname)

    def _get_pname_filename(self):
        return "%s%s.pname.txt" % (self.prefix, self.modelname)

    def _get_data_filename(self):
        return "%s%s.data.txt" % (self.prefix, self.modelname)

    def _load_pname(self):
        self.r2p = {}
        for s in file(self._get_pname_filename()):
            kv = s.strip().split(' ', 1)
            self.r2p['input_%s' % (int(kv[0])-1)] = kv[1]

    def _dump_signals(self, cut_to_one=True, treat_as_one=1.0):
        newlst = []
        for result,sig in self.signallst:
            if abs(treat_as_one - 1.0) > 0.00001:
                result *= 1.0/treat_as_one
            if cut_to_one and result > 1.0:
                result = 1.0
            newlst.append(dict([(k, v) for k, v in sig.items()]+[('result', result)]))

        if not os.path.exists('r'):
            os.mkdir('r')

        if FLAGS.new_signal:
            _, self.r2p, _ = dump_signallst(newlst, self._get_pname_filename(), self._get_data_filename())
        else:
            self._load_pname()

        return self._get_data_filename(), self._get_model_filename()

    def _feed(self, signallst):
        self.signallst = signallst
        self.stats = self._signal_stats()

    def train(self, signallst, cut_to_one=True, treat_as_one=1.0):
        self._feed(signallst)
        input, output = self._dump_signals(cut_to_one, treat_as_one)
        self.regression(input, output)
        self._parse_coef(output)
        self.dump_feature()

    def regression(self, input, output):
        raise "Sub class should implement this!"

    def validation(self, signallst):
        results = []
        for y, s in signallst:
            e = self.estimate(s)
            results.append((y, e))
        return results

    def dump_validation(self, signallst):
        results = self.validation(signallst)
        f = open(self._get_validation_filename(), "w")
        for y,e in results:
            f.write("%s:b,%s:m\n" % (y, e))
        f.close()

    def estimate(self, signal):
        sig_feature = dict([(k, v) for k, v in  signal.items() if k in self.coef])
        result,self.detail = _logit_calc(sig_feature, self.coef)
        return result

    def estimate_with_detail(self,signal):
        kvs = [(k,v) for k, v in  signal.items() if k in self.coef]
        intercept = float(self.coef['(Intercept)'])
        exp = sum([v * float(self.coef[k]) for k, v in kvs], intercept)

        detail = ['%s=%s*%s' % (k,v,self.coef[k]) for k,v in kvs]
        detail.extend(['(Intercept)=%s' % intercept, 'exp=%s' % exp])

        if -exp > 100:
            result = 0
        else:
            result = 1/(1+math.exp(-exp))
        return result, detail

class old_stats_model(stats_model):
    def __init__(self, clientid=0, model_tag=""):
        stats_model.__init__(self, clientid, "old", model_tag)

    def train(self, signallst):
        self._feed(signallst)
        self._bayes_select()
        self._train()

class logit_stats_model(stats_model):
    '''
    >>> from pygaga.helpers.utils import round_data
    >>> FLAGS.logit_split_cols = 1
    >>> FLAGS.logit_split_rows = 2
    >>> s = logit_stats_model()
    >>> s._feed([(0.1, {'a':1,'c':1,'d':1})]*199 + [(0.5, {'a':1, 'b':1,'e':1})]*220 + [(0.2,{'c':1,'f':1})]*201 + [(0.4,{'b':1,'c':1,'g':1})]*264)
    >>> input, output = s._dump_signals()
    >>> regression(input, output, False)
    >>> s._parse_coef(output)
    >>> round_data(s.coef)
    {'c': -0.41, 'b': 0.98, '(Intercept)': -0.98, 'd': -0.81}
    >>> round_data(s.estimate({'a':1, 'b':1, 'c':1}))
    0.4
    '''
    def __init__(self, clientid=0, model_tag=""):
        stats_model.__init__(self, clientid, "logit", model_tag)

    def regression(self, input, output):
        regression(input, output, False)

class pca_stats_model(stats_model):
    '''
    >>> from pygaga.helpers.utils import round_data
    >>> FLAGS.logit_split_cols = 1
    >>> FLAGS.logit_split_rows = 2
    >>> s = pca_stats_model()
    >>> s._feed([(0.1, {'a':1,'c':1,'d':1})]*199 + [(0.5, {'a':1, 'b':1,'e':1})]*220 + [(0.2,{'c':1,'f':1})]*201 + [(0.4,{'b':1,'c':1,'g':1})]*264)
    >>> input, output = s._dump_signals()
    >>> regression(input, output)
    >>> s._parse_coef(output)
    >>> round_data(s.coef)
    {'c': -0.38, 'b': 0.57, 'e': 0.38, 'd': -0.41, 'g': 0.34, 'f': -0.41, '(Intercept)': -0.95}
    >>> round_data(s.estimate({'a':1, 'b':1, 'c':1}))
    0.32
    '''
    def __init__(self, clientid=0, model_tag=""):
        stats_model.__init__(self, clientid, "pca", model_tag)

    def regression(self, input, output):
        regression(input, output)

# FLAGS.family should be poisson
class poisson_stats_model(stats_model):
    def __init__(self, clientid=0, model_tag=""):
        assert FLAGS.family == "poisson"
        stats_model.__init__(self, clientid, "poisson", model_tag)

    def train(self, signallst):
        self._feed(signallst)
        input, output = self._dump_signals(False)
        regression(input, output)
        self._parse_coef(output)
        self.dump_feature()

    def estimate(self, signal):
        sig_feature = dict([(k, v) for k, v in  signal.items() if k in self.coef])
        result,self.detail = _poisson_calc(sig_feature, self.coef)
        return result

class svd_stats_model(stats_model):
    '''
    >>> from pygaga.helpers.utils import round_data
    >>> s = svd_stats_model()
    >>> s._feed([(0.1, {'a':1,'c':1,'d':1})]*199 + [(0.5, {'a':1, 'b':1,'e':1})]*220 + [(0.2,{'c':1,'f':1})]*201 + [(0.4,{'b':1,'c':1,'g':1})]*264)
    >>> input, output = s._dump_signals()
    >>> svd_regression(input, output)
    >>> s._parse_coef(output)
    >>> round_data(s.coef)
    {'a': -0.44, 'c': -0.51, 'b': 0.94, 'e': 0.1, 'd': -0.54, 'g': 0.84, 'f': -0.81, '(Intercept)': -0.48}
    >>> round_data(s.estimate({'a':1, 'b':1, 'c':1}))
    0.38
    '''
    def __init__(self, clientid=0, model_tag=""):
        stats_model.__init__(self, clientid, "svd", model_tag)

    def regression(self, input, output):
        svd_regression(input, output)

class lg_stats_model(stats_model):
    '''
    >>> from pygaga.helpers.utils import round_data
    >>> s = lg_stats_model()
    >>> s._feed([(0.1, {'a':1,'c':1,'d':1})]*199 + [(0.5, {'a':1, 'b':1,'e':1})]*220 + [(0.2,{'c':1,'f':1})]*201 + [(0.4,{'b':1,'c':1,'g':1})]*264)
    >>> input, output = s._dump_signals()
    >>> lg_regression(input, output)
    >>> s._parse_coef(output)
    >>> round_data(s.coef)
    {'a': -0.38, 'c': -0.71, 'b': 0.51, 'e': 0.29, 'd': -0.67, 'g': 0.22, 'f': -0.25, '(Intercept)': -0.42}
    >>> round_data(s.estimate({'a':1, 'b':1, 'c':1}))
    0.27
    '''
    def __init__(self, clientid=0, model_tag=""):
        stats_model.__init__(self, clientid, "lg", model_tag)

    def regression(self, input, output):
        lg_regression(input, output) # todo: add noweight support?

class const_stats_model(stats_model):
    '''
    >>> from pygaga.helpers.utils import round_data
    >>> s = const_stats_model()
    >>> s.train([(0.1, {'a':1,'c':1,'d':1})]*199 + [(0.5, {'a':1, 'b':1,'e':1})]*220 + [(0.2,{'c':1,'f':1})]*201 + [(0.4,{'b':1,'c':1,'g':1})]*264)
    >>> round_data(s.coef)
    {'Average': 0.02}
    >>> round_data(s.estimate({'a':1, 'b':1, 'c':1}))
    0.02
    '''
    def __init__(self, clientid=0, model_tag=""):
        stats_model.__init__(self, clientid, "const", model_tag)

    def train(self, signallst):
        self.coef = {}
        # (NOTE:yuhuan) 1.96*1.96*0.02*0.98/0.005/0.005 = 3011.8144
        # 3000 个 session 可以保证如果平均转化率在 2% 附近，那么估计
        # 的 95% 置信区间为 [1.5%, 2.5%]，凑合使用。如果转化率更高其实需要更多的样本，
        # 此处因陋就简。
        if len(signallst) > 3000:
            self.coef["Average"] = sum([v for v, _ in signallst]) / len(signallst)
        else:
            self.coef["Average"] = 0.02
        logger.debug("Average conversion rate is %s" % self.coef["Average"])

    def estimate(self,signal):
        return self.coef["Average"]

    def estimate_with_detail(self,signal):
        return self.coef["Average"], 'const'

class bayesian_stats_model(stats_model):
    '''
    >>> from pygaga.helpers.utils import round_data
    >>> s = bayesian_stats_model()
    >>> s.train([(0.1, {'a':1,'c':1,'d':1})]*199 + [(0.5, {'a':1, 'b':1,'e':1})]*220 + [(0.2,{'c':1,'f':1})]*201 + [(0.4,{'b':1,'c':1,'g':1})]*200, [('a','c'), ('c','d')])
    '''
    def __init__(self, clientid=0, model_tag=""):
        stats_model.__init__(self, clientid, "bayesian", model_tag)

    def train(self, signallst, keys):
        pass


def chi_square(signallst):
    chi_square_dict = {}
    N = 0
    sample_pos = 0
    scale = 1
    leftfea = {}

    for signal in signallst:
        N = N + 1 * scale
        if signal[0] > 0:
            sample_pos += 1 * scale
        for k, v in signal[1].items():
            chi_square_dict.setdefault(k, [0,0])
            if signal[0] > 0:
                chi_square_dict[k][0] += 1 * scale
            else:
                chi_square_dict[k][1] += 1 * scale

    for fea, frquence in chi_square_dict.items():
        a = frquence[0]
        b = frquence[1]
        c = sample_pos - a
        d = N - a - b - c
        chi = 0
        if a + c != 0 and b + d != 0 and a + b != 0 and c + d != 0:
            chi = 1.0 * N * (a * d - b * c) ** 2 / ((a + c) * (b + d) * (a + b) * (c + d))

        #print fea,chi,N,sample_pos,a,b,c,d
        leftfea[fea] = chi

    #按卡方值排序，取90%
    keys = sorted(leftfea.items(), key=itemgetter(1), reverse=True)
    index = int(len(keys)*1)
    keys = keys[:index]
    leftfea = []
    for key in keys:
        leftfea.append(key[0])

    for idx, signal in enumerate(signallst):
        d = signal[1].copy()
        for key in signal[1]:
            if not key in leftfea:
                del(d[key])
        signallst[idx] = (signallst[idx][0], d)

    return signallst

def entropy(data):
    total = sum(data)
    ent = 0.0
    for item in data:
        p = item * 1.0 / total
        if p > 0:
            ent -= p * math.log(p, 2)

    return ent

def info_gain(signallst):
    info_gain_dict = {}
    N = 0
    sample_pos = 0
    scale = 1
    leftfea = {}
    for signal in signallst:
        N = N + 1 * scale
        if signal[0] > 0:
            sample_pos += 1 * scale
        for k, v in signal[1].items():
            info_gain_dict.setdefault(k, [0,0])
            if signal[0] > 0:
                info_gain_dict[k][0] += 1 * scale
            else:
                info_gain_dict[k][1] += 1 * scale

    sum_ent = entropy([sample_pos, N - sample_pos])
    for fea, frquence in info_gain_dict.items():
        fea_ent = entropy(frquence)
        nofea_ent = entropy([sample_pos - frquence[0], N - sample_pos - frquence[1]])
        ent = sum_ent - sum(frquence) * 1.0/N * fea_ent - (1 - sum(frquence) * 1.0/N) * nofea_ent
        if ent>0.000001:
            leftfea[fea] = ent

    for idx, signal in enumerate(signallst):
        d = signal[1].copy()
        for key in signal[1]:
            if not key in leftfea:
                del(d[key])
        signallst[idx] = (signallst[idx][0], d)

    return signallst

def get_model_instance(clientid=0, model_name='', model_tag=''):
    if not model_name:
        model_name = FLAGS.modelname
    logger.info("instance %s model %s tag for clientid=%s" % (model_name, model_tag, clientid))

    model_class = getattr(sys.modules[__name__], "%s_stats_model" % model_name)
    return model_class(clientid=clientid, model_tag=model_tag)

if __name__ == "__main__":
    import doctest
    from pygaga.helpers.logger import log_init
    log_init()
    doctest.testmod()
