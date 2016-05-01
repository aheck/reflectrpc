from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import json
import traceback

json_types = ['int', 'bool', 'float', 'string', 'array', 'hash', 'base64']

def isstring(value):
    return type(value).__name__ in ['str', 'unicode']

class JsonRpcError(Exception):
    """
    Generic JSON-RPC error class

    All exceptions that are to be serialized and sent back to the user over
    JSON-RPC have to derive from this class. All exceptions not derived from
    this class will be suppressed for security reasons.

    Example:
        The JSON representation of this error looks like this::

            {"name": "JsonRpcError", "message": "Your error message"}
    """
    def __init__(self, msg):
        """
        Constructor

        Args:
            msg (str): Error message
        """
        self.msg = msg
        self.name = type(self).__name__

    def __str__(self):
        return '%s: %s' % (self.name, self.msg)

    def to_dict(self):
        """
        Convert the error to a dictionary

        Returns:
            dict: Dictionary representing this error
        """
        error = {}

        error['name'] = self.name
        error['message'] = self.msg

        return error

class JsonRpcInvalidRequest(JsonRpcError):
    """
    JSON-RPC error class for invalid requests

    Example:
        The JSON representation of this error looks like this::

            {"name": "InvalidRequest", "message": "Your error message"}
    """
    def __init__(self, msg):
        """
        Constructor

        Args:
            msg (str): Error message
        """
        self.msg = msg
        self.name = 'InvalidRequest'

class JsonRpcParamError(JsonRpcInvalidRequest):
    """
    JSON-RPC error class for requests with wrong number of parameters

    Example:
        The JSON representation of this error looks like this::

            {"name": "ParamError", "message": "Expected [expected_count] parameters for '[function_name]' but got [real_count]""}
    """
    def __init__(self, function_name, expected_count, real_count):
        """
        Constructor

        Args:
            function_name (str): Name of the function the user tried to call
            expected_count (int): Expected number of parameters
            real_count (int): Number of parameters actually received
        """
        self.msg = "Expected %d parameters for '%s' but got %d" % (expected_count, function_name, real_count)
        self.name = 'ParamError'

class JsonRpcTypeError(JsonRpcInvalidRequest):
    """
    Generic JSON-RPC error class for requests with parameters of invalid type

    Example:
        The JSON representation of this error looks like this::

            {"name": "TypeError", "message": "Your error message"}
    """
    def __init__(self, msg):
        """
        Constructor

        Args:
            msg (str): Error message
        """
        self.msg = msg
        self.name = 'TypeError'

class JsonRpcParamTypeError(JsonRpcInvalidRequest):
    """
    JSON-RPC error class for requests with parameters of invalid type

    Example:
        The JSON representation of this error looks like this::

            {"name": "TypeError", "message": "[function_name]: Expected value of type '[param_name]' for parameter '[expected_type]' but got value of type '[real_type]'"}
    """
    def __init__(self, function_name, param_name, expected_type, real_type):
        """
        Constructor

        Args:
            function_name (str): Name of the function the user tried to call
            param_name (str): Name of the parameter
            expected_type (str): Name of the type this parameter expects
            real_type (str): Type of the value the user actually passed
        """
        self.function_name = function_name
        self.param_name = param_name
        self.expected_type = expected_type
        self.real_type = real_type

        self.msg = "%s: Expected value of type '%s' for parameter '%s' but got value of type '%s'" % (function_name, expected_type, param_name, real_type)
        self.name = 'TypeError'

class JsonRpcInternalError(JsonRpcError):
    """
    JSON-RPC error class for internal errors

    This error is used when the details of the error are to be hidden from the
    user for security reasons (e.g. when an exception is raised which is not
    derived from JsonRpcError).

    Example:
        The JSON representation of this error looks like this::

            {"name": "InternalError", "message": "Your error message"}
    """
    def __init__(self, msg):
        self.msg = msg
        self.name = 'InternalError'

