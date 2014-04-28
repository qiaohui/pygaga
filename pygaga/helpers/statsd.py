
import logging
import random
import time
import traceback
from socket import socket, AF_INET, SOCK_DGRAM

import gflags

FLAGS = gflags.FLAGS

gflags.DEFINE_string('statshost', "127.0.0.1", "stats host")
gflags.DEFINE_integer('statsport', 8125, "stats port")

logger = logging.getLogger('StatsLogger')

class Statsd(object):
    @staticmethod
    def sets(stat, s, host=None, port=0):
        """
        Log timing information
        >>> Statsd.sets('some.sets', 500)
        """
        stats = {}
        stats[stat] = "%d|s" % s
        Statsd.send(stats, host = host, port = port)

    @staticmethod
    def gauges(stat, g, host=None, port=0):
        """
        Log timing information
        >>> Statsd.gauges('some.sets', 500)
        """
        stats = {}
        stats[stat] = "%d|g" % g
        Statsd.send(stats, host = host, port = port)

    @staticmethod
    def timing(stat, time, sample_rate=1, host=None, port=0):
        """
        Log timing information
        >>> Statsd.timing('some.time', 500)
        """
        stats = {}
        stats[stat] = "%d|ms" % time
        Statsd.send(stats, sample_rate, host = host, port = port)

    @staticmethod
    def increment(stats, sample_rate=1, host=None, port=0):
        """
        Increments one or more stats counters
        >>> Statsd.increment('some.int')
        >>> Statsd.increment('some.int',0.5)
        """
        Statsd.update_stats(stats, 1, sample_rate, host = host, port = port)

    @staticmethod
    def decrement(stats, sample_rate=1, host=None, port=0):
        """
        Decrements one or more stats counters
        >>> Statsd.decrement('some.int')
        """
        Statsd.update_stats(stats, -1, sample_rate, host = host, port = port)

    @staticmethod
    def update_stats(stats, delta=1, sampleRate=1, host=None, port=0):
        """
        Updates one or more stats counters by arbitrary amounts
        >>> Statsd.update_stats('some.int',10)
        """
        if (type(stats) is not list):
            stats = [stats]
        data = {}
        for stat in stats:
            data[stat] = "%s|c" % delta

        Statsd.send(data, sampleRate, host = host, port = port)

    @staticmethod
    def send(data, sample_rate=1, host=None, port=0):
        """
        Squirt the metrics over UDP
        """
        addr=(host or FLAGS.statshost, port or FLAGS.statsport)

        sampled_data = {}

        if(sample_rate < 1):
            if random.random() <= sample_rate:
                for stat in data.keys():
                    value = data[stat]
                    sampled_data[stat] = "%s|@%s" %(value, sample_rate)
        else:
            sampled_data=data

        udp_sock = socket(AF_INET, SOCK_DGRAM)
        try:
            for stat in sampled_data.keys():
                value = sampled_data[stat]
                send_data = "%s:%s" % (stat, value)
                udp_sock.sendto(send_data, addr)
        except:
            logger.warn("Send stats error: %s", traceback.format_exc())

def statsd_timing(name, host=None, port=0):

    def deco_func(f):

        def wrapper(*args):
            t = time.time()
            result = f(*args)
            spent = time.time() - t
            Statsd.timing(name, spent*1000, host=host or FLAGS.statshost, port=port or FLAGS.statsport)
            return result

        return wrapper

    return deco_func

if __name__=="__main__":
    Statsd.increment('test.guang')
    class Test:
        @statsd_timing("test.call")
        def test(self, a):
            self.x = a
    t = Test()
    t.test(1)
