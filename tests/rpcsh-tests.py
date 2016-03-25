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

if __name__ == '__main__':
    unittest.main()