class InvalidEnumValueError(Exception):
    def __init__(self, name, expected_type, value):
        self.name = name
        self.expected_type = expected_type
        self.value = value

class InvalidEnumTypeError(Exception):
    def __init__(self, name, real_type):
        self.name = name
        self.real_type = real_type

class InvalidNamedHashError(Exception):
    def __init__(self, name, expected_type, real_type):
        self.name = name
        self.expected_type = expected_type
        self.real_type = real_type

class InvalidPrimitiveTypeError(Exception):
    def __init__(self, name, expected_type, real_type):
        self.name = name
        self.expected_type = expected_type
        self.real_type = real_type

class JsonEnumType(object):
    """
    Self-describing enum types

    An enum is a list of named integers. Translation between integer value and
    string names is supported by this class as well as validation of integer
    and string values to check if they are valid values of an enum.
    """
    def __init__(self, name, description, start=0):
        """
        Constructor

        Args:
            name (str): Name of the enum type, has to start with an upper-case letter
            description (str): Description of this enum type
            start (int): enum integer values are assigned starting from this value

        Raises:
            ValueError: If name doesn't start with an upper-case letter
        """
        self.startvalue = start
        self.nextvalue = start

        if not name[0].isupper():
            raise ValueError("The Name of a custom type has to start with an upper-case letter")

        self.name = name
        self.typ = 'enum'
        self.description = description
        self.values = []

    def validate(self, value):
        """
        Check if a string or integer value is a valid value for this enum

        Args:
            value (int|str): Value to check

        Returns:
            bool: True if value is valid, False if not
        """
        result = self.resolve_to_intvalue(value)

        if result == None:
            return False

        return True

    def add_value(self, name, description):
        """
        Add a new value to the enum

        Args:
            name (str): String name of the value
            description (str): Description of this value
        """
        value = {}

        value['name'] = name
        value['description'] = description
        value['intvalue'] = self.nextvalue
        self.nextvalue += 1

        self.values.append(value)

    def resolve_name(self, name):
        """
        Resolves a string name to its integer value

        Args:
            name (str): String name of a value

        Returns:
            int: Integer value of name on success
            None: If name is not a valid value for this enum

        Raises:
            ValueError: If name is not a string
        """
        if not isstring(name):
            raise ValueError("'name' must be a string but is '%s'" % (type(name).__name__))

        for v in self.values:
            if v['name'] == name: return v['intvalue']

        return None

    def resolve_intvalue(self, intvalue):
        """
        Resolves an integer value to its string name

        Args:
            intvalue (int): Integer value to resolve

        Returns:
            str: Name of intvalue on success
            None: If intvalue is not a valid value for this enum

        Raises:
            ValueError: If intvalue is not an integer
        """
        if type(intvalue).__name__ != 'int':
            raise ValueError("'intvalue' must be of type 'int'")

        for v in self.values:
            if v['intvalue'] == intvalue: return v['name']

        return None

    def resolve_to_name(self, value):
        """
        Resolves an integer value or string name to the corresponding string name

        Args:
            value (int|str): Integer value or string name

        Returns:
            str: String name if value is a valid enum value
            None: If value is not a valid enum value

        Raises:
            ValueError: If value is neither interger or string
        """
        if isstring(value):
            if self.resolve_name(value) != None:
                return value
        elif type(value).__name__ == 'int':
            return self.resolve_intvalue(value)
        else:
            raise ValueError("'value' must be either string or int")

        return None

    def resolve_to_intvalue(self, value):
        """
        Resolves an integer value or string name to the corresponding integer value

        Args:
            value (int|str): Integer value or string name

        Returns:
            int: Integer value if value is a valid enum value
            None: If value is not a valid enum value

        Raises:
            ValueError: If value is neither interger or string
        """
        if isstring(value):
            return self.resolve_name(value)
        elif type(value).__name__ == 'int':
            if value >= self.startvalue and value < self.nextvalue:
                return value
        else:
            raise ValueError("'value' must be either string or int")

        return None

    def to_dict(self):
        """
        Convert the enum to a dictionary

        Returns:
            dict: Dictionary representing this enum type
        """
        d = {}

        d['name'] = self.name
        d['type'] = self.typ
        d['description'] = self.description
        d['values'] = self.values

        return d

