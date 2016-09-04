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

    def test_rpcsh_complete_function_names(self):
        rpcsh = ReflectRpcShell(None)
        rpcsh.functions = [
                {'name': 'get_something'},
                {'name': 'get_anotherthing'},
                {'name': 'echo'},
                {'name': 'echoEcho'},
                {'name': 'add'},
        ]

        result = rpcsh.function_completion('', 'exec ')
        self.assertEqual(result, ['get_something', 'get_anotherthing', 'echo', 'echoEcho', 'add'])

        result = rpcsh.function_completion('get_', 'exec get_')
        self.assertEqual(result, ['get_something', 'get_anotherthing'])

        result = rpcsh.function_completion('ad', 'exec ad')
        self.assertEqual(result, ['add'])

        result = rpcsh.function_completion('add', 'exec add')
        self.assertEqual(result, [])

        result = rpcsh.function_completion('echo', 'exec echo')
        self.assertEqual(result, ['echo', 'echoEcho'])

    def test_rpcsh_complete_type_names(self):
        rpcsh = ReflectRpcShell(None)
        rpcsh.custom_types = [
                {'name': 'AddressExtension'},
                {'name': 'AddressEntry'},
                {'name': 'CPU'},
                {'name': 'CPUInfo'},
                {'name': 'Order'},
        ]

        result = rpcsh.complete_type('', 'exec ', 0, 0)
        self.assertEqual(result, ['AddressExtension', 'AddressEntry', 'CPU', 'CPUInfo', 'Order'])

        result = rpcsh.complete_type('Address', 'exec Address', 0, 0)
        self.assertEqual(result, ['AddressExtension', 'AddressEntry'])

        result = rpcsh.complete_type('Ord', 'exec Ord', 0, 0)
        self.assertEqual(result, ['Order'])

        result = rpcsh.complete_type('Order', 'exec Order', 0, 0)
        self.assertEqual(result, [])

        result = rpcsh.complete_type('CPU', 'exec CPU', 0, 0)
        self.assertEqual(result, ['CPU', 'CPUInfo'])

    def test_rpcsh_expect_simple(self):
        server = ServerRunner('../examples/server.py', 5500)
        server.run()

        try:
            python = sys.executable
            child = pexpect.spawn('%s ../rpcsh localhost 5500' % (python))

            child.expect('ReflectRPC Shell\r\n')
            child.expect('================\r\n\r\n')
            child.expect("Type 'help' for available commands\r\n\r\n")
            child.expect('RPC server: localhost:5500\r\n\r\n')
            child.expect('Self-description of the Service:\r\n')
            child.expect('================================\r\n')
            child.expect('Example RPC Service \(1.0\)\r\n')
            child.expect('This is an example service for ReflectRPC\r\n')
            child.expect('\(rpc\) ')

            child.sendline('list')
            child.expect('echo\(message\)\r\n')
            child.expect('add\(a, b\)\r\n')
            child.expect('sub\(a, b\)\r\n')
            child.expect('mul\(a, b\)\r\n')
            child.expect('div\(a, b\)\r\n')
            child.expect('enum_echo\(phone_type\)\r\n')
            child.expect('hash_echo\(address\)\r\n')
            child.expect('notify\(value\)\r\n')
            child.expect('is_authenticated\(\)\r\n')
            child.expect('get_username\(\)\r\n')
            child.expect('echo_ints\(ints\)\r\n')

            child.sendline('exec echo "Hello Server"')
            child.expect('Server replied: "Hello Server"\r\n')

            child.sendline('exec add 5 6')
            child.expect('Server replied: 11\r\n')

            child.sendline('exec is_authenticated')
            child.expect('Server replied: false\r\n')

            child.sendline('exec get_username')
            child.expect('Server replied: null\r\n')
        finally:
            child.kill(signal.SIGTERM)
            server.stop()

    def test_rpcsh_expect_unix_socket(self):
        server = ServerRunner('../examples/serverunixsocket.py',
                '/tmp/reflectrpc.sock')
        server.run()

        try:
            python = sys.executable
            child = pexpect.spawn('%s ../rpcsh unix:///tmp/reflectrpc.sock' % (python))

            child.expect('ReflectRPC Shell\r\n')
            child.expect('================\r\n\r\n')
            child.expect("Type 'help' for available commands\r\n\r\n")
            child.expect('RPC server: unix:///tmp/reflectrpc.sock\r\n\r\n')
            child.expect('Self-description of the Service:\r\n')
            child.expect('================================\r\n')
            child.expect('Example RPC Service \(1.0\)\r\n')
            child.expect('This is an example service for ReflectRPC\r\n')
            child.expect('\(rpc\) ')

            child.sendline('list')
            child.expect('echo\(message\)\r\n')
            child.expect('add\(a, b\)\r\n')
            child.expect('sub\(a, b\)\r\n')
            child.expect('mul\(a, b\)\r\n')
            child.expect('div\(a, b\)\r\n')
            child.expect('enum_echo\(phone_type\)\r\n')
            child.expect('hash_echo\(address\)\r\n')
            child.expect('notify\(value\)\r\n')
            child.expect('is_authenticated\(\)\r\n')
            child.expect('get_username\(\)\r\n')
            child.expect('echo_ints\(ints\)\r\n')

            child.sendline('exec echo "Hello Server"')
            child.expect('Server replied: "Hello Server"\r\n')

            child.sendline('exec add 5 6')
            child.expect('Server replied: 11\r\n')

            child.sendline('exec is_authenticated')
            child.expect('Server replied: false\r\n')

            child.sendline('exec get_username')
            child.expect('Server replied: null\r\n')
        finally:
            child.kill(signal.SIGTERM)
            server.stop()

    def test_rpcsh_expect_http(self):
        server = ServerRunner('../examples/serverhttp.py', 5500)
        server.run()

        try:
            python = sys.executable
            child = pexpect.spawn('%s ../rpcsh localhost 5500 --http' % (python))

            child.expect('ReflectRPC Shell\r\n')
            child.expect('================\r\n\r\n')
            child.expect("Type 'help' for available commands\r\n\r\n")
            child.expect('RPC server: localhost:5500\r\n\r\n')
            child.expect('Self-description of the Service:\r\n')
            child.expect('================================\r\n')
            child.expect('Example RPC Service \(1.0\)\r\n')
            child.expect('This is an example service for ReflectRPC\r\n')
            child.expect('\(rpc\) ')

            child.sendline('list')
            child.expect('echo\(message\)\r\n')
            child.expect('add\(a, b\)\r\n')
            child.expect('sub\(a, b\)\r\n')
            child.expect('mul\(a, b\)\r\n')
            child.expect('div\(a, b\)\r\n')
            child.expect('enum_echo\(phone_type\)\r\n')
            child.expect('hash_echo\(address\)\r\n')
            child.expect('notify\(value\)\r\n')
            child.expect('is_authenticated\(\)\r\n')
            child.expect('get_username\(\)\r\n')
            child.expect('echo_ints\(ints\)\r\n')

            child.sendline('exec echo "Hello Server"')
            child.expect('Server replied: "Hello Server"\r\n')

            child.sendline('exec add 5 6')
            child.expect('Server replied: 11\r\n')

            child.sendline('exec is_authenticated')
            child.expect('Server replied: false\r\n')

            child.sendline('exec get_username')
            child.expect('Server replied: null\r\n')
        finally:
            child.kill(signal.SIGTERM)
            server.stop()

    def test_rpcsh_expect_http_basic_auth(self):
        server = ServerRunner('../examples/serverhttp.py', 5500)
        server.run()

        try:
            python = sys.executable
            child = pexpect.spawn('%s ../rpcsh localhost 5500 --http --http-basic-user testuser' % (python))
            child.expect('Password: ')
            child.send('123456\r\n')

            child.expect('ReflectRPC Shell\r\n')
            child.expect('================\r\n\r\n')
            child.expect("Type 'help' for available commands\r\n\r\n")
            child.expect('RPC server: localhost:5500\r\n\r\n')
            child.expect('Self-description of the Service:\r\n')
            child.expect('================================\r\n')
            child.expect('Example RPC Service \(1.0\)\r\n')
            child.expect('This is an example service for ReflectRPC\r\n')
            child.expect('\(rpc\) ')

            child.sendline('list')
            child.expect('echo\(message\)\r\n')
            child.expect('add\(a, b\)\r\n')
            child.expect('sub\(a, b\)\r\n')
            child.expect('mul\(a, b\)\r\n')
            child.expect('div\(a, b\)\r\n')
            child.expect('enum_echo\(phone_type\)\r\n')
            child.expect('hash_echo\(address\)\r\n')
            child.expect('notify\(value\)\r\n')
            child.expect('is_authenticated\(\)\r\n')
            child.expect('get_username\(\)\r\n')
            child.expect('echo_ints\(ints\)\r\n')

            child.sendline('exec echo "Hello Server"')
            child.expect('Server replied: "Hello Server"\r\n')

            child.sendline('exec add 5 6')
            child.expect('Server replied: 11\r\n')

            child.sendline('exec is_authenticated')
            child.expect('Server replied: true\r\n')

            child.sendline('exec get_username')
            child.expect('Server replied: "testuser"\r\n')
        finally:
            child.kill(signal.SIGTERM)
            server.stop()

    def test_rpcsh_expect_tls(self):
        server = ServerRunner('../examples/servertls.py', 5500)
        server.run()

        try:
            python = sys.executable
            child = pexpect.spawn('%s ../rpcsh localhost 5500 --tls' % (python))

            child.expect('ReflectRPC Shell\r\n')
            child.expect('================\r\n\r\n')
            child.expect("Type 'help' for available commands\r\n\r\n")
            child.expect('RPC server: localhost:5500\r\n\r\n')
            child.expect('Self-description of the Service:\r\n')
            child.expect('================================\r\n')
            child.expect('Example RPC Service \(1.0\)\r\n')
            child.expect('This is an example service for ReflectRPC\r\n')
            child.expect('\(rpc\) ')

            child.sendline('list')
            child.expect('echo\(message\)\r\n')
            child.expect('add\(a, b\)\r\n')
            child.expect('sub\(a, b\)\r\n')
            child.expect('mul\(a, b\)\r\n')
            child.expect('div\(a, b\)\r\n')
            child.expect('enum_echo\(phone_type\)\r\n')
            child.expect('hash_echo\(address\)\r\n')
            child.expect('notify\(value\)\r\n')
            child.expect('is_authenticated\(\)\r\n')
            child.expect('get_username\(\)\r\n')
            child.expect('echo_ints\(ints\)\r\n')

            child.sendline('exec echo "Hello Server"')
            child.expect('Server replied: "Hello Server"\r\n')

            child.sendline('exec add 5 6')
            child.expect('Server replied: 11\r\n')

            child.sendline('exec is_authenticated')
            child.expect('Server replied: false\r\n')

            child.sendline('exec get_username')
            child.expect('Server replied: null\r\n')
        finally:
            child.kill(signal.SIGTERM)
            server.stop()

    def test_rpcsh_expect_tls_client_auth(self):
        server = ServerRunner('../examples/servertls_clientauth.py', 5500)
        server.run()

        try:
            python = sys.executable
            child = pexpect.spawn('%s ../rpcsh localhost 5500 --tls --ca ../examples/certs/rootCA.crt --key ../examples/certs/client.key --cert ../examples/certs/client.crt' % (python))

            child.expect('ReflectRPC Shell\r\n')
            child.expect('================\r\n\r\n')
            child.expect("Type 'help' for available commands\r\n\r\n")
            child.expect('RPC server: localhost:5500\r\n\r\n')
            child.expect('Self-description of the Service:\r\n')
            child.expect('================================\r\n')
            child.expect('Example RPC Service \(1.0\)\r\n')
            child.expect('This is an example service for ReflectRPC\r\n')
            child.expect('\(rpc\) ')

            child.sendline('list')
            child.expect('echo\(message\)\r\n')
            child.expect('add\(a, b\)\r\n')
            child.expect('sub\(a, b\)\r\n')
            child.expect('mul\(a, b\)\r\n')
            child.expect('div\(a, b\)\r\n')
            child.expect('enum_echo\(phone_type\)\r\n')
            child.expect('hash_echo\(address\)\r\n')
            child.expect('notify\(value\)\r\n')
            child.expect('is_authenticated\(\)\r\n')
            child.expect('get_username\(\)\r\n')
            child.expect('echo_ints\(ints\)\r\n')

            child.sendline('exec echo "Hello Server"')
            child.expect('Server replied: "Hello Server"\r\n')

            child.sendline('exec add 5 6')
            child.expect('Server replied: 11\r\n')

            child.sendline('exec is_authenticated')
            child.expect('Server replied: true\r\n')

            child.sendline('exec get_username')
            child.expect('Server replied: "example-username"\r\n')
        finally:
            child.kill(signal.SIGTERM)
            server.stop()

if __name__ == '__main__':
    unittest.main()
