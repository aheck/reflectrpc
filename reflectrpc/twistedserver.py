from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import os
import sys
import json

from zope.interface import implementer
from twisted.internet import defer
from twisted.web.guard import HTTPAuthSessionWrapper
from twisted.web.guard import BasicCredentialFactory
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.web.resource import IResource
from twisted.web.resource import NoResource
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

class PasswordChecker(object):
    credentialInterfaces = (credentials.IUsernamePassword,)
    @implementer(checkers.ICredentialsChecker)

    def __init__(self, check_function):
        """
        Constructor

        Args:
            check_function (callable): A callable that checks a username and a
                                       password
        """
        self.check_function = check_function

    def requestAvatarId(self, credentials):
        username = credentials.username
        password = credentials.password

        if type(username) == bytes:
            username = username.decode('utf-8')

        if type(password) == bytes:
            password = password.decode('utf-8')

        if self.check_function(username, password):
            return defer.succeed(username)
        else:
            return defer.fail(credError.UnauthorizedLogin("Login failed"))

class HttpPasswordRealm(object):
    @implementer(portal.IRealm)

    def __init__(self, resource):
        self.resource = resource

    def requestAvatar(self, credentials, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, self.resource, lambda: None)
        raise NotImplementedError()

class JsonRpcProtocol(Protocol):
    """
    Twisted protocol adapter
    """
    def __init__(self):
        self.buf = ''

    def dataReceived(self, data):
        if not hasattr(self, 'server'):
            rpcinfo = None

            if self.factory.tls_client_auth_enabled:
                self.username = self.transport.getPeerCertificate().get_subject().commonName
                rpcinfo = {}
                rpcinfo['authenticated'] = True
                rpcinfo['username'] = self.username

            self.server = JsonRpcServer(self.factory.rpcprocessor,
                    self.transport, rpcinfo)

        self.server.data_received(data)

class JsonRpcProtocolFactory(Factory):
    """
    Factory to create JsonRpcProtocol objects
    """
    protocol = JsonRpcProtocol

    def __init__(self, rpcprocessor, tls_client_auth_enabled):
        self.rpcprocessor = rpcprocessor
        self.tls_client_auth_enabled = tls_client_auth_enabled

class RootResource(resource.Resource):
    def __init__(self, rpc):
        resource.Resource.__init__(self)
        self.rpc = rpc

    def getChild(self, name, request):
        if name == b'rpc':
            return self.rpc
        else:
            return NoResource()

class JsonRpcHttpResource(resource.Resource):
    isLeaf = True

    def __init__(self):
        resource.Resource.__init__(self)

    def render_POST(self, request):
        rpcinfo = None

        if self.tls_client_auth_enabled:
            self.username = request.transport.getPeerCertificate().get_subject().commonName
            rpcinfo = {}
            rpcinfo['authenticated'] = True
            rpcinfo['username'] = self.username
        elif request.getUser():
            rpcinfo = {}
            rpcinfo['authenticated'] = True
            rpcinfo['username'] = request.getUser().decode('utf-8')

        data = request.content.getvalue().decode('utf-8')
        reply = json.dumps(self.rpcprocessor.process_request(data, rpcinfo))
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
        self.http_basic_auth_enabled = False
        self.passwdCheckFunction = None

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

    def enable_http_basic_auth(self, passwdCheckFunction):
        """
        Enables HTTP Basic Auth

        Args:
            passwdCheckFunction (callable): Takes a username and a password as
                                            argument and checks if they are
                                            valid
        """
        self.http_basic_auth_enabled = True
        self.passwdCheckFunction = passwdCheckFunction

    def run(self):
        """
        Start the server and listen on host:port
        """
        f = None

        if self.http_enabled:
            rpc = JsonRpcHttpResource()
            rpc.rpcprocessor = self.rpcprocessor
            rpc.tls_client_auth_enabled = self.tls_client_auth_enabled

            if self.http_basic_auth_enabled:
                checker = PasswordChecker(self.passwdCheckFunction)
                realm = HttpPasswordRealm(rpc)
                p = portal.Portal(realm, [checker])

                realm_name = 'Reflect RPC'

                if sys.version_info.major == 2:
                    realm_name = realm_name.encode('utf-8')

                credentialFactory = BasicCredentialFactory(realm_name)
                rpc = HTTPAuthSessionWrapper(p, [credentialFactory])

            root = RootResource(rpc)

            f = server.Site(root)
        else:
            f = JsonRpcProtocolFactory(self.rpcprocessor,
                    self.tls_client_auth_enabled)

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