class JsonHashType(object):
    """
    Self-describing named hashes

    A named hash is a hash with a description of its members and their types
    """
    def __init__(self, name, description):
        """
        Constructor

        Args:
            name (str): Name of the hash type to be defined. Must start with an upper-case letter
            description (str): Description of this named hash type

        Raises:
            ValueError: If name does not start with an upper-case letter
        """
        if not name[0].isupper():
            raise ValueError("The Name of a custom type has to start with an upper-case letter")

        self.name = name
        self.typ = 'hash'
        self.description = description
        self.fields = []
        self.fields_dict = {}
        self.fieldnames = []

    def add_field(self, name, typ, description):
        """
        Add a new field to the named hash

        Args:
            name (str): Name of the field
            typ (str): Type of the field (JSON type or enum or named hash)
            description (str): Description of this field

        Raises:
            ValueError: If typ is not a valid type
        """
        if not typ in json_types and not typ[0].isupper():
            raise ValueError("Invalid JSON-RPC type: %s" % (typ))

        field = {}

        field['name'] = name
        field['type'] = typ
        field['description'] = description

        self.fields.append(field)
        self.fields_dict[name] = field
        self.fieldnames.append(name)

    def to_dict(self):
        """
        Convert the named hash to a dictionary

        Returns:
            dict: Dictionary representing this enum type
        """
        d = {}

        d['name'] = self.name
        d['type'] = self.typ
        d['description'] = self.description

        d['fields'] = self.fields

        return d

