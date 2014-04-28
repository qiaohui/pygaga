import cPickle
from pygaga.log_decoder.log_decoder import decode_click_ex, decode_click

def load(session_file, dec=True):
    for sess in cPickle.load(open(session_file)):
        if dec:
            for p in sess['paths']:
                if p['cate'] == 'click':
                    p['clkex'] = decode_click_ex(p['clkex'])
                    p['clkobj'] = decode_click(p['clkobj'])
        yield sess
