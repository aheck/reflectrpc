import json

from abc import ABCMeta, abstractmethod

class AbstractJsonRpcServer(metaclass=ABCMeta):
    """
    Abstract base class for line based JSON-RPC servers
    """
    def __init__(self, jsonrpc, conn):
        self.buf = ''
        self.jsonrpc = jsonrpc
        self.conn = conn

    def data_received(self, data):
        self.buf += data.decode('utf-8')

        count = self.buf.count("\n")
        if count > 0:
            lines = self.buf.splitlines()

            for i in range(count):
                line = lines.pop(0)
                reply_line = json.dumps(self.jsonrpc.process_request(line)) + "\r\n"
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
