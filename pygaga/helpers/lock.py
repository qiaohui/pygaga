import errno
import os
import logging
import gflags
import sys
import time
import traceback
from contextlib import contextmanager
from socket import gethostname

from pygaga.helpers.utils import pid_exists, get_pid_running_seconds

# optional redis/zookeeper support
try:
    import pykeeper
    from zookeeper import NoNodeException
    from redis import Redis
except:
    pass

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('lock', True, "Lock this")
gflags.DEFINE_boolean('autounlock', True, "Unlock when exit.")
gflags.DEFINE_boolean('unlock', False, "Clean this lock")
gflags.DEFINE_boolean('usefilelock', True, "Use file lock")
gflags.DEFINE_boolean('usezklock', False, "Use zookeeper lock")
gflags.DEFINE_boolean('useredislock', False, "Use redis lock")
gflags.DEFINE_string('redis_lockserver', "127.0.0.1", "Redis lock server ip")
gflags.DEFINE_string('zk_lockserver', "127.0.0.1:2181", "Comma splitted zookeeper server:port")
gflags.DEFINE_string('zk_lockpath', "/com/langtaojin/guang", "Zookeeper path")
gflags.DEFINE_string('file_lockpath', "/var/lock", "File lock path")
gflags.DEFINE_boolean('kill_lock_pid', False, "Is kill locked pid")
gflags.DEFINE_integer('lock_pid_expire_seconds', 0, "How many seconds lock pid will expire, if expire will be killed")

@contextmanager
def check_filelock(key, value, logger):
    lockpath = "%s/%s.lock" % (FLAGS.file_lockpath, key)

    if FLAGS.unlock:
        try:
            os.remove(lockpath)
            logger.info('%s has been deleted', lockpath)
        except OSError, e:
            if e.errno == errno.ENOENT: #no such file
                pass
            else:
                logger.error("clean lock failed %s, error %s", lockpath, traceback.format_exc())
                sys.exit(1)
        except:
            logger.error("clean lock failed %s, error %s", lockpath, traceback.format_exc())
            sys.exit(1)
        sys.exit(0)

    if os.path.exists(lockpath):
        content = open(lockpath).read().strip()
        hostname, pid, ts = content.split(":")
        pid = int(pid.strip())
        if pid_exists(pid):
            logger.warning("%s is running, val %s", lockpath, content)
            if FLAGS.kill_lock_pid and (FLAGS.lock_pid_expire_seconds==0 or FLAGS.lock_pid_expire_seconds < get_pid_running_seconds(pid)):
                logger.info("%s expired, pid %s runs too long, removing lock file", lockpath, content)
                os.kill(pid, 9)
                os.remove(lockpath)
            else:
                sys.exit(1)
        else:
            logger.info("%s expired, pid %s not exists, removing lock file", lockpath, content)
            os.remove(lockpath)
    try:
        try:
            f = open(lockpath, "w")
            f.write(value)
            f.close()
        except:
            logger.error("lock %s failed, %s", lockpath, traceback.format_exc())
        yield
    finally:
        print "removing"
        if FLAGS.autounlock:
            os.remove(lockpath)

@contextmanager
def check_zookeeper_lock(key, value, logger):
    zk_key = "%s/%s" % (FLAGS.zk_lockpath, key)
    zk = None
    try:
        pykeeper.install_log_stream()
        zk = pykeeper.ZooKeeper(FLAGS.zk_lockserver)
        zk.connect()

        if FLAGS.unlock:
            try:
                zk.delete(zk_key)
                logger.info('%s has been deleted', zk_key)
            except NoNodeException:
                logger.info('%s has been deleted.', zk_key)
            except:
                logger.error("Clean lock failed %s, %s", zk_key, traceback.format_exc())
            sys.exit(0)

        if zk.exists(zk_key):
            logger.warning('%s is running, val %s', key, zk.get(zk_key))
            sys.exit(1)
    except:
        logger.error("Zookeeper failed %s, %s", zk_key, traceback.format_exc())
        sys.exit(0)

    try:
        try:
            zk.create_recursive(FLAGS.zk_lockpath, '')
            zk.create(zk_key, value)
        except:
            logger.error("Zookeeper lock failed %s, %s", zk_key, traceback.format_exc())
            sys.exit(0)
        yield
    finally:
        if FLAGS.autounlock:
            zk.delete(zk_key)

@contextmanager
def check_redis_lock(key, value, logger):
    r = None
    try:
        r = Redis(host = FLAGS.redis_lockserver)

        if FLAGS.unlock:
            r.delete(key)
            logger.info('%s has been deleted' % key)
            sys.exit(0)

        if r.exists(key):
            logger.warning('%s is running' % key)
            sys.exit(1)
    except:
        logger.error("Redis failed %s, %s", key, traceback.format_exc())
        sys.exit(0)

    try:
        try:
            r.set(key, value)
        except:
            logger.error("Redis lock failed %s, %s", key, traceback.format_exc())
            sys.exit(0)
        yield
    finally:
        if FLAGS.autounlock:
            r.delete(key)

@contextmanager
def lock(key, loggername=__name__):
    logger = logging.getLogger(loggername)

    if not FLAGS.lock:
        yield
        return

    mypid = str(os.getpid())
    value = '%s:%s:%s' % (gethostname(), mypid, time.time())

    if FLAGS.usefilelock:
        with check_filelock(key, value, logger):
            yield
    elif FLAGS.usezklock:
        with check_zookeeper_lock(key, value, logger):
            yield
    elif FLAGS.useredislock:
        with check_redis_lock(key, value, logger):
            yield
    else:
        yield

if __name__ == "__main__":
    try:
        argv = FLAGS(sys.argv)[1:]  # parse flags
    except gflags.FlagsError, e:
        print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    logging.basicConfig()
    with lock("test"):
        print "Got lock, testing"

