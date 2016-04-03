from builtins import str

import os
import sys
import json
import socket
import traceback

json_types = ['int', 'bool', 'float', 'string', 'array', 'hash', 'base64']

class JsonRpcError(Exception):
    def __init__(self, msg):
        self.msg = msg
        self.name = type(self).__name__

    def __str__(self):
        return '%s: %s' % (self.name, self.msg)

    def to_dict(self):
        error = {}

        error['name'] = self.name
        error['message'] = self.msg

        return error

class JsonRpcInvalidRequest(JsonRpcError):
    def __init__(self, msg):
        self.msg = msg
        self.name = 'InvalidRequest'

class JsonRpcParamError(JsonRpcInvalidRequest):
    def __init__(self, function_name, expected_count, real_count):
        self.msg = "Expected %d parameters for '%s' but got %d" % (expected_count, function_name, real_count)
        self.name = 'ParamError'

class JsonRpcTypeError(JsonRpcInvalidRequest):
    def __init__(self, function_name, param_name, expected_type, real_type):
        self.msg = "%s: Expected type '%s' of parameter '%s' but got value of type '%s'" % (function_name, expected_type, param_name, real_type)
        self.name = 'TypeError'

class JsonRpcInternalError(JsonRpcError):
    def __init__(self, msg):
        self.msg = msg
        self.name = 'InternalError'

class JsonEnumType(object):
    """
    Self-describing enum types
    """
    def __init__(self, name, description, start=0):
        self.curvalue = start

        if not name[0].isupper():
            raise ValueError("The Name of a custom type has to start with an upper-case letter")

        self.name = name
        self.typ = 'enum'
        self.description = description
        self.values = []

    def add_value(self, name, description):
        value = {}

        value['name'] = name
        value['description'] = description
        value['intvalue'] = self.curvalue
        self.curvalue += 1

        self.values.append(value)

    def resolve(self, value):
        return None

    def to_dict(self):
        d = {}

        d['name'] = self.name
        d['type'] = self.typ
        d['description'] = self.description
        d['values'] = self.values

        return d

class JsonHashType(object):
    """
    Self-describing hashes
    """
    def __init__(self, name, description):
        if not name[0].isupper():
            raise ValueError("The Name of a custom type has to start with an upper-case letter")

        self.name = name
        self.typ = 'hash'
        self.description = description
        self.fields = []

    def add_field(self, name, typ, description):
        if not typ in json_types and not result_type[0].isupper():
            raise ValueError("Invalid JSON-RPC type: %s" % (typ))

        field = {}

        field['name'] = name
        field['type'] = typ
        field['description'] = description

        self.fields.append(field)

    def to_dict(self):
        d = {}

        d['name'] = self.name
        d['type'] = self.typ
        d['description'] = self.description

        d['fields'] = self.fields

        return d

class RpcFunction(object):
    """
    Description of a function exposed as RPC
    """
    def __init__(self, func, name, description, result_type, result_desc):
        if not result_type in json_types and not result_type[0].isupper():
            raise ValueError("Invalid JSON-RPC type: %s" % (result_type))

        if not callable(func):
            raise ValueError("TypeError: Parameter func must be a function or another callable")

        self.func = func
        self.name = name
        self.description = description
        self.result_type = result_type
        self.result_desc = result_desc

        self.params = []

        self.type_checks_enabled = True

    def add_param(self, typ, name, description):
        if not typ in json_types and not typ[0].isupper():
            raise ValueError("Invalid JSON-RPC type: %s" % (typ))

        param = {'name': name, 'type': typ, 'description': description}
        self.params.append(param)

    def to_dict(self):
        d = {}

        d['name'] = self.name
        d['description'] = self.description
        d['result_type'] = self.result_type
        d['result_desc'] = self.result_desc

        params = []

        for p in self.params:
            param = {}

            param['name'] = p['name']
            param['description'] = p['description']
            param['type'] = p['type']

            params.append(param)

        d['params'] = params

        return d

