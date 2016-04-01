import os
import sys
import json

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

import reflectrpc.server

class JsonRpcServer(reflectrpc.server.AbstractJsonRpcServer):
    def send_data(self, data):
        self.conn.write(data)

class JsonRpcProtocol(Protocol):
    def __init__(self):
        self.buf = ''

    def dataReceived(self, data):
        if not hasattr(self, 'server'):
            self.server = JsonRpcServer(self.factory.jsonrpc, self.transport)

        self.server.data_received(data)

class JsonRpcProtocolFactory(Factory):
    protocol = JsonRpcProtocol

    def __init__(self, rpcprocessor):
        self.jsonrpc = rpcprocessor

class TwistedJsonRpcServer(object):
    def __init__(self, rpcprocessor, host, port):
        self.host = host
        self.port = port
        self.jsonrpc = rpcprocessor

    def run(self):
        f = JsonRpcProtocolFactory(self.jsonrpc)
        reactor.listenTCP(self.port, f, interface=self.host)
        reactor.run()
