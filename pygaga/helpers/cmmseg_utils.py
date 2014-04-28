#coding=utf-8

import cmmseg
import os
import cPickle
import gflags
import traceback
import logging
import tst
from pygaga.helpers.nlp import lazy_dict

logger = logging.getLogger('cmmseg')

FLAGS = gflags.FLAGS
gflags.DEFINE_boolean('use_client_cmmseg', True, "gen cmmseg dict")
gflags.DEFINE_string('worddict_directory', '/usr/local/etc', "Word dictionary directory.")

def init_cmmseg_dict(dict_path):
    logger.info("init cmmseg %s" % dict_path )
    try:
        cmmseg.instance(dict_path)
    except:
        cmmseg.init(dict_path)

def cmmseg2_seg(w, encoding='utf8'):
    segs = []
    if type(w) != unicode:
        w = w.decode(encoding)
    for x in cmmseg.segment(w.encode('utf8')):
        try:
            x = x.decode("utf8")
            segs.append(x)
        except:
            pass
    return segs

def split_entities(w, entity_words):
    """
    >>> #split_entities("我爱北京天T恤安北京门", ['T恤','北京'])
    ['\\xe6\\x88\\x91\\xe7\\x88\\xb1', '\\xe5\\x8c\\x97\\xe4\\xba\\xac', '\\xe5\\xa4\\xa9', 'T\\xe6\\x81\\xa4', '\\xe5\\xae\\x89', '\\xe5\\x8c\\x97\\xe4\\xba\\xac', '\\xe9\\x97\\xa8']
    """
    t = tst.TST()
    for ew in entity_words:
        t.put(ew, ew)
    results = t.scan(w, tst.TupleListAction())
    return [(x[0],x[1]) for x in results]

def cmmseg2(w, encoding='utf8', entity_words=[]):
    """
    >>> cmmseg2("我爱北京天安门和T恤", entity_words=['T恤','t恤'])
    [u'\u6211\u7231', u'\u5317\u4eac', u'\u5929\u5b89\u95e8', u'\u548c', u'T\u6064']
    """
    try:
        if entity_words:
            words = split_entities(w.decode(encoding).encode('utf8'), entity_words)
            results = []
            for word, is_entity in words:
                if is_entity < 0:
                    results.extend(cmmseg2_seg(word, 'utf8'))
                else:
                    results.append(word.decode('utf8'))
            return results
        else:
            return cmmseg2_seg(w, encoding)
    except Exception, e:
        if 'Needs load segment dictionary library frist' in e.message:
            init_cmmseg_dict('/usr/local/etc')
        try:
            return cmmseg2_seg(w, encoding)
        except:
            print traceback.format_exc()
    return []

def gen_cmmseg_dict(dictionary, cmmseg_dir):
    ds ='\n'.join(['%s\t%s\nx:%s' % (k, v, v)
                   for k, v in dictionary.items()
                   ]
                  )
    os.system("mkdir -p %s" % cmmseg_dir)
    cmmseg_df = "%s/unigram.txt" % cmmseg_dir
    cmmseg_lib = "%s/uni.lib" % (cmmseg_dir)

    mmseg_ini = "\n".join(["[mmseg] ",
                           "merge_number_and_ascii=0; ",
                           "number_and_ascii_joint=-; ",
                           "compress_space=1; ",
                           "seperate_number_ascii=0; ",
                           ""
                           ]
                          )
    fp = file("%s/mmseg.ini" % cmmseg_dir, "w")
    fp.write(mmseg_ini)
    fp.close()

    fp = file(cmmseg_df, "w")
    fp.write('%s\n' % ds)
    fp.close()

    #gen cmmseg dict
    cmd = "mmseg -u %s" % cmmseg_df
    logger.info(cmd)
    os.system(cmd)

    cmd = "mv %s.uni %s/uni.lib" % (cmmseg_df, cmmseg_dir)
    logger.info(cmd)
    os.system(cmd)

def append_to_cmmseg_dict(dictionary, new_cmmseg_dir, org_cmmseg_dir="/usr/local/etc"):
    """
    dictionary encoding -- utf8
    >>> dictionary = {"我爱":1, "词非词":1}
    >>> append_to_cmmseg_dict(dictionary, "/tmp")
    >>> init_cmmseg_dict("/tmp")
    >>> cmmseg2_seg("我爱词非词北京")
    [u'\u6211\u7231', u'\u8bcd\u975e\u8bcd', u'\u5317\u4eac']
    """
    org_file = os.path.join(org_cmmseg_dir, "unigram.txt")
    s = open(org_file).read()
    org_dict = dict([l.strip().split('\t') for l in s.split("\n") if l.strip() and not l.startswith('x:')])
    org_dict.update(dictionary)
    gen_cmmseg_dict(org_dict, new_cmmseg_dir)

def load_worddict():
    if os.path.exists('%s/' % (FLAGS.worddict_directory)):
        wd_file = '%s/' % (FLAGS.worddict_directory)
        dictionary = cPickle.load(open(wd_file))

        #cmmseg lib
        cmmseg_dir = "%s_cmmseg" % wd_file
        cmmseg_lib = "%s/uni.lib" % (cmmseg_dir)

        if FLAGS.use_client_cmmseg:
            if not os.path.isfile(cmmseg_lib):
                gen_cmmseg_dict(dictionary, cmmseg_dir)
            #init cmmseg dict
            init_cmmseg_dict('%s' % cmmseg_dir)
        else:
            init_cmmseg_dict('/usr/local/etc')

    else:
        if FLAGS.use_client_cmmseg:
            init_cmmseg_dict('/usr/local/etc')
        dictionary = {}
        logger.warning("keyword_convert not have worddict")
    return lazy_dict(dictionary.items())

if __name__ == "__main__":
    import doctest
    doctest.testmod()
