#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import errno
import sys
import json
import os
import os.path
import shutil
import tempfile
import unittest

sys.path.append('..')

from reflectrpc.client import RpcClient
from reflectrpc.client import RpcError
from reflectrpc.client import NetworkError
from reflectrpc.client import HttpException
from reflectrpc.testing import ServerRunner

class RpcGenCodeTests(unittest.TestCase):
    def test_basic_operation(self):
        server = ServerRunner('../examples/server.py', 5500)
        server.run()

        python = sys.executable

        try:
            dirname = tempfile.mkdtemp()
            packagedir = os.path.join(dirname, 'example')
            os.mkdir(packagedir)
            filename = os.path.join(packagedir, '__init__.py')
            status = os.system('%s ../rpcgencode localhost 5500 %s' % (python, filename))

            if status != 0:
                self.fail('rpcgencode returned with a non-zero status code')

            if not os.path.exists(filename):
                self.fail("File '%s' was not created by rpcgencode" % (filename))

            status = os.system('%s -m py_compile %s' % (python, filename))

            if status != 0:
                self.fail("Syntax error in file '%s'" % (filename))
        finally:
            server.stop()
            shutil.rmtree(dirname)


if __name__ == '__main__':
    unittest.main()
