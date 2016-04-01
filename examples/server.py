#!/usr/bin/env python3

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
