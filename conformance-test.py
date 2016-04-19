#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import argparse
import json
import sys
import unittest

from reflectrpc.client import RpcClient
from reflectrpc.testing import ServerRunner

server_program = None

class ConformanceTest(unittest.TestCase):
    # Table driven conformance test that can also be run against
    # implementations in other programming languages
    def test_conformance(self):
        global server_program

        tests = [
                ['{"method": "echo", "params": ["Hello Server"], "id": 1}',
                 '{"result": "Hello Server", "error": null, "id": 1}']
        ]

        server = ServerRunner(server_program, 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            for test in tests:
                request = test[0]
                expected_result = json.loads(test[1])

                result_str = client.rpc_call_raw(request)
                result_dict = json.loads(result_str)
                self.assertEqual(result_dict, expected_result)
        finally:
            server.stop()


parser = argparse.ArgumentParser(
        description="ReflectRPC conformance test to run against a server program that listens on localhost:5500")

parser.add_argument("server_program", metavar='SERVER', type=str,
        help="Server program to run the test against")

args = parser.parse_args()
server_program = args.server_program

# reset argv so unittest.main() does not try to interpret our arguments
sys.argv = [sys.argv[0]]

if __name__ == '__main__':
    unittest.main()
