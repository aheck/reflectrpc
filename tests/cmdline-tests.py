#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import os
import sys
import unittest

import pexpect

sys.path.append('..')

from reflectrpc.testing import ServerRunner

# Generic tests for ReflectRPC command-line utils
class CmdlineTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CmdlineTests, self).__init__(*args, **kwargs)
        self.cmdline_programs = ['rpcsh', 'rpcdoc', 'rpcgencode']

    def test_cmdline_expect_connection_fails(self):
        for cmd in self.cmdline_programs:
            # connect although no server is running
            try:
                python = sys.executable
                outfile = ''
                if cmd != 'rpcsh':
                    outfile = 'outfile.html'

                child = pexpect.spawn('%s ../%s localhost 5500 %s' % (python, cmd, outfile))

                child.expect('NetworkError: \[Errno \d+\] Connection refused\r\n')
                child.expect('\r\n')
                child.expect('Failed to connect to localhost on TCP port 5500\r\n')
            finally:
                child.close(True)

            # connect to a TLS server without enabling TLS
            try:
                server = ServerRunner('../examples/servertls.py', 5500)
                server.run()

                python = sys.executable
                outfile = ''
                if cmd != 'rpcsh':
                    outfile = 'outfile.html'

                child = pexpect.spawn('%s ../%s localhost 5500 %s' % (python, cmd, outfile))

                child.expect('NetworkError: Non-JSON content received\r\n')
                child.expect('\r\n')
                child.expect('Failed to connect to localhost on TCP port 5500\r\n')
            finally:
                child.close(True)
                server.stop()

            # connect to a Non-TLS server with enabled TLS
            try:
                server = ServerRunner('../examples/server.py', 5500)
                server.run()

                python = sys.executable
                outfile = ''
                if cmd != 'rpcsh':
                    outfile = 'outfile.html'

                child = pexpect.spawn('%s ../%s localhost 5500 %s --tls' % (python, cmd, outfile))

                child.expect('NetworkError: EOF occurred in violation of protocol \(_ssl.c:\d+\)\r\n')
                child.expect('\r\n')
                child.expect('Failed to connect to localhost on TCP port 5500\r\n')
            finally:
                child.close(True)
                server.stop()

            # connect to a TLS server but fail the hostname check
            try:
                server = ServerRunner('../examples/servertls.py', 5500)
                server.run()

                python = sys.executable
                outfile = ''
                if cmd != 'rpcsh':
                    outfile = 'outfile.html'

                child = pexpect.spawn('%s ../%s localhost 5500 %s --tls --ca ../examples/certs/rootCA.crt --check-hostname' % (python, cmd, outfile))

                child.expect("NetworkError: TLSHostnameError: Host name 'localhost' doesn't match certificate host 'reflectrpc'\r\n")
                child.expect('\r\n')
                child.expect('Failed to connect to localhost on TCP port 5500\r\n')
            finally:
                child.close(True)
                server.stop()

    def test_cmdline_expect_wrong_arguments(self):
        for cmd in self.cmdline_programs:
            # check what happens when rpcsh is called without parameters
            try:
                python = sys.executable
                child = pexpect.spawn('%s ../%s' % (python, cmd))

                python3_errstr = '%s: error: the following arguments are required: HOST, PORT, OUTFILE' % (cmd)
                if cmd == 'rpcsh':
                    python3_errstr = '%s: error: the following arguments are required: HOST, PORT' % (cmd)

                child.expect('\r\n(%s: error: too few arguments|%s)\r\n' % (cmd, python3_errstr))
            finally:
                child.close(True)

            # check that --cert doesn't work without --key
            try:
                python = sys.executable
                outfile = ''
                if cmd != 'rpcsh':
                    outfile = 'outfile.html'

                child = pexpect.spawn('%s ../%s localhost 5500 %s --tls --ca ../examples/certs/rootCA.crt --cert ../examples/certs/rootCA.crt' % (python, cmd, outfile))

                child.expect('\r\n--cert also requires --key\r\n')
            finally:
                child.close(True)

            # check that --key doesn't work without --cert
            try:
                python = sys.executable
                outfile = ''
                if cmd != 'rpcsh':
                    outfile = 'outfile.html'

                child = pexpect.spawn('%s ../%s localhost 5500 %s --tls --ca ../examples/certs/rootCA.crt --key ../examples/certs/client.key' % (python, cmd, outfile))

                child.expect('\r\n--key also requires --cert\r\n')
            finally:
                child.close(True)

            # check that --cert and --key don't work without --ca
            try:
                python = sys.executable
                outfile = ''
                if cmd != 'rpcsh':
                    outfile = 'outfile.html'

                child = pexpect.spawn('%s ../%s localhost 5500 %s --tls --cert ../examples/certs/rootCA.crt --key ../examples/certs/client.key' % (python, cmd, outfile))

                child.expect('\r\nClient auth requires --ca\r\n')
            finally:
                child.close(True)

if __name__ == '__main__':
    unittest.main()
