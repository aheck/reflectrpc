from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import json
import os.path
import ssl
import sys
import socket

if sys.version_info.major == 2:
    class ConnectionRefusedError(Exception):
        pass

    class SSLEOFError(Exception):
        pass
else:
    from ssl import SSLEOFError

class NetworkError(Exception):
    """
    Encapsulates network errors to ease error handling for users
    """
    def __init__(self, real_exception):
        self.real_exception = real_exception

    def __str__(self):
        return "NetworkError: " + str(self.real_exception)

class TLSHostnameError(Exception):
    """
    Exception for when the hostname of a server does not match the hostname in the certificate
    """
    def __init__(self, hostname, cert_hostname):
        self.hostname = hostname
        self.cert_hostname = cert_hostname

    def __str__(self):
        return "TLSHostnameError: Host name '%s' doesn't match certificate host '%s'" % (self.hostname, self.cert_hostname)

class HttpException(Exception):
    pass

class RpcError(Exception):
    """
    JSON-RPC error object as received by the client
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "ERROR: " + str(self.msg)

class RpcClient(object):
    """
    Client for the JSON-RPC 1.0 protocol
    """
    def __init__(self, host, port):
        """
        Constructor

        Args:
            host (str): Hostname or IP address to connect to
            port (int): TCP port to connect to
        """
        self.req_id = 1
        self.recv_buf = ''
        self.sock = None

        # Client configuration
        self.host = host
        self.port = port

        self.timeout = 5

        self.tls_enabled = False
        self.tls_version = ssl.PROTOCOL_TLSv1
        # CA file to check server cert against
        self.ca_file = None
        # check the hostname of a TLS server against the hostname in the certificate
        self.check_hostname = False

        # do we want to authenticate with a client certificate?
        self.tls_client_auth_enabled = False
        # cert to authenticate with the server
        self.client_cert = None

        self.http_enabled = False
        self.http_path = None

    def enable_tls(self, ca_file, check_hostname=True):
        """
        Enable TLS on the connection

        Args:
            ca_file (str): Path to a CA file to validate the server certificate
        """
        self.tls_enabled = True
        self.ca_file = ca_file
        self.check_hostname = check_hostname

        if self.ca_file:
            self.__check_ca_file()

    def enable_client_auth(self, cert_file, key_file):
        """
        Enable TLS client authentication

        Args:
            cert_file (str): Path of a PEM file containing client cert
            key_file (str): Path of a PEM file containing the client key
        """
        self.tls_client_auth_enabled = True

        self.tls_client_cert = cert_file
        self.tls_client_key = key_file

    def enable_http(self, http_path='/rpc'):
        """
        Use HTTP as transport protocol

        Args:
            http_path (str): The path to the RPC HTTP resource (e.g. /rpc)
        """
        self.http_enabled = True
        self.http_path = http_path

    def is_connected(self):
        """
        Check if the client is connected to a server
        """
        if not self.sock:
            return False

        return True

    def build_rpc_call(self, method, *params):
        """
        Builds a JSON-RPC request dictionary

        Args:
            method (str): Name of the RPC method
            params (list): Parameters for the RPC method

        Returns:
            dict: Request dictionary
        """
        request = {}
        request['id'] = self.req_id
        self.req_id = self.req_id + 1
        request['method'] = method
        request['params'] = params

        return request

    def build_rpc_notify(self, method, *params):
        """
        Builds a JSON-RPC notify request dictionary

        Args:
            method (str): Name of the notify method
            params (list): Parameters for the notify method

        Returns:
            dict: Request dictionary
        """
        request = {}
        request['id'] = None
        request['method'] = method
        request['params'] = params

        return request

    def rpc_call_raw(self, json_data, send_only=False):
        """
        Send a raw JSON request to the server

        This method does not validate the input JSON. Also you have to make sure
        that if you send a request where the "id" parameter has the value "null"
        the parameter send_only must be True. Otherwise the client will block
        indefinitely because the server sees it as a notify request and does not
        send an answer.

        If we are currently not connected with the server this method will call
        __connect() to create a connection.

        Args:
            json_data (str): The JSON that is sent to the server as is
            send_only (bool): Only send the request, don't try to read a response

        Returns:
            str: The response string as returned by the server
            None: If send_only is True

        Raises:
            NetworkError: Any network error
        """
        try:
            if not self.is_connected():
                self.__connect()

            self.send_request(json_data)

            if send_only:
                return

            json_reply = self.receive_response()

            return json_reply
        except (ConnectionRefusedError, socket.error, SSLEOFError,
                TLSHostnameError) as e:
            self.close_connection()
            raise NetworkError(e)

    def send_request(self, data):
        data = data.encode('utf-8')

        if self.http_enabled:
            http_headers = [
                    'POST %s HTTP/1.1' % (self.http_path),
                    'Host: %s' % (self.host),
                    'Content-Type: application/json-rpc',
                    'Content-Length: %d' % (len(data))
            ]

            header = '\r\n'.join(http_headers) + '\r\n\r\n'
            header = header.encode('utf-8')

            self.sock.sendall(header)
            self.sock.sendall(data)
        else:
            data += '\r\n'.encode('utf-8')
            self.sock.sendall(data)

    def receive_response(self):
        if self.http_enabled:
            return self.receive_http_response()
        else:
            return self.receive_line_response()

    def receive_http_response(self):
        data = self.sock.recv(4096)

        while not b"\r\n" in data:
            if len(data >= 4096):
                raise Exception("Couldn't find a complete HTTP header within the first 4096 bytes of the server response!")

            data += self.sock.recv(4096)

        header, data = data.split(b"\r\n\r\n", 1)

        header = header.decode('utf-8')
        headerlines = header.splitlines()

        if len(headerlines) == 0:
            raise Exception("Invalid HTTP header")

        # check HTTP status line
        statusline = headerlines.pop(0)
        fields = statusline.split(' ')

        if fields[0] != 'HTTP/1.1':
            raise HttpException("Unexpected HTTP version: '%s'" % (fields[0]))

        if fields[1] != '200':
            raise HttpException("Expected status code '200' but got '%s'" % (fields[1]))

        content_length = 0
        content_type = ''
        content_encoding = 'UTF-8'

        while headerlines:
            line = headerlines.pop(0)
            fields = line.split(': ')

            if fields[0] == 'Content-Length':
                content_length = int(fields[1])

            if fields[0] == 'Content-Type':
                content_type = fields[1]

            if fields[0] == 'Content-Encoding':
                content_encoding = fields[1]

        if content_encoding != 'UTF-8':
            raise HttpException("Unsupported content encoding: '%s'" % (content_encoding))

        if content_length == 0:
            raise HttpException("Content length is 0 but expected some content")

        remaining_bytes = content_length - len(data)

        while remaining_bytes > 0:
            data += self.sock.recv(remaining_bytes)
            remaining_bytes = content_length - len(data)

        return data.decode('utf-8')

    def receive_line_response(self):
        data = self.sock.recv(4096)
        self.recv_buf += data.decode('utf-8')

        if not self.recv_buf.strip().startswith('{'):
            self.close_connection()
            raise NetworkError("Non-JSON content received")

        while not "\n" in self.recv_buf:
            data = self.sock.recv(4096)
            self.recv_buf += data.decode('utf-8')

        response = self.recv_buf
        self.recv_buf = ''

        return response

    def rpc_call(self, method, *params):
        """
        Call a RPC function on the server

        This function returns the server response or raises an error

        Args:
            method (str): The name of the RPC method to call on the server
            params (list): The parameters to pass to the RPC method

        Returns:
            JSON type: The value returned by the server

        Raises:
            RpcError: Generic exception to encapsulate all errors
        """
        json_data = json.dumps(self.build_rpc_call(method, *params))

        json_reply = self.rpc_call_raw(json_data)

        reply = json.loads(json_reply)

        if 'error' in reply and reply['error']:
            raise RpcError(reply['error'])

        return reply['result']

    def rpc_notify(self, method, *params):
        """
        Call a RPC function on the server but tell it to send no response

        Args:
            method (str): The name of the RPC method to call on the server
            params (list): The parameters to pass to the RPC method
        """

        json_data = json.dumps(self.build_rpc_call(method, *params))
        self.rpc_call_raw(json_data, True)

    def close_connection(self):
        """
        Force the connection to be closed
        """
        try:
            self.sock.close()
        except:
            pass

        self.sock = None

    def __check_host_cert(self, sock):
        """
        Check if the hostname of our server matches with the server cert
        """
        cert = sock.getpeercert()
        for field in cert['subject']:
            if field[0][0] != 'commonName':
                continue

            certhost = field[0][1]
            if certhost != self.host:
                self.close_connection()
                raise TLSHostnameError(self.host, certhost)

    def __connect(self):
        """
        Connect to the server

        Raises:
            socket.error: If connection attempt fails
            TLSHostnameError: If server hostname validation failed
        """
        self.sock = None

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        sock.connect((self.host, self.port))

        if self.tls_enabled:
            if self.ca_file:
                self.__check_ca_file()

                if self.tls_client_auth_enabled:
                    sock = ssl.wrap_socket(sock,
                            ssl_version=self.tls_version,
                            cert_reqs=ssl.CERT_REQUIRED,
                            certfile=self.tls_client_cert,
                            keyfile=self.tls_client_key,
                            ca_certs=self.ca_file
                    )
                else:
                    sock = ssl.wrap_socket(sock,
                            ssl_version=self.tls_version,
                            cert_reqs=ssl.CERT_REQUIRED,
                            ca_certs=self.ca_file
                    )

                if self.check_hostname:
                    self.__check_host_cert(sock)
            else:
                sock = ssl.wrap_socket(sock, ssl_version=self.tls_version)

        self.sock = sock

    def __check_ca_file(self):
        # check if ca_file exists and can be read to omit ugly and
        # confusing OpenSSL error
        with open(self.ca_file) as f:
            pass
