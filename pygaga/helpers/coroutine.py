#!/usr/local/bin/python2.6

def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.next()
        return cr
    return start

if __name__ == '__main__':
    @coroutine
    def grep(pattern):
        print "looking for %s" % pattern
        while True:
            line = (yield)
            if pattern in line:
                print line,

    g = grep("python")
    g.send("test1")
    g.send("test2")
    g.send("python rock!")
