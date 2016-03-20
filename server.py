#!/usr/bin/env python3

import os
import sys

import reflectrpc
import reflectrpc.simpleserver

def echo(message):
    return message

def add(a, b):
    return a + b

jsonrpc = reflectrpc.ReflectRpcProcessor()

echo_func = reflectrpc.RpcFunction(echo, 'echo', 'Returns the message it was sent',
        'string', 'The message previously received')
echo_func.add_param('string', 'message', 'The message we will send back')
jsonrpc.add_function(echo_func)

add_func = reflectrpc.RpcFunction(add, 'add', 'Adds two numbers', 'int',
        'Sum of the two numbers')
add_func.add_param('int', 'a', 'First int to add')
add_func.add_param('int', 'b', 'Second int to add')
jsonrpc.add_function(add_func)

try:
    server = reflectrpc.simpleserver.SimpleJsonRpcServer(jsonrpc, 'localhost', 5500)
    server.run()
except KeyboardInterrupt:
    sys.exit(0)
