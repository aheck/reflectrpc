from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import json

from abc import ABCMeta, abstractmethod

class AbstractJsonRpcServer(object):
    """
    Abstract base class for line based JSON-RPC servers
    """
    __metaclass__=ABCMeta

    def __init__(self, rpcprocessor, conn):
        """
        Constructor

        Args:
            rpcprocessor (RpcProcessor): RpcProcessor with the RPCs to be served
            conn (any): An abstract connection object to be used in the user
                        implemented send_data method
        """
        self.buf = ''
        self.rpcprocessor = rpcprocessor
        self.conn = conn

    def data_received(self, data):
        self.buf += data.decode('utf-8')

        count = self.buf.count("\n")
        if count > 0:
            lines = self.buf.splitlines()

            for i in range(count):
                line = lines.pop(0)
                reply = self.rpcprocessor.process_request(line)

                # in case of a notification request process_request returns None
                # and we send no reply back
                if reply:
                    reply_line = json.dumps(reply) + "\r\n"
                    self.send_data(reply_line.encode("utf-8"))

            self.buf = ''
            if lines:
                self.buf = lines[0]

    """
    Abstract method you must override to send a reply back to the client
    """
    @abstractmethod
    def send_data(self, data):
        pass
