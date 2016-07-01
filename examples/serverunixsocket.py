#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import sys

sys.path.append('..')

import reflectrpc
import reflectrpc.twistedserver

import rpcexample

jsonrpc = rpcexample.build_example_rpcservice()
server = reflectrpc.twistedserver.TwistedJsonRpcServer(jsonrpc,
       'unix:///tmp/reflectrpc.sock', 0)
server.run()
