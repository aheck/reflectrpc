import os
import sys
import json

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

class JsonRpcProtocol(Protocol):
    def __init__(self):
        self.buf = ''

    def dataReceived(self, data):
        self.buf += data.decode()

        count = self.buf.count("\n")
        if count > 0:
            lines = self.buf.splitlines()

            for i in range(count):
                line = lines.pop(0)
                reply_line = json.dumps(self.factory.jsonrpc.process_request(line)) + "\r\n"
                self.transport.write(reply_line.encode("utf-8"))

            self.buf = ''
            if lines:
                self.buf = lines[0]

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
