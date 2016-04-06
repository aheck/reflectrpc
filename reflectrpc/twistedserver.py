import os
import sys
import json

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

import reflectrpc.server

class JsonRpcServer(reflectrpc.server.AbstractJsonRpcServer):
    """
    Twisted implementation of AbstractJsonRpcServer
    """
    def send_data(self, data):
        self.conn.write(data)

class JsonRpcProtocol(Protocol):
    """
    Twisted protocol adapter
    """
    def __init__(self):
        self.buf = ''

    def dataReceived(self, data):
        if not hasattr(self, 'server'):
            self.server = JsonRpcServer(self.factory.jsonrpc, self.transport)

        self.server.data_received(data)

class JsonRpcProtocolFactory(Factory):
    """
    Factory to create JsonRpcProtocol objects
    """
    protocol = JsonRpcProtocol

    def __init__(self, rpcprocessor):
        self.jsonrpc = rpcprocessor

class TwistedJsonRpcServer(object):
    """
    JSON-RPC server for line-terminated messages based on Twisted
    """
    def __init__(self, rpcprocessor, host, port):
        """
        Constructor

        Args:
            rpcprocessor (RpcProcessor): RPC implementation
            host (str): Hostname or IP to listen on
            port (int): TCP port to listen on
        """
        self.host = host
        self.port = port
        self.jsonrpc = rpcprocessor

    def run(self):
        """
        Start the server and listen on host:port
        """
        f = JsonRpcProtocolFactory(self.jsonrpc)
        reactor.listenTCP(self.port, f, interface=self.host)
        reactor.run()
