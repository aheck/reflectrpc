#!/usr/bin/env python3

import sys

sys.path.append('..')

import reflectrpc
import reflectrpc.twistedserver

import rpcexample

jsonrpc = rpcexample.build_example_rpcservice()
server = reflectrpc.twistedserver.TwistedJsonRpcServer(jsonrpc, 'localhost', 5500)
server.enable_http()
server.enable_tls('./certs/server.pem')
server.enable_client_auth('./certs/rootCA.crt')
server.run()
