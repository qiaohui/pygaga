from pygaga.helpers.cache import lru_cache

@lru_cache(maxsize=1000, maxsec=10)
def f(x, y):
      return x+y

if __name__ == "__main__":
    for i in range(10):
        f(1, 2)
    print f.hits, f.misses
