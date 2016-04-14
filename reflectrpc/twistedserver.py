from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import os
import sys
import json

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, ssl
from twisted.python import log

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

        self.tls_enabled = False
        self.tls_client_auth_enabled = False
        self.cert = None
        self.client_auth_ca = None

    def enable_tls(self, pem_file):
        """
        Enable TLS authentication and encryption for this server

        Args:
            pem_file (str): Path of a PEM file containing server cert and key
        """
        self.tls_enabled = True

        with open(pem_file) as f: pem_data = f.read()
        self.cert = ssl.PrivateCertificate.loadPEM(pem_data)

    def enable_client_auth(self, ca_file):
        """
        Enable TLS client authentication

        The client needs to present a certificate that validates against our CA
        to be authenticated

        Args:
            ca_file (str): Path of a PEM file containing a CA cert to validate the client certs against
        """
        self.tls_client_auth_enabled = True

        with open(ca_file) as f: ca_data = f.read()
        self.client_auth_ca = ssl.Certificate.loadPEM(ca_data)

    def run(self):
        """
        Start the server and listen on host:port
        """
        f = JsonRpcProtocolFactory(self.jsonrpc)
        if self.tls_enabled:
            if not self.tls_client_auth_enabled:
                reactor.listenSSL(self.port, f, self.cert.options(),
                        interface=self.host)
            else:
                reactor.listenSSL(self.port, f,
                        self.cert.options(self.client_auth_ca),
                        interface=self.host)
        else:
            reactor.listenTCP(self.port, f, interface=self.host)

        reactor.run()
