from __future__ import print_function

import os
import sys
import json
import socket

class SimpleJsonRpcServer(object):
    """
    Simple JSON-RPC server

    Not a production quality server, handles only one connection at a time.
    """
    def __init__(self, processor, host, port):
        self.jsonrpc = processor
        self.host = host
        self.port = port

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind((self.host, self.port))
        except OSError as e:
            print("ERROR: " + e.strerror, file=sys.stderr)
            sys.exit(1)

        self.socket.listen(10)

        while 1:
            conn, addr = self.socket.accept()
            self.handle_connection(conn)

    def handle_connection(self, conn):
        buf = ''
        data = conn.recv(4096)

        while data:
            buf += data.decode("utf-8")
            count = buf.count("\n")
            if count > 0:
                lines = buf.splitlines()

                for i in range(count):
                    line = lines.pop(0)
                    reply_line = json.dumps(self.jsonrpc.process_request(line)) + "\n"
                    conn.sendall(reply_line.encode("utf-8"))

                buf = ''
                if lines:
                    buf = lines[0]

            data = conn.recv(4096)
