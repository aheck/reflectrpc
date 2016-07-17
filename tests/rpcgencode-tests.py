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

class RpcGenCodeTests(unittest.TestCase):
    def test_basic_operation(self):
        server = ServerRunner('../examples/server.py', 5500)
        server.run()

        python = sys.executable
        cwd = os.getcwd()

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

            os.chdir(dirname)

            cmd = "%s -c 'import sys; sys.path.append(\"%s/..\"); import example; c = example.ServiceClient(); print(c.echo(\"Hello Server\"))'" % (python, cwd)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            (out, status) = proc.communicate()

            self.assertEqual('Hello Server\n', out.decode('utf-8'))
        finally:
            server.stop()
            shutil.rmtree(dirname)
            os.chdir(cwd)


if __name__ == '__main__':
    unittest.main()
