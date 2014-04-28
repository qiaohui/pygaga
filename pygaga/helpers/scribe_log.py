
import socket

from scribe import scribe

from thrift.transport import TTransport, TSocket, THttpClient
from thrift.transport.TTransport import TTransportException

from thrift.protocol import TBinaryProtocol

class ScribeLogError(Exception): pass
class ScribeTransportError(Exception): pass
class ScribeHandlerBufferError(Exception): pass

FRAMED = 1
UNFRAMED = 2
HTTP = 3

class Scribe:
    def __init__(self, host='127.0.0.1', port=1463,
                 category=None, transport=FRAMED, uri=None):

        if category is None:
            self.category = '%(hostname)s-%(loggername)s'
        else:
            self.category = category

        if transport is None:
            self.transport = None
            self.client = None
            return

        if transport == HTTP:
            if uri is None:
                raise ScribeLogError('http transport with no uri')
            self.transport = THttpClient.THttpClient(host, port, uri)
        else:
            socket = TSocket.TSocket(host=host, port=port)

            if transport == FRAMED:
                self.transport = TTransport.TFramedTransport(socket)
            elif transport == UNFRAMED:
                self.transport = TTransport.TBufferedTransport(socket)
            else:
                raise ScribeLogError('Unsupported transport type')

        #self._make_client()

    def _make_client(self):

        protocol = TBinaryProtocol.TBinaryProtocol(trans=self.transport,
                                                   strictRead=False, strictWrite=False)
        self.client = scribe.Client(protocol)

    def __setattr__(self, var, val):
        ## Filterer is an old style class through at least 3.1
        self.__dict__[var] = val

        if var == 'transport':
            self._make_client()

    def emit(self, msg):
        if not msg.startswith('\n') or msg.endswith('\n'):
            msg += '\n'

        if (self.client is None) or (self.transport is None):
            raise ScribeTransportError('No transport defined')

        log_entry = scribe.LogEntry(category=self.category, message=msg)

        try:
            self.transport.open()

            result = self.client.Log(messages=[log_entry,])
            if result != scribe.ResultCode.OK:
                raise ScribeLogError(result)

            self.transport.close()

        except TTransportException:
            raise

def scribe_log(message, category='default', host='127.0.0.1', port=1463):
    s = Scribe(host=host, port=port, category=category)
    s.emit(message)


if __name__ == "__main__":
    import gflags
    from pygaga.helpers.logger import log_init

    FLAGS = gflags.FLAGS

    gflags.DEFINE_string("cate", 'test', 'category name', short_name='c')
    gflags.DEFINE_string("msg", '', 'message', short_name='m')
    gflags.DEFINE_string("host", '127.0.0.1', 'host name', short_name='h')
    gflags.DEFINE_integer("port", 1463, 'port', short_name='p')

    log_init()
    scribe_log(FLAGS.msg, FLAGS.cate, FLAGS.host, FLAGS.port)
