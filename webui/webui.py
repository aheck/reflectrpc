#!/usr/bin/env python3

import os
import sys
from flask import Flask, Response, render_template, request, session

sys.path.append('..')

import reflectrpc
from reflectrpc.client import RpcClient
from reflectrpc.client import RpcError
from reflectrpc.client import NetworkError
from reflectrpc.client import HttpException

app = Flask(__name__)

# not secure but since this application is supposed to run on your local PC
# and not in a production environment we don't care for the moment
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

def connect_client(host, port, http, username, password):
    client = RpcClient(host, port)
    if http:
        client.enable_http()
        if username and password:
            client.enable_http_basic_auth(username, password)

    return client

@app.route('/', methods=['GET', 'POST'])
def index_page():
    if request.method == 'POST':
        host = ''
        port = 0
        http = False
        username = ''
        password = ''

        if 'host' in request.form:
            host = request.form['host']
        if 'port' in request.form:
            port = int(request.form['port'])
        if 'http' in request.form:
            http = True
        if 'username' in request.form:
            username = request.form['username']
        if 'password' in request.form:
            password = request.form['password']

        session['host'] = host
        session['port'] = port
        session['http'] = http
        session['username'] = username
        session['password'] = password

        http_label = 'No'
        if http:
            http_label = 'Yes'

        service_description = ''
        functions = []
        custom_types = []

        try:
            client = connect_client(host, port, http, username, password)

            try:
                service_description = client.rpc_call('__describe_service')
            except RpcError:
                print("Call to '__describe_service' failed", file=sys.stderr)

            try:
                functions = client.rpc_call('__describe_functions')
            except RpcError:
                print("Call to '__describe_functions' failed", file=sys.stderr)

            try:
                custom_types = client.rpc_call('__describe_custom_types')
            except RpcError:
                print("Call to '__describe_custom_types' failed", file=sys.stderr)
        except NetworkError as e:
            return render_template('login.html', error=str(e))
        except HttpException as e:
            if e.status == '401':
                return render_template('login.html', error='Authentication failed')
            else:
                return render_template('login.html', error=str(e))
        finally:
            client.close_connection()

        for func in functions:
            func['name_with_params'] = func['name'] + '('
            first = True
            for param in func['params']:
                if not first:
                    func['name_with_params'] += ', '
                func['name_with_params'] += param['name']

                if param['type'].startswith('array') or param['type'] in ['base64', 'hash'] or param['type'][0].isupper():
                    param['control'] = 'textarea'
                else:
                    param['control'] = 'lineedit'

                first = False

            func['name_with_params'] += ')'

        return render_template('app.html', functions=functions,
                service_description=service_description,
                custom_types=custom_types, host=host, port=port, http=http_label)
    else:
        return render_template('login.html')

@app.route('/call_jsonrpc', methods=['POST'])
def call_json_rpc():
    funcname = request.form.get('funcname', '', type=str)
    params = request.form.get('params', '', type=str)

    req_id = 0
    if 'req_id' in session:
        req_id = int(session['req_id'])

    req_id += 1
    session['req_id'] = req_id

    client = None
    result = None

    try:
        client = connect_client(session['host'], session['port'], session['http'],
                session['username'], session['password'])
        result = client.rpc_call_raw('{"method": "%s", "params": [%s], "id": %d}'
                % (funcname, params, req_id))
    finally:
        client.close_connection()

    return Response(result, mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)
