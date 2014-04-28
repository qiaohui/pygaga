
import time
from itertools import islice, chain

def batch(iterable, size):
    it = iter(iterable)
    while True:
        bi = islice(it, size)
        yield chain([bi.next()], bi)

def chunks(l, n, fn_len=len):
    for i in xrange(0, fn_len(l), n):
        yield l[i:i+n]

def droplimit(rate, per, items):
    allowance = rate
    last_check = time.time()

    for item in items:
        current = time.time()
        time_passed = current - last_check
        last_check = current
        allowance += time_passed * (rate / per)
        if allowance > rate:
            allowance = rate
        if (allowance >= 1.0):
            allowance -= 1.0;
            yield item

def waitlimit(rate, per, items):
    allowance = max(rate * 0.1, 1.0)
    last_check = time.time()

    for item in items:
        while True:
            current = time.time()
            time_passed = current - last_check
            last_check = current
            allowance += time_passed * (rate / per)

            #print time_passed, allowance, rate, per
            if allowance > rate:
                allowance = rate
            if (allowance >= 1.0):
                allowance -= 1.0;
                yield item
                break
            else:
                time.sleep(0.025)

if __name__ == "__main__":
    def input_generator():
        for i in range(1000):
            time.sleep(0.05)
            yield i

    #for item in droplimit(5.0, 3.0, input_generator()):
    #    print item, time.time()
    for item in waitlimit(60.0, 60.0, input_generator()):
        print item, time.time()
