#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import errno
import sys
import json
import os
import os.path
import pexpect
import shutil
import subprocess
import tempfile
import unittest

sys.path.append('..')

from reflectrpc.testing import ServerRunner

class RpcDocTests(unittest.TestCase):
    def test_rpcdoc_basic_operation(self):
        try:
            server = ServerRunner('../examples/server.py', 5500)
            server.run()

            python = sys.executable

            dirname = tempfile.mkdtemp()
            filename = os.path.join(dirname, 'doc.html')
            status = os.system('%s ../rpcdoc localhost 5500 %s' % (python, filename))

            if status != 0:
                self.fail('rpcdoc returned with a non-zero status code')

            if not os.path.exists(filename):
                self.fail("File '%s' was not created by rpcdoc" % (filename))

            statinfo = os.stat(filename)
            self.assertGreater(statinfo.st_size, 0)
        finally:
            server.stop()
            shutil.rmtree(dirname)

    def test_rpcdoc_unix_socket(self):
        try:
            server = ServerRunner('../examples/serverunixsocket.py', '/tmp/reflectrpc.sock')
            server.run()

            python = sys.executable

            dirname = tempfile.mkdtemp()
            filename = os.path.join(dirname, 'doc.html')
            status = os.system('%s ../rpcdoc unix:///tmp/reflectrpc.sock %s' % (python, filename))

            if status != 0:
                self.fail('rpcdoc returned with a non-zero status code')

            if not os.path.exists(filename):
                self.fail("File '%s' was not created by rpcdoc" % (filename))

            statinfo = os.stat(filename)
            self.assertGreater(statinfo.st_size, 0)
        finally:
            server.stop()
            shutil.rmtree(dirname)

    def test_rpcdoc_http(self):
        try:
            server = ServerRunner('../examples/serverhttp.py', 5500)
            server.run()

            python = sys.executable

            dirname = tempfile.mkdtemp()
            filename = os.path.join(dirname, 'doc.html')
            status = os.system('%s ../rpcdoc localhost 5500 %s --http' % (python, filename))

            if status != 0:
                self.fail('rpcdoc returned with a non-zero status code')

            if not os.path.exists(filename):
                self.fail("File '%s' was not created by rpcdoc" % (filename))

            statinfo = os.stat(filename)
            self.assertGreater(statinfo.st_size, 0)
        finally:
            server.stop()
            shutil.rmtree(dirname)

    def test_rpcdoc_http_basic_auth(self):
        try:
            server = ServerRunner('../examples/serverhttp.py', 5500)
            server.run()

            python = sys.executable

            dirname = tempfile.mkdtemp()
            filename = os.path.join(dirname, 'doc.html')
            child = pexpect.spawn('%s ../rpcdoc localhost 5500 %s --http --http-basic-user testuser' % (python, filename))
            child.expect('Password: ')
            child.sendline('123456')
            child.read()
            child.wait()

            if child.status != 0:
                self.fail('rpcdoc returned with a non-zero status code')

            if not os.path.exists(filename):
                self.fail("File '%s' was not created by rpcdoc" % (filename))

            statinfo = os.stat(filename)
            self.assertGreater(statinfo.st_size, 0)
        finally:
            server.stop()
            shutil.rmtree(dirname)

    def test_rpcdoc_tls(self):
        try:
            server = ServerRunner('../examples/servertls.py', 5500)
            server.run()

            python = sys.executable

            dirname = tempfile.mkdtemp()
            filename = os.path.join(dirname, 'doc.html')
            status = os.system('%s ../rpcdoc localhost 5500 %s --tls' % (python, filename))

            if status != 0:
                self.fail('rpcdoc returned with a non-zero status code')

            if not os.path.exists(filename):
                self.fail("File '%s' was not created by rpcdoc" % (filename))

            statinfo = os.stat(filename)
            self.assertGreater(statinfo.st_size, 0)
        finally:
            server.stop()
            shutil.rmtree(dirname)

    def test_rpcdoc_tls_client_auth(self):
        try:
            server = ServerRunner('../examples/servertls_clientauth.py', 5500)
            server.run()

            python = sys.executable

            dirname = tempfile.mkdtemp()
            filename = os.path.join(dirname, 'doc.html')
            status = os.system('%s ../rpcdoc localhost 5500 %s --tls --ca ../examples/certs/rootCA.crt --key ../examples/certs/client.key --cert ../examples/certs/client.crt' % (python, filename))

            if status != 0:
                self.fail('rpcdoc returned with a non-zero status code')

            if not os.path.exists(filename):
                self.fail("File '%s' was not created by rpcdoc" % (filename))

            statinfo = os.stat(filename)
            self.assertGreater(statinfo.st_size, 0)
        finally:
            server.stop()
            shutil.rmtree(dirname)


if __name__ == '__main__':
    unittest.main()
