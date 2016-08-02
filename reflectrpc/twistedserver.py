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
from twisted.internet.defer import Deferred
from twisted.protocols.basic import LineReceiver
from twisted.web.server import NOT_DONE_YET

import reflectrpc.server

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

class JsonRpcProtocol(LineReceiver):
    """
    Twisted protocol adapter
    """
    def __init__(self):
        self.rpcinfo = None
        self.initialized = False

            #self.server = JsonRpcServer(self.factory.rpcprocessor,
            #        self.transport, rpcinfo)

    def lineReceived(self, line):
        if not self.initialized:
            self.initialized = True
            if self.factory.tls_client_auth_enabled:
                self.username = self.transport.getPeerCertificate().get_subject().commonName
                self.rpcinfo = {}
                self.rpcinfo['authenticated'] = True
                self.rpcinfo['username'] = self.username

        rpcprocessor = self.factory.rpcprocessor
        reply = rpcprocessor.process_request(line.decode('utf-8'), self.rpcinfo)

        if isinstance(reply['result'], Deferred):
            def handler(value):
                reply['result'] = value
                self.sendLine(json.dumps(reply).encode('utf-8'))

            def error_handler(error):
                r = rpcprocessor.handle_error(error.value, reply)
                self.sendLine(json.dumps(r).encode('utf-8'))

            d = reply['result']
            d.addCallback(handler)
            d.addErrback(error_handler)
        else:
            self.sendLine(json.dumps(reply).encode('utf-8'))

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
        reply = self.rpcprocessor.process_request(data, rpcinfo)
        request.setHeader(b"Content-Type", b"application/json-rpc")

        if isinstance(reply['result'], Deferred):
            def delayed_render(value):
                reply['result'] = value

                data = json.dumps(reply).encode('utf-8')
                header_value = str(len(data)).encode('utf-8')
                request.setHeader(b"Content-Length", header_value)
                request.write(data)
                request.finish()

            def error_handler(error):
                r = self.rpcprocessor.handle_error(error.value, reply)

                data = json.dumps(r).encode('utf-8')
                header_value = str(len(data)).encode('utf-8')
                request.setHeader(b"Content-Length", header_value)
                request.write(data)
                request.finish()

            d = reply['result']
            d.addCallback(delayed_render)
            d.addErrback(error_handler)

            return NOT_DONE_YET

        data = json.dumps(reply).encode('utf-8')
        header_value = str(len(data)).encode('utf-8')
        request.setHeader(b"Content-Length", header_value)
        return data

class TwistedJsonRpcServer(object):
    """
    JSON-RPC server for line-terminated messages based on Twisted
    """
    def __init__(self, rpcprocessor, host, port):
        """
        Constructor

        Args:
            rpcprocessor (RpcProcessor): RPC implementation
            host (str): Hostname, IP or UNIX domain socket to listen on. A UNIX
                        Domain Socket might look like this: unix:///tmp/my.sock
            port (int): TCP port to listen on (if host is a UNIX Domain Socket
                        this value is ignored)
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

        self.unix_socket_backlog = 50
        self.unix_socket_mode = 438
        self.unix_socket_want_pid = False

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

    def set_unix_socket_backlog(self, backlog):
        """
        Sets the number of client connections accepted in case we listen on a
        UNIX Domain Socket

        Args:
            backlog (int): Number of client connections allowed
        """
        self.unix_socket_backlog = backlog

    def set_unix_socket_mode(self, mode):
        """
        Sets the file permission mode used in case we listen on a UNIX Domain
        Socket

        Args:
            mode (int): UNIX file permission mode to protect the Domain Socket
        """
        self.unix_socket_mode = mode

    def enable_unix_socket_want_pid(self):
        """
        Enable the creation of a PID file in case you listen on a UNIX Domain
        Socket
        """
        self.unix_socket_want_pid = True

    def run(self):
        """
        Start the server and listen on host:port
        """
        f = None
        unix_prefix = 'unix://'

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
            if self.host.startswith(unix_prefix):
                path = self.host[len(unix_prefix):]
                reactor.listenUNIX(path, f, backlog=self.unix_socket_backlog,
                        mode=self.unix_socket_mode, wantPID=self.unix_socket_want_pid)
            else:
                reactor.listenTCP(self.port, f, interface=self.host)

        if self.host.startswith(unix_prefix):
            print("Listening on %s" % (self.host))
        else:
            print("Listening on %s:%d" % (self.host, self.port))

        reactor.run()
