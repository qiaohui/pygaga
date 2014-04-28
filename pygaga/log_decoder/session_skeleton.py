import sys
from collections import defaultdict
from pygaga.log_decoder.session_loader import load

for session in load(sys.argv[1], True):
    import pdb; pdb.set_trace()
    print session

