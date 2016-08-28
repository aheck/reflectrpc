#!/usr/bin/env python3

import os
import sys
from flask import Flask, render_template, request

sys.path.append('..')

from reflectrpc.client import RpcClient
from reflectrpc.cmdline import fetch_service_metainfo

app = Flask(__name__)

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

        client = RpcClient(host, port)

        if http:
            http = 'Yes'
            client.enable_http()
        else:
            http = 'No'

        (service_description, functions, custom_types) = fetch_service_metainfo(client)

        for func in functions:
            func['name_with_params'] = func['name'] + '('
            first = True
            for param in func['params']:
                if not first:
                    func['name_with_params'] += ', '
                func['name_with_params'] += param['name']
                first = False

            func['name_with_params'] += ')'

        return render_template('app.html', functions=functions,
                service_description=service_description,
                custom_types=custom_types, host=host, port=port, http=http)
    else:
        return render_template('login.html')

@app.route('/call_json_rpc')
def call_json_rpc():
    params = request.args.get('params', 0, type=str)
    return jsonify(result=a + b)

if __name__ == '__main__':
    app.run(debug=True)
