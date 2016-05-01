from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import os
import sys
import json
import socket

import reflectrpc.server

if sys.version_info.major == 2:
    class ConnectionResetError(Exception):
        pass

class JsonRpcServer(reflectrpc.server.AbstractJsonRpcServer):
    """
    Blocking socket implementation of AbstractJsonRpcServer
    """
    def send_data(self, data):
        self.conn.sendall(data)

class SimpleJsonRpcServer(object):
    """
    Simple JSON-RPC server for line-terminated messages

    Not a production quality server, handles only one connection at a time.
    """
    def __init__(self, rpcprocessor, host, port):
        """
        Constructor

        Args:
            rpcprocessor (RpcProcessor): RPC implementation
            host (str): Hostname or IP to listen on
            port (int): TCP port to listen on
        """
        self.rpcprocessor = rpcprocessor
        self.host = host
        self.port = port

    def run(self):
        """
        Start the server and listen on host:port
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind((self.host, self.port))
        except OSError as e:
            print("ERROR: " + e.strerror, file=sys.stderr)
            sys.exit(1)

        self.socket.listen(10)
        print("Listening on %s:%d" % (self.host, self.port))

        while 1:
            conn, addr = self.socket.accept()
            self.server = JsonRpcServer(self.rpcprocessor, conn)

            try:
                self.__handle_connection(conn)
            except ConnectionResetError:
                pass

    def __handle_connection(self, conn):
        """
        Serve a single client connection
        """
        data = conn.recv(4096)

        while data:
            self.server.data_received(data)
            data = conn.recv(4096)
