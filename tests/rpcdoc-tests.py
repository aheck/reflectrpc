#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import errno
import sys
import json
import os
import os.path
import shutil
import subprocess
import tempfile
import unittest

sys.path.append('..')

from reflectrpc.testing import ServerRunner

class RpcDocTests(unittest.TestCase):
    def test_basic_operation(self):
        server = ServerRunner('../examples/server.py', 5500)
        server.run()

        python = sys.executable

        try:
            dirname = tempfile.mkdtemp()
            filename = os.path.join(dirname, 'doc.html')
            status = os.system('%s ../rpcdoc localhost 5500 %s' % (python, filename))

            if status != 0:
                self.fail('rpcdoc returned with a non-zero status code')

            if not os.path.exists(filename):
                self.fail("File '%s' was not created by rpcdoc" % (filename))
        finally:
            server.stop()
            shutil.rmtree(dirname)


if __name__ == '__main__':
    unittest.main()
