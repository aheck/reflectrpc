#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import errno
import sys
import json
import os
import unittest
import time

sys.path.append('..')

from reflectrpc.client import RpcClient
from reflectrpc.client import RpcError
from reflectrpc.client import NetworkError
from reflectrpc.client import HttpException
from reflectrpc.testing import FakeServer

class ClientTests(unittest.TestCase):
    def test_client_simple(self):
        server = FakeServer('localhost', 5500)
        server.add_reply('{"error": null, "result": "Hello Server", "id": 1}')
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            result = client.rpc_call('echo', 'Hello Server')
            server.stop()
            request = server.requests.pop()

            expected = {'method': 'echo', 'params': ['Hello Server'], 'id': 1}
            self.assertEqual(json.loads(request), expected)
            self.assertEqual(result, 'Hello Server')
        finally:
            client.close_connection()

    def test_client_http_invalid_answer(self):
        server = FakeServer('localhost', 5500)
        server.add_reply('{"error": null, "result": "Hello Server", "id": 1}')
        server.run()

        client = RpcClient('localhost', 5500)
        client.enable_http()

        try:
            with self.assertRaises(HttpException) as cm:
                client.rpc_call('echo', 'Hello Server')

            self.assertEqual(str(cm.exception), "Received invalid HTTP response: Couldn't find a HTTP header")
            server.stop()
        finally:
            client.close_connection()


if __name__ == '__main__':
    unittest.main()
