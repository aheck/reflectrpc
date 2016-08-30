#!/usr/bin/env python3

#
# Connect to this server with: rpcsh localhost 5000 --http
#

import sys
import json
from flask import Flask, request, Response

sys.path.append('..')

import reflectrpc
import reflectrpc.simpleserver

import rpcexample

app = Flask(__name__)

jsonrpc = rpcexample.build_example_rpcservice()

@app.route('/rpc', methods=['POST'])
def rpc_handler():
    response = jsonrpc.process_request(request.get_data().decode('utf-8'))
    reply = json.dumps(response)

    return Response(reply, 200, mimetype='application/json-rpc')

if __name__ == '__main__':
    app.run()
