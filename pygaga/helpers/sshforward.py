
import SocketServer
import ssh
import socket
import select
import logging
import time
import os
import sys

logger = logging.getLogger('sshforward')

class ForwardServer (SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

class Handler (SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.client.get_transport().open_channel('direct-tcpip',
                                                   (self.chain_host, self.chain_port),
                                                   self.request.getpeername())
        except Exception, e:
            logger.warn('Incoming request to %s:%d failed: %s, retry', self.chain_host,
                                                              self.chain_port,
                                                              repr(e))
            time.sleep(1)
            self.connect_server()
        if chan is None:
            logger.warn('Incoming request to %s:%d was rejected by the SSH server.',
                    self.chain_host, self.chain_port)
            return

        logger.info('Connected!  Tunnel open %r -> %r -> %r', self.request.getpeername(),
                    chan.getpeername(), (self.chain_host, self.chain_port))
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)
        chan.close()
        logger.info('Tunnel closed from %r', self.request.getpeername())
        self.request.close()

def forward_tunnel(local_port, remote_host, remote_port, server_host, server_port, username, keyfile, password, look_for_keys):
    # this is a little convoluted, but lets me configure things for the Handler
    # object.  (SocketServer doesn't give Handlers any way to access the outer
    # server normally.)
    class SubHander (Handler):
        chain_host = remote_host
        chain_port = remote_port
        s_host = server_host
        s_port = server_port
        uname = username
        kfile = keyfile
        passwd = password
        is_look_for_keys = look_for_keys

        client = ssh.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(ssh.WarningPolicy())
        client.connect(server_host, server_port, username=username, key_filename=keyfile, look_for_keys=look_for_keys, password=password)

        def connect_server(self):
            logger.info('Connecting to ssh host %s:%d ...', self.s_host, self.s_port)
            try:
                self.client.connect(self.s_host, self.s_port, username=self.uname,
                        key_filename=self.kfile, look_for_keys=self.is_look_for_keys, password=self.passwd)
            except Exception, e:
                logger.error('*** Failed to connect to %s:%d: %r, wait and retry', self.s_host, self.s_port, e)

    logger.info('Now forwarding port %d to %s:%d ...', local_port, remote_host, remote_port)
    ForwardServer(('', local_port), SubHander).serve_forever()

def connect_forward(server_host, local_port, remote_host, remote_port, username, server_port=22, keyfile=None, password=None, look_for_keys=True):
    try:
        forward_tunnel(local_port, remote_host, remote_port, server_host, server_port, username, keyfile, password, look_for_keys)
    except KeyboardInterrupt:
        return

if __name__ ==  "__main__":
    import gflags
    from pygaga.helpers.logger import log_init
    FLAGS = gflags.FLAGS

    gflags.DEFINE_integer('lport', 3306, "local port")
    gflags.DEFINE_integer('rport', 3306, "remote port")
    gflags.DEFINE_string('rhost', '192.168.10.42', "remote host")
    gflags.DEFINE_string('shost', 'log.j.cn', "server host")
    gflags.DEFINE_integer('sport', 22, "server port")
    gflags.DEFINE_string('user', 'chuansheng.song', "server username")

    FLAGS.stderr = True
    FLAGS.verbose = "info"
    FLAGS.color = True
    log_init("sshforward", "sqlalchemy.*")
    connect_forward(FLAGS.shost, FLAGS.lport, FLAGS.rhost, FLAGS.rport, FLAGS.user, FLAGS.sport)

