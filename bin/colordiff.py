#!/usr/bin/env python

import sys
import pHash

if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2]
    d1 = pHash.image_digest(src, 1.0, 1.0, 180)
    d2 = pHash.image_digest(dst, 1.0, 1.0, 180)
    print pHash.crosscorr(d1, d2)[1]