class RpcFunction(object):
    """
    Description of a function exposed as Remote Procedure Call
    """
    def __init__(self, func, name, description, result_type, result_desc):
        """
        Constructor

        Args:
            func (Callable): A callable to be exposed as RPC
            name (str): Function name under which to expose func
            description (str): Description of the function
            result_type (str): Type of the return value
            result_desc (str): Description of the return value

        Raises:
            ValueError: If result_type is an invalid type or func is not a callable
        """
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
        """
        Add a parameter to the function description

        Args:
            typ (str): Type of the parameter
            name (str): Name of the parameter
            description (str): Description of the parameter

        Raises:
            ValueError: If typ is not a valid type
        """
        if not typ in json_types and not typ[0].isupper():
            raise ValueError("Invalid JSON-RPC type: %s" % (typ))

        param = {'name': name, 'type': typ, 'description': description}
        self.params.append(param)

    def to_dict(self):
        """
        Convert the function description to a dictionary

        Returns:
            dict: Dictionary representing this error
        """
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
    A JSON-RPC server that is capable of describing all of its RPC functions to the client
    """
    def __init__(self):
        """
        Constructor
        """
        self.functions = []
        self.functions_dict = {}

        self.custom_types = []
        self.custom_types_dict = {}

        self.description = {
                'name': '',
                'description': '',
                'version': '',
                'custom_fields': {}
        }

        self.builtins = {}
        self.builtins['__describe_service'] = self.describe_service
        self.builtins['__describe_functions'] = self.describe_functions
        self.builtins['__describe_custom_types'] = self.describe_custom_types

        self.named_hash_validation = False

        self.json2py = {'bool': 'bool', 'int': 'int', 'float': 'float', 'string':
                'str', 'array': 'list', 'hash': 'dict', 'base64': 'str'}

        self.py2json = {'bool': 'bool', 'int': 'int', 'float': 'float', 'str':
                'string', 'list': 'array', 'dict': 'hash'}

    def set_description(self, name, description, version, custom_fields = {}):
        """
        Set the description of this RPC service

        Args:
            name (str): Name of the service
            description (str): Description of the service
            version (str): Version of the service
            custom_fields (dict): A dict with user-defined fields
        """
        self.description['name'] = name
        self.description['description'] = description
        self.description['version'] = version
        self.description['custom_fields'] = custom_fields

    def add_custom_type(self, custom_type):
        """
        Make a custom type (enum or named hash) known to the RpcProcessor

        Args:
            custom_type (JsonEnumType|JsonHashType): Enum or named hash

        Raises:
            ValueError: If custom_type is neither a JsonEnumType nor a JsonHashType or custom_type is already registered
        """
        if type(custom_type) != JsonEnumType and type(custom_type) != JsonHashType:
            raise ValueError("Custom type must be of class JsonEnumType or JsonHashType")

        if custom_type.name in self.custom_types_dict.keys():
            raise ValueError("Custom type with name '%s' already exists!",
                    custom_type.name)

        self.custom_types.append(custom_type)
        self.custom_types_dict[custom_type.name] = custom_type

    def enable_named_hash_validation(self):
        """
        Enable validation of the fields of named hashes
        """
        self.named_hash_validation = True

    def disable_named_hash_validation(self):
        """
        Disable validation of the fields of named hashes
        """
        self.named_hash_validation = False

    def add_function(self, func):
        """
        Add a new RPC function to the RpcProcessor

        Args:
            func (RpcFunction): Description object for the new function

        Raises:
            ValueError: If a function of this name is already registered or unknown types are referenced in func
        """
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
        """
        Return the self-description of this RPC service

        Returns:
            dict: Description of this service
        """
        return self.description

    def describe_functions(self):
        """
        Describe the functions exposed by this RPC service

        Returns:
            list: Description of all functions registered to this RpcProcessor
        """
        return [function.to_dict() for function in self.functions]

    def describe_custom_types(self):
        """
        Describe the custom types exposed by this RPC service

        Returns:
            list: Description of all custom types registered to this RpcProcessor
        """
        return [custom_type.to_dict() for custom_type in self.custom_types]

    def call_function(self, name, func, func_desc, *params):
        """
        Execute the actual function
        """
        return func(*params)

    def check_request_types(self, func, params):
        """
        Check the types of the parameters passed by a JSON-RPC call

        Args:
            func (RpcFunction): Description of the called function
            params (list): Parameters passed in the request

        Raises:
            JsonRpcTypeError: If a parameter type is invalid
            JsonRpcParamTypeError: If a parameter type is invalid
        """
        if len(params) != len(func.params):
            raise JsonRpcParamError(func.name, len(func.params), len(params))

        i = 0

        for p in func.params:
            value = params[i]
            try:
                self.check_param_type(p['name'], p['type'], value)
            except InvalidEnumValueError as e:
                raise JsonRpcTypeError("%s: '%s' is not a valid value for parameter '%s' of enum type '%s'"
                        % (func.name, e.value, e.name, e.expected_type))
            except InvalidEnumTypeError as e:
                raise JsonRpcTypeError("%s: Enum parameter '%s' requires a value of type 'int' or 'string' but type was '%s'"
                        % (func.name, e.name, e.real_type))
            except InvalidNamedHashError as e:
                raise JsonRpcTypeError("%s: Named hash parameter '%s' of type '%s' requires a hash value but got '%s'"
                        % (func.name, e.name, e.expected_type, e.real_type))
            except InvalidPrimitiveTypeError as e:
                raise JsonRpcParamTypeError(func.name, e.name, e.expected_type, e.real_type)

            # validate named hashes if named has validation is enabled
            if self.named_hash_validation and self.__is_named_hash_type(p['type']):
                named_hash = self.custom_types_dict[p['type']]

                for fieldname in named_hash.fieldnames:
                    if fieldname not in value:
                        raise JsonRpcTypeError("%s: Named hash parameter '%s' of type '%s': Missing field '%s'" % (func.name, p['name'], p['type'], fieldname))

                    try:
                        self.check_param_type(fieldname, named_hash.fields_dict[fieldname]['type'], value[fieldname])
                    except InvalidEnumValueError as e:
                        raise JsonRpcTypeError("%s: Named hash parameter '%s' of type '%s' has invalid field '%s': '%s' is not a valid value" % (func.name, p['name'], named_hash.name, fieldname, e.value))
                    except InvalidEnumTypeError as e:
                        raise JsonRpcTypeError("%s: Named hash parameter '%s' of type '%s' has invalid field '%s': Value must be of type 'int' or 'string' but type was '%s'" % (func.name, p['name'], named_hash.name, fieldname, e.real_type))
                    except InvalidNamedHashError as e:
                        raise JsonRpcTypeError("%s: Named hash parameter '%s' of type '%s' requires a hash value but got '%s'" % (func.name, e.name, e.expected_type, e.real_type))
                    except InvalidPrimitiveTypeError as e:
                        raise JsonRpcTypeError("%s: Named hash parameter '%s' of type '%s' has invalid field '%s': Expected %s but got %s" % (func.name, p['name'], p['type'], fieldname, e.expected_type, e.real_type))

            i += 1

    def check_param_type(self, name, declared_type, value):
        """
        Check the type of a single parameter

        Args:
            name (string): Name of the parameter
            declared_type (string): Type that we expect from the caller
            value (any): Actual value that was passed by the caller
        """
        real_type = type(value).__name__

        # workaround for Python 2.7
        if real_type == 'unicode':
            real_type = 'str'

        # custom type?
        if declared_type[0].isupper():
            typeobj = self.custom_types_dict[declared_type]

            if type(typeobj).__name__ == 'JsonEnumType':
                try:
                    if not typeobj.validate(value):
                        raise InvalidEnumValueError(name, declared_type, str(value))
                except ValueError:
                    raise InvalidEnumTypeError(name, self.py2json[real_type])
            elif type(typeobj).__name__ == 'JsonHashType':
                if self.py2json[real_type] != 'hash':
                    raise InvalidNamedHashError(name, declared_type, self.py2json[real_type])
        # primitive type?
        elif real_type != self.json2py[declared_type]:
            raise InvalidPrimitiveTypeError(name, declared_type, self.py2json[real_type])

    def process_request(self, message):
        """
        Process a JSON-RPC request

        Validates the JSON-RPC request and executes the RPC function in case the
        request is valid. Errors are reported to the user. Exceptions that are
        not derived from JsonRpcError are reported as internal errors with no
        further explanation for security reasons.

        Args:
            message (str): The JSON-RPC request sent by the client

        Returns:
            dict: JSON-RPC reply for the client
        """
        reply = {}
        request = {}

        reply['result'] = None
        # Notification requests expect no answer
        notify_request = False

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

        if request['id'] == None:
            notify_request = True
        else:
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
                if notify_request:
                    try:
                        if func_desc.type_checks_enabled:
                            self.check_request_types(func_desc, request['params'])
                        self.call_function(func_desc.name, func, func_desc, *request['params'])
                    except Exception as e:
                        traceback.print_exc()

                    return None

                if func_desc.type_checks_enabled:
                    self.check_request_types(func_desc, request['params'])

                if notify_request:
                    try:
                        self.call_function(func_desc.name, func, func_desc, *request['params'])
                    except:
                        pass

                    return None

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

    def __is_named_hash_type(self, typename):
        """
        Check if a typename references a Named Hash

        Args:
            typename (str): Name of the type to check

        Returns:
            bool: True if it is a Named Hash, False otherwise
        """
        if typename[0].isupper():
            typeobj = self.custom_types_dict[typename]

            if type(typeobj).__name__ == 'JsonHashType':
                return True

        return False

    def __is_enum_type(self, typename):
        """
        Check if a typename references an Enum

        Args:
            typename (str): Name of the type to check

        Returns:
            bool: True if it is an Enum, False otherwise
        """
        if typename[0].isupper():
            typeobj = self.custom_types_dict[typename]

            if type(typeobj).__name__ == 'JsonEnumType':
                return True

        return False
