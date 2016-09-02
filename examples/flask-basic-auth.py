#!/usr/bin/env python3

#
# Connect to this server with: rpcsh localhost 5000 --http --http-basic-user testuser
#

import sys
import json
from functools import wraps
from flask import Flask, request, Response

sys.path.append('..')

import reflectrpc
import reflectrpc.simpleserver

import rpcexample

app = Flask(__name__)

jsonrpc = rpcexample.build_example_rpcservice()

def check_auth(username, password):
    return username == 'testuser' and password == '123456'

def authenticate():
    return Response('Login required', 401,
    {'WWW-Authenticate': 'Basic realm="ReflectRPC"'})

def requires_auth(f):
    @wraps(f)
    def decorated():
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(auth.username)
    return decorated

@app.route('/rpc', methods=['POST'])
@requires_auth
def rpc_handler(username):
    rpcinfo = {'authenticated': True, 'username': username}
    response = jsonrpc.process_request(request.get_data().decode('utf-8'),
            rpcinfo)
    reply = json.dumps(response)

    return Response(reply, 200, mimetype='application/json-rpc')

if __name__ == '__main__':
    app.run()
