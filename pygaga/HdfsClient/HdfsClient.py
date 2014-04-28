import sys
#sys.path.append("./gen-py")

from random import shuffle
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from pygaga.HdfsClient.hadoopfs import ThriftHadoopFileSystem
from pygaga.HdfsClient.hadoopfs.ttypes import *

def connect(hosts):
    hostPorts = hosts.split(',')
    shuffle(hostPorts)
    for hostPort in hostPorts:
        host, port = hostPort.split(':')
        cli, tp = _connect(host, port)
        if cli and tp:
            return cli, tp
    return None, None

def _connect(host, port):
    try:
        transport = TSocket.TSocket(host, port)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)

        client = ThriftHadoopFileSystem.Client(protocol)
        transport.open()

        client.setInactivityTimeoutPeriod(60*60)

        print 'successful connected to ', host, port
        return client, transport
    except Exception, e:
        print "ERROR in connecting to ", host, port
        print '%s' % (e)
        return None, None

def close(transport):
    transport.close()

if __name__ == '__main__':
    cli, t = connect('varnish3:12312,localhost:55290')
    if cli:
        close(t)

