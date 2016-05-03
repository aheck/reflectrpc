from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import os
import sys
import json

from twisted.web import server, resource
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
            self.server = JsonRpcServer(self.factory.rpcprocessor, self.transport)

        self.server.data_received(data)

class JsonRpcProtocolFactory(Factory):
    """
    Factory to create JsonRpcProtocol objects
    """
    protocol = JsonRpcProtocol

    def __init__(self, rpcprocessor):
        self.rpcprocessor = rpcprocessor

class JsonRpcHttpResource(resource.Resource):
    isLeaf = True
    def render_POST(self, request):
        data = request.content.getvalue().decode('utf-8')
        reply = json.dumps(self.rpcprocessor.process_request(data))
        request.setHeader(b"Content-Type", b"application/json-rpc")

        return reply.encode('utf-8')

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
        self.rpcprocessor = rpcprocessor

        self.tls_enabled = False
        self.tls_client_auth_enabled = False
        self.cert = None
        self.client_auth_ca = None
        self.http_enabled = False

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

    def enable_http(self):
        """
        Enables HTTP as transport protocol

        JSON-RPC requests are to be sent to '/rpc' as HTTP POST requests with
        content type 'application/json-rpc'. The server sends the reply in
        the response body.
        """
        self.http_enabled = True

    def run(self):
        """
        Start the server and listen on host:port
        """
        f = None

        if self.http_enabled:
            root = JsonRpcHttpResource()
            root.putChild('rpc', root)
            root.rpcprocessor = self.rpcprocessor
            f = server.Site(root)
        else:
            f = JsonRpcProtocolFactory(self.rpcprocessor)

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

        print("Listening on %s:%d" % (self.host, self.port))

        reactor.run()
