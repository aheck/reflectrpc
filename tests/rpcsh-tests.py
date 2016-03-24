#!/usr/bin/env python3

import sys
import unittest

sys.path.append('..')

from reflectrpc.rpcsh import print_functions
from reflectrpc.rpcsh import split_exec_line
from reflectrpc.rpcsh import ReflectRpcShell

class RpcShTests(unittest.TestCase):
    def test_split_exec_line(self):
        tokens = split_exec_line('echo "Hello Server"')
        self.assertEqual(tokens, ['echo', 'Hello Server'])

        tokens = split_exec_line('add 4 5')
        self.assertEqual(tokens, ['add', 4, 5])

if __name__ == '__main__':
    unittest.main()