class RpcProcessor(object):
    """
    A JSON-RPC server that is capable of describing all its RPC functions to the client
    """
    def __init__(self):
        self.functions = []
        self.functions_dict = {}

        self.custom_types = []
        self.custom_types_dict = {}

        self.description = ''

        self.builtins = {}
        self.builtins['__describe_service'] = self.describe_service
        self.builtins['__describe_functions'] = self.describe_functions
        self.builtins['__describe_custom_types'] = self.describe_custom_types

    def add_custom_type(self, custom_type):
        if type(custom_type) != JsonEnumType and type(custom_type) != JsonHashType:
            raise ValueError("Custom type must be of class JsonEnumType or JsonHashType")

        if custom_type.name in self.custom_types_dict.keys():
            raise ValueError("Custom type with name '%s' already exists!",
                    custom_type.name)

        self.custom_types.append(custom_type)
        self.custom_types_dict[custom_type.name] = custom_type

    def add_function(self, func):
        if func.name in self.functions_dict:
            raise ValueError("Another function of the name '%s' is already registered" % (func.name))

        if func.result_type[0].isupper() and not func.result_type in self.custom_types_dict.keys():
            raise ValueError("Unknown custom type: '%s'" % (func.result_type))

        for param in func.params:
            if not param['type'][0].isupper(): continue

            if not param['type'] in self.custom_types_dict.keys():
                raise ValueError("Unknown custom type: '%s'" % (param['type']))

        self.functions.append(func)
        self.functions_dict[func.name] = func

    def describe_service(self):
        return self.description

    def describe_functions(self):
        return [function.to_dict() for function in self.functions]

    def describe_custom_types(self):
        return [custom_type.to_dict() for custom_type in self.custom_types]

    def call_function(self, name, func, func_desc, *params):
        """
        Executes the actual function. Can be overridden for concurrent execution e.g.
        """
        return func(*params)

    def check_request_types(self, func, params):
        if len(params) != len(func.params):
            raise JsonRpcParamError(func.name, len(func.params), len(params))

        json2py = {'bool': 'bool', 'int': 'int', 'float': 'float', 'string':
                'str', 'array': 'list', 'hash': 'dict', 'base64': 'str'}

        py2json = {'bool': 'bool', 'int': 'int', 'float': 'float', 'str':
                'string', 'list': 'array', 'dict': 'hash'}

        i = 0

        for p in func.params:
            if type(params[i]).__name__ != json2py[p['type']]:
                real_type = py2json[type(params[i]).__name__]
                raise JsonRpcTypeError(func.name, p['name'], p['type'], real_type)

            i += 1

    def process_request(self, message):
        reply = {}
        request = {}

        reply['result'] = None

        try:
            request = json.loads(message)
        except ValueError:
            reply['id'] = -1
            error = JsonRpcInvalidRequest("Received invalid JSON")
            reply['error'] = error.to_dict()
            return reply

        if not 'id' in request.keys():
            reply['id'] = -1
            error = JsonRpcInvalidRequest("Field 'id' missing in request")
            reply['error'] = error.to_dict()
            return reply

        if not isinstance(request['id'], int):
            reply['id'] = -1
            error = JsonRpcInvalidRequest("Field 'id' must contain an integer value")
            reply['error'] = error.to_dict()
            return reply

        reply['id'] = request['id']

        if not 'method' in request.keys():
            error = JsonRpcInvalidRequest("Field 'method' missing in request")
            reply['error'] = error.to_json()
            return reply

        if not isinstance(request['method'], str):
            error = JsonRpcInvalidRequest("Field 'method' must contain a string value")
            reply['error'] = error.to_dict()
            return reply

        if not 'params' in request.keys():
            error = JsonRpcInvalidRequest("Field 'params' missing in request")
            reply['error'] = error.to_dict()
            return reply

        if not isinstance(request['params'], list):
            error = JsonRpcInvalidRequest("Field 'params' must contain an array")
            reply['error'] = error.to_dict()
            return reply

        # check for builtins
        if request['method'] in self.builtins:
            reply['result'] = self.builtins[request['method']]()
            return reply

        if not request['method'] in self.functions_dict:
            error = JsonRpcInvalidRequest("No such method: %s. Call '__describe_functions' to get details on available function calls" % (request['method']))
            reply['error'] = error.to_dict()
            return reply

        try:
            reply['error'] = None
            func_desc = self.functions_dict[request['method']]
            func = func_desc.func

            try:
                if func_desc.type_checks_enabled:
                    self.check_request_types(func_desc, request['params'])

                reply['result'] = self.call_function(func_desc.name, func,
                        func_desc, *request['params'])
            except JsonRpcError as e:
                reply['error'] = e.to_dict()
                reply['result'] = None
            except Exception as e:
                traceback.print_exc()
                error = JsonRpcInternalError("Internal error")
                reply['error'] = error.to_dict()
                reply['result'] = None

            return reply
        except Exception as e:
            traceback.print_exc()
            error = JsonRpcInternalError("Method execution failed: %s" % (request['method']))
            reply['error'] = error.to_dict()
            return reply

class RpcError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "ERROR: " + str(self.msg)

class RpcClient(object):
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
