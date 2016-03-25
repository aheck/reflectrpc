import os
import sys
import json
import socket

json_types = ['int', 'bool', 'float', 'string', 'array', 'hash', 'base64']

class JsonRpcError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    def to_json(self):
        error = {}

        error['name'] = type(self).__name__
        error['message'] = self.msg

        return error

class RpcFunction:
    """
    Description of a function exposed as RPC
    """
    def __init__(self, func, name, description, result_type, result_desc):
        if not result_type in json_types:
            raise ValueError("Invalid JSON-RPC type: %s" % (result_type))

        if not callable(func):
            raise ValueError("TypeError: Parameter func must be a function or another callable")

        self.func = func
        self.name = name
        self.description = description
        self.result_type = result_type
        self.result_desc = result_desc

        self.params = []

    def add_param(self, typ, name, description):
        if not typ in json_types:
            raise ValueError("Invalid JSON-RPC type: %s" % (typ))

        param = {'name': name, 'type': typ, 'desc': description}
        self.params.append(param)

    def to_dict(self):
        d = {}

        d['name'] = self.name
        d['description'] = self.description
        d['result_type'] = self.result_type
        d['result_desc'] = self.result_desc
        d['params'] = self.params

        return d

class RpcProcessor:
    """
    A JSON-RPC server that is capable of describing all its RPC functions to the client
    """
    def __init__(self):
        self.functions = []
        self.functions_dict = {}

    def add_function(self, func):
        if func.name in self.functions_dict:
            raise ValueError("Another function of the name '%s' is already registered" % (func.name))

        self.functions.append(func)
        self.functions_dict[func.name] = func

    def describe_functions(self):
        functions = []
        for item in self.functions:
            functions.append(item.to_dict())

        return functions

    def call_function(self, name, func, func_desc, *params):
        """Executes the actual function. Can be overridden for concurrent execution e.g."""
        return func(*params)

    def process_request(self, message):
        reply = {}
        request = {}

        reply['result'] = None

        try:
            request = json.loads(message)
        except ValueError:
            reply['id'] = -1
            reply['error'] = "Received invalid JSON"
            return reply

        if not 'id' in request.keys():
            reply['id'] = -1
            reply['error'] = "Field 'id' missing in request"
            return reply

        if not isinstance(request['id'], int):
            reply['id'] = -1
            reply['error'] = "Field 'id' must contain an integer value"
            return reply

        reply['id'] = request['id']

        if not 'method' in request.keys():
            reply['error'] = "Field 'method' missing in request"
            return reply

        if not isinstance(request['method'], str):
            reply['error'] = "Field 'method' must contain a string value"
            return reply

        if not 'params' in request.keys():
            reply['error'] = "Field 'params' missing in request"
            return reply

        if not isinstance(request['params'], list):
            reply['error'] = "Field 'params' must contain an array"
            return reply

        # check for builtin __describe_functions
        if request['method'] == '__describe_functions':
            reply['result'] = self.describe_functions()
            return reply

        if not request['method'] in self.functions_dict:
            reply['error'] = "No such method: %s. Call '__describe_functions' to get details on available function calls" % (request['method'])
            return reply

        try:
            reply['error'] = None
            func_desc = self.functions_dict[request['method']]
            func = func_desc.func

            try:
                reply['result'] = self.call_function(func_desc.name, func,
                        func_desc, *request['params'])
            except JsonRpcError as e:
                reply['error'] = e.to_json()
                reply['result'] = None
            except Exception as e:
                reply['error'] = "Internal error"
                reply['result'] = None

            return reply
        except Exception as e:
            print(e)
            reply['error'] = "Method execution failed: %s" % (request['method'])
            return reply

class RpcError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "ERROR: " + str(msg)

class RpcClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.req_id = 1
        self.recv_buf = ''

    def build_rpc_call(self, method, *params):
        request = {}
        request['id'] = self.req_id
        self.req_id = self.req_id + 1
        request['method'] = method
        request['params'] = params

        return request

    def rpc_call_raw(self, json_data):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))

        json_data += "\n"
        sock.sendall(json_data.encode('utf-8'))

        data = sock.recv(4096)
        self.recv_buf += data.decode('utf-8')
        while not "\n" in self.recv_buf:
            data = sock.recv(4096)
            self.recv_buf += data.decode('utf-8')

        sock.close()

        json_reply = self.recv_buf
        self.recv_buf = ''

        return json_reply

    def rpc_call(self, method, *params):
        json_data = json.dumps(self.build_rpc_call(method, *params))

        json_reply = self.rpc_call_raw(json_data)

        reply = json.loads(json_reply)

        if 'error' in reply and reply['error']:
            raise RpcError(reply['error'])

        return reply['result']
