import time
from pygaga.helpers.lock import lock
from pygaga.helpers.logger import log_init

if __name__ == "__main__":
    log_init("Logger")
    print "entering lock"
    with lock("mylock"):
         time.sleep(20)
         print "running"
    print "done"

