#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import sys

sys.path.append('..')

import reflectrpc
import reflectrpc.twistedserver

import rpcexample

def check_password(username, password):
    if username == 'testuser' and password == '123456':
        return True

    return False

jsonrpc = rpcexample.build_example_rpcservice()
server = reflectrpc.twistedserver.TwistedJsonRpcServer(jsonrpc, 'localhost', 5500)
server.enable_http()
server.enable_http_basic_auth(check_password)
server.run()
