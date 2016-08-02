#!/usr/bin/env python3

import sys

import twisted.internet.defer as defer
from twisted.internet import task
from twisted.internet import reactor

sys.path.append('..')

from reflectrpc import RpcFunction
from reflectrpc import RpcProcessor
from reflectrpc import JsonRpcError
import reflectrpc.twistedserver

def slow_operation():
    def calc_value(value):
        return 42

    return task.deferLater(reactor, 1, calc_value, None)

def fast_operation():
    return 41

def deferred_error():
    def calc_result(value):
        raise JsonRpcError("You wanted an error, here you have it!")

    return task.deferLater(reactor, 0.1, calc_result, None)

def deferred_internal_error():
    def calc_result(value):
        return 56 / 0

    return task.deferLater(reactor, 0.1, calc_result, None)

jsonrpc = RpcProcessor()
jsonrpc.set_description("Concurrency Example RPC Service",
        "This service demonstrates concurrency with the Twisted Server", "1.0")

slow_func = reflectrpc.RpcFunction(slow_operation, 'slow_operation', 'Calculate ultimate answer',
        'int', 'Ultimate answer')
jsonrpc.add_function(slow_func)

fast_func = reflectrpc.RpcFunction(fast_operation, 'fast_operation',
        'Calculate fast approximation of the ultimate answer',
        'int', 'Approximation of the ultimate answer')
jsonrpc.add_function(fast_func)

error_func = reflectrpc.RpcFunction(deferred_error, 'deferred_error', 'Raise a JsonRpcError from a deferred function',
        'int', 'Nothing of interest')
jsonrpc.add_function(error_func)

internal_error_func = reflectrpc.RpcFunction(deferred_internal_error, 'deferred_internal_error',
        'Raise an internal error from adeferred function', 'int', 'Nothing of interest')
jsonrpc.add_function(internal_error_func)

server = reflectrpc.twistedserver.TwistedJsonRpcServer(jsonrpc, 'localhost', 5500)
server.run()
