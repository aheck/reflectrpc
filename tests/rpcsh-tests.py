#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import os
import signal
import sys
import unittest

import pexpect

sys.path.append('..')

from reflectrpc.rpcsh import print_functions
from reflectrpc.rpcsh import split_exec_line
from reflectrpc.rpcsh import ReflectRpcShell
from reflectrpc.testing import ServerRunner

class RpcShTests(unittest.TestCase):
    def test_split_exec_line(self):
        tokens = split_exec_line('echo')
        self.assertEqual(tokens, ['echo'])

        tokens = split_exec_line('echo     ')
        self.assertEqual(tokens, ['echo'])

        tokens = split_exec_line('echo "Hello Server"')
        self.assertEqual(tokens, ['echo', 'Hello Server'])

        tokens = split_exec_line('  echo   "Hello Server"    ')
        self.assertEqual(tokens, ['echo', 'Hello Server'])

        tokens = split_exec_line('add 4 5')
        self.assertEqual(tokens, ['add', 4, 5])

        tokens = split_exec_line('add 4452 5980')
        self.assertEqual(tokens, ['add', 4452, 5980])

        tokens = split_exec_line('    add    4     5    ')
        self.assertEqual(tokens, ['add', 4, 5])

        tokens = split_exec_line('test 4 5 "A String" "Another String" 3424 453.9 true null "Yet another String"')
        self.assertEqual(tokens, ['test', 4, 5, 'A String', 'Another String',
            3424, 453.9, True, None, 'Yet another String'])

        tokens = split_exec_line('test 4 [5]')
        self.assertEqual(tokens, ['test', 4, [5]])

        tokens = split_exec_line('test 4 [5   ]')
        self.assertEqual(tokens, ['test', 4, [5]])

        tokens = split_exec_line('    test    4   [   5   ]')
        self.assertEqual(tokens, ['test', 4, [5]])

        tokens = split_exec_line('test ["Hello Server", 5, "String"] [5]')
        self.assertEqual(tokens, ['test', ["Hello Server", 5, "String"], [5]])

        tokens = split_exec_line('test {"num": 5, "name": "object"}')
        self.assertEqual(tokens, ['test', {'num': 5, 'name': 'object'}])

        tokens = split_exec_line('func [1,2,3,4,5,6] [7,8,9] [10,11,12,13]')
        self.assertEqual(tokens, ['func', [1,2,3,4,5,6], [7,8,9], [10,11,12,13]])

        tokens = split_exec_line('func {"array": [{"key1": "value1", "key2": "value2"}]} 5 ["str1", "str2", 5, "str3"]')
        self.assertEqual(tokens, ['func', {'array': [{'key1': 'value1', 'key2': 'value2'}]}, 5, ['str1', 'str2', 5, 'str3']])

    def test_rpcsh_compiles_and_runs(self):
        python = sys.executable
        exit_status = os.system("cd .. && %s rpcsh --help > /dev/null" % (python))
        self.assertEqual(exit_status, 0)

    def test_rpcsh_expect(self):
        server = ServerRunner('../examples/server.py', 5500)
        server.run()

        try:
            child = pexpect.spawn ('../rpcsh localhost 5500')

            child.expect('ReflectRPC Shell\r\n')
            child.expect('================\r\n\r\n')
            child.expect("Type 'help' for available commands\r\n\r\n")
            child.expect('RPC server: localhost:5500\r\n\r\n')
            child.expect('Self-description of Service:\r\n')
            child.expect('============================\r\n')
            child.expect('Example RPC Service \(1.0\)\r\n')
            child.expect('This is an example service for ReflectRPC\r\n')
            child.expect('\(rpc\) ')
        finally:
            child.kill(signal.SIGTERM)
            server.stop()

if __name__ == '__main__':
    unittest.main()
