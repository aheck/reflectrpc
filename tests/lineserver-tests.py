#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import json
import sys
import unittest

sys.path.append('..')

from reflectrpc import RpcProcessor
from reflectrpc import RpcFunction
from reflectrpc.server import AbstractJsonRpcServer

def echo(msg):
    return msg

class DummyServer(AbstractJsonRpcServer):
    def send_data(self, data):
        if not hasattr(self, 'responses'):
            self.responses = []

        self.responses.append(data)

class LineServerTests(unittest.TestCase):
    def test_invalid_json(self):
        rpc = RpcProcessor()

        echo_func = RpcFunction(echo, 'echo', 'Returns what it was given',
                'string', 'Same value as the first parameter')
        echo_func.add_param('string', 'message', 'Message to send back')

        rpc.add_function(echo_func)
        server = DummyServer(rpc, None)

        # data with linebreak gets processed immediatelly
        server.data_received(b"data\r\n")
        self.assertEqual(1, len(server.responses))

        # without linebreak it doesn't get processed
        server.data_received(b"data")
        server.data_received(b"data")
        server.data_received(b"data")
        self.assertEqual(1, len(server.responses))

        # once the linebreak arrives data gets processed again
        server.data_received(b"\r\n")
        self.assertEqual(2, len(server.responses))

    def test_json_messages(self):
        rpc = RpcProcessor()

        echo_func = RpcFunction(echo, 'echo', 'Returns what it was given',
                'string', 'Same value as the first parameter')
        echo_func.add_param('string', 'message', 'Message to send back')

        rpc.add_function(echo_func)
        server = DummyServer(rpc, None)

        # JSON-RPC call with linebreak gets processed immediatelly
        server.data_received(b'{"method": "echo", "params": ["Hello Server"], "id": 1}\r\n')
        self.assertEqual(1, len(server.responses))
        msgstr = server.responses[0].decode("utf-8")
        msg = json.loads(msgstr)
        self.assertEqual({"result": "Hello Server", "error": None, "id": 1}, msg)

        # if JSON is received in chunks the request must be processed after the linebreak
        server.data_received(b'{"method":')
        server.data_received(b' "echo", "params": ["Hello')
        server.data_received(b' Server"], "id": 2}\r\n{"method": "echo",')
        self.assertEqual(2, len(server.responses))
        msgstr = server.responses[1].decode("utf-8")
        msg = json.loads(msgstr)
        self.assertEqual({"result": "Hello Server", "error": None, "id": 2}, msg)

        # completing the next message should work too
        server.data_received(b' "params": ["Hello Echo"], "id": 3}\r\n')
        self.assertEqual(3, len(server.responses))
        msgstr = server.responses[2].decode("utf-8")
        msg = json.loads(msgstr)
        self.assertEqual({"result": "Hello Echo", "error": None, "id": 3}, msg)

if __name__ == '__main__':
    unittest.main()
