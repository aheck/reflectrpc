#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import errno
import sys
import json
import os
import unittest

sys.path.append('..')

from reflectrpc.client import RpcClient
from reflectrpc.client import RpcError
from reflectrpc.client import NetworkError
from reflectrpc.testing import ServerRunner

class ClientServerTests(unittest.TestCase):
    def test_simple_server(self):
        server = ServerRunner('../examples/server.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            result = client.rpc_call('echo', 'Hello Server')
            client.close_connection()

            self.assertEqual(result, 'Hello Server')
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server(self):
        server = ServerRunner('../examples/servertwisted.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            result = None

            result = client.rpc_call('echo', 'Hello Server')
            client.close_connection()

            self.assertEqual(result, 'Hello Server')
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_http(self):
        server = ServerRunner('../examples/serverhttp.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)
        client.enable_http()

        try:
            result = client.rpc_call('echo', 'Hello Server')

            self.assertEqual(result, 'Hello Server')
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_tls(self):
        server = ServerRunner('../examples/servertls.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            client.enable_tls(None)

            result = client.rpc_call('echo', 'Hello Server')

            self.assertEqual(result, 'Hello Server')
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_tls_non_tls_client_fail(self):
        server = ServerRunner('../examples/servertls.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            with self.assertRaises(NetworkError) as cm:
                client.rpc_call('echo', 'Hello Server')

            self.assertEqual(cm.exception.real_exception, "Non-JSON content received")
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_tls_cert_file_not_found(self):
        client = RpcClient('localhost', 5500)

        error = None
        with self.assertRaises(IOError) as cm:
            client.enable_tls('/file/that/does/not/exist')

        self.assertEqual(cm.exception.errno, errno.ENOENT)
        self.assertEqual(cm.exception.filename, '/file/that/does/not/exist')

    def test_twisted_server_tls_server_check(self):
        server = ServerRunner('../examples/servertls.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            client.enable_tls('../examples/certs/wrongCA.crt')

            with self.assertRaises(NetworkError) as cm:
                result = client.rpc_call('echo', 'Hello Server')

            python2_check = str(cm.exception.real_exception).startswith(
                    '[Errno 1]')
            python3_check = str(cm.exception.real_exception).startswith(
                    '[SSL: CERTIFICATE_VERIFY_FAILED]')
            self.assertTrue(python2_check or python3_check)
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_tls_hostname_check(self):
        server = ServerRunner('../examples/servertls.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            client.enable_tls('../examples/certs/rootCA.crt')

            with self.assertRaises(NetworkError) as cm:
                result = client.rpc_call('echo', 'Hello Server')

            self.assertEqual(str(cm.exception.real_exception),
                    "TLSHostnameError: Host name 'localhost' doesn't match certificate host 'reflectrpc'")
        finally:
            client.close_connection()
            server.stop()


    def test_twisted_server_tls_client_auth_no_client_cert(self):
        server = ServerRunner('../examples/servertls_clientauth.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            client.enable_tls('../examples/certs/rootCA.crt')

            with self.assertRaises(NetworkError) as cm:
                result = client.rpc_call('echo', 'Hello Server')

            python2_check = 'alert handshake failure' in str(cm.exception.real_exception)
            python3_check = str(cm.exception.real_exception).startswith(
                    "[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE]")
            self.assertTrue(python2_check or python3_check)
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_tls_client_auth(self):
        server = ServerRunner('../examples/servertls_clientauth.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            client.enable_tls('../examples/certs/rootCA.crt', False)
            client.enable_client_auth('../examples/certs/client.crt',
                    '../examples/certs/client.key')

            result = client.rpc_call('echo', 'Hello Server')

            self.assertEqual(result, "Hello Server")
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_tls_client_auth_wrong_client_cert(self):
        server = ServerRunner('../examples/servertls_clientauth.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            client.enable_tls('../examples/certs/rootCA.crt', False)
            client.enable_client_auth('../examples/certs/wrong-client.crt',
                    '../examples/certs/wrong-client.key')

            with self.assertRaises(NetworkError) as cm:
                result = client.rpc_call('echo', 'Hello Server')

            self.assertTrue('alert decrypt error' in str(cm.exception.real_exception))
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_tls_client_auth_username(self):
        server = ServerRunner('../examples/servertls_clientauth.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        try:
            client.enable_tls('../examples/certs/rootCA.crt', False)
            client.enable_client_auth('../examples/certs/client.crt',
                    '../examples/certs/client.key')

            authenticated = client.rpc_call('is_authenticated')
            username = client.rpc_call('get_username')

            self.assertEqual(authenticated, True)
            self.assertEqual(username, 'example-username')
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_tls_client_auth_username_http(self):
        server = ServerRunner('../examples/servertls_clientauth_http.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)
        client.enable_http()

        try:
            client.enable_tls('../examples/certs/rootCA.crt', False)
            client.enable_client_auth('../examples/certs/client.crt',
                    '../examples/certs/client.key')

            authenticated = client.rpc_call('is_authenticated')
            username = client.rpc_call('get_username')

            self.assertEqual(authenticated, True)
            self.assertEqual(username, 'example-username')
        finally:
            client.close_connection()
            server.stop()

    def test_twisted_server_http_basic_auth(self):
        server = ServerRunner('../examples/serverhttp_basic_auth.py', 5500)
        server.run()

        client = RpcClient('localhost', 5500)
        client.enable_http()
        client.enable_http_basic_auth('testuser', '123456')

        try:
            authenticated = client.rpc_call('is_authenticated')
            username = client.rpc_call('get_username')

            self.assertEqual(authenticated, True)
            self.assertEqual(username, 'testuser')
        finally:
            client.close_connection()
            server.stop()


if __name__ == '__main__':
    unittest.main()
