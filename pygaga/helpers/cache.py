from collections import deque
import time

def lru_cache(maxsize, maxsec=0, hold_exception=0):
    '''Decorator applying a least-recently-used cache with the given maximum size.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.

    Chris: add support for hold exception for several times, exception statistics stored in f.exception_hits
    '''
    def decorating_function(f):
        cache = {}              # mapping of args to results
        exception_cache = {}    # mapping of args to exceptions
        queue = deque()         # order that keys have been accessed
        refcount = {}           # number of times each key is in the access queue
        def wrapper(*args):

            # localize variable access (ugly but fast)
            _cache=cache; _len=len; _refcount=refcount; _maxsize=maxsize; _exception_cache=exception_cache
            queue_append=queue.append; queue_popleft = queue.popleft; _hold_exception=hold_exception; _maxsec=maxsec

            # get cache entry or compute if not found
            try:
                cache_obj = _cache[args]
                if _maxsec == 0 or time.time()-cache_obj['t'] < _maxsec:
                    result = cache_obj['v']
                    wrapper.hits += 1
                else:
                    result = f(*args)
                    _cache[args] = {'v':result, 't':time.time()}
                    wrapper.misses += 1
            except KeyError:
                if _hold_exception > 0:
                    try:
                        last_exception = _exception_cache[args]
                        last_exception['c'] += 1
                        if last_exception['c'] < _hold_exception and (_maxsec == 0 or time.time()-last_exception['t'] < _maxsec):
                            wrapper.exception_hits += 1
                            raise last_exception['e']
                        else:
                            try:
                                result = f(*args)
                                _cache[args] = {'v':result, 't':time.time()}
                            except Exception, e:
                                _exception_cache[args] = {'e':e, 'c':0, 't':time.time()}
                                raise
                    except KeyError:
                        try:
                            result = f(*args)
                            _cache[args] = {'v':result, 't':time.time()}
                        except Exception, e:
                            _exception_cache[args] = {'e':e, 'c':0, 't':time.time()}
                            raise
                else:
                    result = f(*args)
                    _cache[args] = {'v':result, 't':time.time()}
                wrapper.misses += 1

            # record that this key was recently accessed
            queue_append(args)
            _refcount[args] = _refcount.get(args, 0) + 1

            # Purge least recently accessed cache contents
            while _len(_cache) > _maxsize:
                k = queue_popleft()
                _refcount[k] -= 1
                if not _refcount[k]:
                    del _cache[k]
                    del _refcount[k]

            # Periodically compact the queue by duplicate keys
            if _len(queue) > _maxsize * 4:
                for _ in [None] * _len(queue):
                    k = queue_popleft()
                    if _refcount[k] == 1:
                        queue_append(k)
                    else:
                        _refcount[k] -= 1
                assert len(queue) == len(cache) == len(refcount) == sum(refcount.itervalues())

            return result
        wrapper.__doc__ = f.__doc__
        wrapper.__name__ = f.__name__
        wrapper.hits = wrapper.misses = wrapper.exception_hits = 0
        return wrapper
    return decorating_function

if __name__ == '__main__':

    @lru_cache(maxsize=20, maxsec=2)
    def f(x, y):
        return 3*x+y

    @lru_cache(maxsize=20, hold_exception=10)
    def e(x, y):
        print "got exception"
        raise Exception("abc")

    f(1, 2)
    f(1, 2)
    time.sleep(4)
    f(1, 2)
    print f.hits, f.misses

    domain = range(5)
    from random import choice
    for i in range(1000):
        r = f(choice(domain), choice(domain))

    for i in range(30):
        try:
            r = e(1, 2)
        except Exception, ee:
            pass
    time.sleep(3)
    try:
        e(1,2)
    except:
        pass

    print f.hits, f.misses, e.exception_hits

