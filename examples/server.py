#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import sys

sys.path.append('..')

import reflectrpc
import reflectrpc.simpleserver

import rpcexample

try:
    jsonrpc = rpcexample.build_example_rpcservice()
    server = reflectrpc.simpleserver.SimpleJsonRpcServer(jsonrpc, 'localhost', 5500)
    server.run()
except KeyboardInterrupt:
    sys.exit(0)
