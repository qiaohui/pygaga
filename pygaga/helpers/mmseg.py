# coding=gbk

import math
import time
import logging
from pygaga.corpus import sogou_dict_path
from pygaga.helpers.i18n import smartdecode
from pygaga.helpers.nlp import lazy_dict
import traceback

logger = logging.getLogger('mmseg')

specialch = dict([(c,' ') for c in u'''1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
"-/<>#\'!:,._+|\\{}[]();��������=~����������?&%@^*���������������Уࣤ$��������������L�ޡ������`�������������K�I�������C����i�h
������ᩦ���������Ψq�r���أ��~�ީU�t�ۣݩm�����ɩI�S��񨌡����A�@�����ᡴ���������`���`�ܩ`���������詃�ũp��
���u�������ȡҡá��ʡϡΨJ�U�������詵�z�x�����V���
�����Ӥ����ͤ롹����������ȥ�`�������`�ȥ饤�󡹡�����餵�󡸥ե������`�ܩ`���������
����֣������å����������Ρ�����󥰡����������������������������ɨӨڨި��ƨʨͨШԨר�
��������������Ѩy�ѣ��񣼣�����¡ơ̡بp�|�}�~���O�ӡ�֡٣��ԡܡݨQ�R�n�ڡۨr������������թ����ĩw�F�k�k�|
���a�D�򣪣��ɩo�ܩl�ߡ���������š�婯���䡼���e���Ģ��ߡС�s�ʤʨ��������������c�����T���M
�����������ששש����������ǩ��שש����t�t���s�^�m�a�t�Ũt��ΨT���ȩЩةةШw�v�����쩮�ȩ�
��G���������������O�O�H���Ш���������������������
���£ãģţƣǣȣɣʣˣ̣ͣΣϣУѣңӣԣգ֣ףأ٣�
���������������������������������
��������������
����������������
�٢ڢۢܢݢޢߢ��⨒
�ŢƢǢ�
��������������������
�����Ũ��������騬���ɨ������姤��Ԩ�����������������������������
���¦æĦŦƦǦȦɦʦ˦̦ͦΦϦЦѦҦӦԦզ֦�
�������������������������������Ǧ��ѧ𧥧���ҧ�ӧ�觲������
����Ϥˤʤ�Ǥ�äƤޤ��ޤ��Ƥ䤡�ڥפإؤکY���㤢���������Ȥ�����椭�ɤ��ɤ��Хƥ��Ӥҥ��
'''])

def enum_sogoudict():
    for line in open(sogou_dict_path):
        try:
            wd,freq = line.split()[:2]
            wd = wd.decode('gbk')
            freq = int(freq)
            yield wd,freq
        except:
            pass

def extend_sogoudict(ext_dicts):
    for wd, freq in enum_sogoudict():
        yield wd, freq
    for wd, freq in ext_dicts:
        yield wd, freq

def lines2dict(lines):
    for l in lines:
        yield l, 2

sogoudict = lazy_dict(enum_sogoudict())

def getwd(txt,idx=0,maxwdlen=1e10,dictionary=sogoudict):
    '''
    >>> [(wd,f) for wd,f in getwd('�Ұ������찲��')]
    [('\\xce', 0)]
    >>> [(wd,f) for wd,f in getwd('�Է�')]
    [('\\xb3', 0)]
    '''
    pref2wd2f,ch2f = dictionary.load()
    if idx >= len(txt):
        return
    yield txt[idx],ch2f.get(txt[idx],0)
    for wd,f in pref2wd2f.get(txt[idx:idx+2],{}).items():
        if txt[idx:idx+len(wd)] != wd:
            continue
        if len(wd) > maxwdlen:
            continue
        yield wd,f

def get3wd(txt,idx=0,wdprev=[],pprev=0,maxwdlen=1e10,dictionary=sogoudict):
    '''
    >>> [(wd,f) for wd,f in get3wd('�Ұ������찲��')]
    [(0.0, ['\\xce', '\\xd2', '\\xb0'])]
    '''
    for wd,f in getwd(txt,idx,maxwdlen=maxwdlen,dictionary=dictionary):
        wdnext = wdprev+[wd]
        pnext = pprev+f/(0.5+math.log(len(wd)))
        if len(wdnext) == 3 or len(wd)+idx >= len(txt):
            yield pnext,wdnext
        else:
            for p,wdlst in get3wd(txt,idx+len(wd),wdnext,pnext,dictionary=dictionary):
                yield p,wdlst

def pre_text(txt):
    if isinstance(txt,str):
        txt = smartdecode(txt)
    chlst = [' ' if c in specialch and not c.lower() in '0123456789abcdefghijklmnopqrstuvwxyz' else c for c in txt]
    if not chlst:
        return []
    enchsep = [chlst[0]]
    a1 = ord(chlst[0])
    aspace = ord(' ')
    for ch in chlst[1:]:
        a2 = ord(ch)
        if a1 > 256 and a2 < 128 and a2 != aspace: enchsep.append(' ')
        if a1 < 128 and a2 > 256 and a1 != aspace: enchsep.append(' ')
        enchsep.append(ch)
        a1 = a2
    txt = ''.join(enchsep)
    return txt

def mmseg2(txt,maxwdlen = 1e10,dictionary=sogoudict):
    '''
    >>> mmseg2('�Ұ������찲��')
    [u'\u6211\u7231', u'\u5317\u4eac', u'\u5929\u5b89\u95e8']
    '''
    if not dictionary:
        dictionary=sogoudict

    txt = pre_text(txt)

    ret = []
    retp = 0
    try:
        pref2wd2f,ch2f = dictionary.load()
    except:
        if dictionary != sogoudict:
            dictionary=sogoudict
            pref2wd2f,ch2f = dictionary.load()
        else:
            logger.warning(traceback.format_exc())

    for ch,f in ch2f.items():
        pref2wd2f[ch] = {ch:f}
    for txt in txt.split():
        if ord(txt[0]) < 128:
            if len(txt) > 1 and txt[:2] in pref2wd2f and txt in pref2wd2f[txt[:2]]:
                ret.append(txt)
            continue
        while txt:
#            lst = sorted([(p/sum([len(wd) for wd in wdlst]),wdlst) for p,wdlst in get3wd(txt)])
            lst = sorted([(p,wdlst) for p,wdlst in get3wd(txt,maxwdlen=maxwdlen,dictionary=dictionary)])
#            for p,wdlst in lst:
#                print txt[:20],p,' '.join(wdlst)
            wd = lst[-1][1][0]
            retp += pref2wd2f.get(wd[:2],{}).get(wd,0)
            ret.append(wd)
            txt = txt[len(wd):]
    return ret

if __name__ == "__main__":
    import doctest
    doctest.testmod()
