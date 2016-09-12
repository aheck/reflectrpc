#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import sys
import json
import unittest

sys.path.append('..')

from reflectrpc import RpcProcessor
from reflectrpc import RpcFunction
from reflectrpc import JsonRpcError
from reflectrpc import JsonEnumType
from reflectrpc import JsonHashType

def test_function():
    return True

def echo(msg):
    return msg

def add(a, b):
    return int(a) + int(b)

def echo_enum(a):
    return a

notify_was_called = False

def notify():
    global notify_was_called
    notify_was_called = True

def authcheck(rpcinfo):
    reply = 'Authenticated: %s; Username: %s' % (rpcinfo['authenticated'], rpcinfo['username'])
    return reply

def echo_array(a):
    return a

def echo_hash(a):
    return a

def internal_error():
    raise ValueError("This should not be visible to the client")

def json_error():
    raise JsonRpcError("User error")

class TestMethod(object):
    def __init__(self):
        self.testvar = False

    def echo(self, message):
        return message

    def change_variable(self):
        self.testvar = True

class RpcProcessorTests(unittest.TestCase):
    def test_execute_basic_rpc_request(self):
        rpc = RpcProcessor()

        test_func = RpcFunction(test_function, 'test', 'Returns true',
                'bool', 'Should be true')

        rpc.add_function(test_func)
        reply = rpc.process_request('{"method": "test", "params": [], "id": 1}')
        self.assertEqual(reply['error'], None)
        self.assertTrue(reply['result'])

    def test_describe_functions(self):
        rpc = RpcProcessor()

        echo_func = RpcFunction(echo, 'echo', 'Returns what it was given',
                'string', 'Same value as the first parameter')
        echo_func.add_param('string', 'message', 'Message to send back')

        rpc.add_function(echo_func)
        reply = rpc.process_request('{"method": "__describe_functions", "params": [], "id": 1}')

        expected = [{
                    'name': 'echo',
                    'description': 'Returns what it was given',
                    'result_type': 'string',
                    'result_desc': 'Same value as the first parameter',
                    'params': [{'name': 'message', 'type': 'string',
                        'description': 'Message to send back'}]
        }]
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], expected)

        add_func = RpcFunction(add, 'add', 'Returns the sum of the two parameters',
                'int', 'Sum of a and b')
        add_func.add_param('int', 'a', 'First int to add')
        add_func.add_param('int', 'b', 'Second int to add')

        rpc.add_function(add_func)

        reply = rpc.process_request('{"method": "__describe_functions", "params": [], "id": 2}')

        expected = [
                {
                    'name': 'echo',
                    'description': 'Returns what it was given',
                    'result_type': 'string',
                    'result_desc': 'Same value as the first parameter',
                    'params': [{'name': 'message', 'type': 'string',
                        'description': 'Message to send back'}]
                },
                {
                    'name': 'add',
                    'description': 'Returns the sum of the two parameters',
                    'result_type': 'int',
                    'result_desc': 'Sum of a and b',
                    'params': [
                        {'name': 'a', 'type': 'int', 'description': 'First int to add'},
                        {'name': 'b', 'type': 'int', 'description': 'Second int to add'}
                    ]
                }
        ]

        self.assertEqual(reply['result'], expected)

    def test_echo(self):
        rpc = RpcProcessor()

        echo_func = RpcFunction(echo, 'echo', 'Returns what it was given',
                'string', 'Same value as the first parameter')
        echo_func.add_param('string', 'message', 'Message to send back')

        rpc.add_function(echo_func)
        reply = rpc.process_request('{"method": "echo", "params": ["Hello Server"], "id": 1}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], "Hello Server")

    def test_add(self):
        rpc = RpcProcessor()

        add_func = RpcFunction(add, 'add', 'Returns the sum of the two parameters',
                'int', 'Sum of a and b')
        add_func.add_param('int', 'a', 'First int to add')
        add_func.add_param('int', 'b', 'Second int to add')

        rpc.add_function(add_func)
        reply = rpc.process_request('{"method": "add", "params": [4, 5], "id": 1}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], 9)

    def test_notification(self):
        global notify_was_called

        rpc = RpcProcessor()

        notify_func = RpcFunction(notify, 'notify', 'Notification function',
                'bool', 'Does not return because it is a notification')

        rpc.add_function(notify_func)
        self.assertFalse(notify_was_called)
        reply = rpc.process_request('{"method": "notify", "params": [], "id": null}')
        self.assertEqual(None, reply)
        self.assertTrue(notify_was_called)

    def test_double_register_of_function(self):
        rpc = RpcProcessor()

        echo_func = RpcFunction(echo, 'echo', 'Returns what it was given',
                'string', 'Same value as the first parameter')
        add_func = RpcFunction(add, 'echo', 'Returns the sum of the two parameters',
                'int', 'Sum of a and b')

        rpc.add_function(echo_func)
        self.assertRaises(ValueError, rpc.add_function, add_func)

    def test_internal_exception(self):
        rpc = RpcProcessor()

        error_func = RpcFunction(internal_error, 'internal_error', 'Raises ValueError',
                'bool', '')
        rpc.add_function(error_func)

        reply = rpc.process_request('{"method": "internal_error", "params": [], "id": 1}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'InternalError', 'message': 'Internal error'})

    def test_json_exception(self):
        rpc = RpcProcessor()

        error_func = RpcFunction(json_error, 'json_error', 'Raises JsonRpcError',
                'bool', '')
        rpc.add_function(error_func)

        reply = rpc.process_request('{"method": "json_error", "params": [], "id": 1}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'JsonRpcError', 'message': 'User error'})

    def test_wrong_number_of_params(self):
        rpc = RpcProcessor()

        echo_func = RpcFunction(echo, 'echo', 'Returns what it was given',
                'string', 'Same value as the first parameter')
        echo_func.add_param('string', 'message', 'Message to send back')

        rpc.add_function(echo_func)

        reply = rpc.process_request('{"method": "echo", "params": ["Hello Server", 42], "id": 1}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'ParamError', 'message': 'Expected 1 parameters for \'echo\' but got 2'})

        reply = rpc.process_request('{"method": "echo", "params": [], "id": 2}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'ParamError', 'message': 'Expected 1 parameters for \'echo\' but got 0'})

    def test_method_as_rpc(self):
        obj = TestMethod()

        rpc = RpcProcessor()

        echo_func = RpcFunction(obj.echo, 'echo', 'Returns what it was given',
                'string', 'Same value as the first parameter')
        echo_func.add_param('string', 'message', 'Message to send back')

        rpc.add_function(echo_func)

        reply = rpc.process_request('{"method": "echo", "params": ["Hello Server"], "id": 1}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], "Hello Server")

        change_variable_func = RpcFunction(obj.change_variable, 'change_variable',
                'Changes object attribute', 'bool', '')

        rpc.add_function(change_variable_func)

        self.assertFalse(obj.testvar)

        reply = rpc.process_request('{"method": "change_variable", "params": [], "id": 2}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], None)

        self.assertTrue(obj.testvar)

    def test_type_checks(self):
        rpc = RpcProcessor()

        echo_func = RpcFunction(echo, 'echo', 'Returns what it was given',
                'string', 'Same value as the first parameter')
        echo_func.add_param('string', 'message', 'Message to send back')

        rpc.add_function(echo_func)

        add_func = RpcFunction(add, 'add', 'Returns the sum of the two parameters',
                'int', 'Sum of a and b')
        add_func.add_param('int', 'a', 'First int to add')
        add_func.add_param('int', 'b', 'Second int to add')

        rpc.add_function(add_func)

        reply = rpc.process_request('{"method": "echo", "params": [42], "id": 1}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message':'echo: Expected value of type \'string\' for parameter \'message\' but got value of type \'int\''})

        reply = rpc.process_request('{"method": "echo", "params": [[]], "id": 2}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message':'echo: Expected value of type \'string\' for parameter \'message\' but got value of type \'array\''})

        reply = rpc.process_request('{"method": "add", "params": [4, 8.9], "id": 3}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message':'add: Expected value of type \'int\' for parameter \'b\' but got value of type \'float\''})

        reply = rpc.process_request('{"method": "add", "params": [4, {"test": 8}], "id": 3}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message':'add: Expected value of type \'int\' for parameter \'b\' but got value of type \'hash\''})

    def test_enum_types(self):
        enum = JsonEnumType('PhoneType', 'Type of a phone number')
        enum.add_value('HOME', 'Home phone')
        enum.add_value('WORK', 'Work phone')
        enum.add_value('MOBILE', 'Mobile phone')
        enum.add_value('FAX', 'FAX number')

        self.assertRaises(ValueError, enum.resolve_name, 5)
        self.assertRaises(ValueError, enum.resolve_intvalue, 'String')

        self.assertEqual(enum.resolve_name('HOME'), 0)
        self.assertEqual(enum.resolve_name('WORK'), 1)
        self.assertEqual(enum.resolve_name('MOBILE'), 2)
        self.assertEqual(enum.resolve_name('FAX'), 3)
        self.assertEqual(enum.resolve_name('SOMERANDOMSTRING'), None)

        self.assertEqual(enum.resolve_intvalue(0), 'HOME')
        self.assertEqual(enum.resolve_intvalue(1), 'WORK')
        self.assertEqual(enum.resolve_intvalue(2), 'MOBILE')
        self.assertEqual(enum.resolve_intvalue(3), 'FAX')
        self.assertEqual(enum.resolve_intvalue(-1), None)
        self.assertEqual(enum.resolve_intvalue(4), None)
        self.assertEqual(enum.resolve_intvalue(5000), None)

        self.assertRaises(ValueError, enum.resolve_to_intvalue, [])
        self.assertRaises(ValueError, enum.resolve_to_name, [])

        self.assertEqual(enum.resolve_to_intvalue(0), 0)
        self.assertEqual(enum.resolve_to_intvalue('HOME'), 0)
        self.assertEqual(enum.resolve_to_intvalue(1), 1)
        self.assertEqual(enum.resolve_to_intvalue('WORK'), 1)
        self.assertEqual(enum.resolve_to_intvalue(2), 2)
        self.assertEqual(enum.resolve_to_intvalue('MOBILE'), 2)
        self.assertEqual(enum.resolve_to_intvalue(3), 3)
        self.assertEqual(enum.resolve_to_intvalue('FAX'), 3)
        self.assertEqual(enum.resolve_to_intvalue(-1), None)
        self.assertEqual(enum.resolve_to_intvalue(4), None)
        self.assertEqual(enum.resolve_to_intvalue(5000), None)
        self.assertEqual(enum.resolve_to_intvalue('SOMERANDOMSTR'), None)

        self.assertEqual(enum.resolve_to_name(0), 'HOME')
        self.assertEqual(enum.resolve_to_name('HOME'), 'HOME')
        self.assertEqual(enum.resolve_to_name(1), 'WORK')
        self.assertEqual(enum.resolve_to_name('WORK'), 'WORK')
        self.assertEqual(enum.resolve_to_name(2), 'MOBILE')
        self.assertEqual(enum.resolve_to_name('MOBILE'), 'MOBILE')
        self.assertEqual(enum.resolve_to_name(3), 'FAX')
        self.assertEqual(enum.resolve_to_name('FAX'), 'FAX')
        self.assertEqual(enum.resolve_to_intvalue(-1), None)
        self.assertEqual(enum.resolve_to_intvalue(4), None)
        self.assertEqual(enum.resolve_to_intvalue(5000), None)
        self.assertEqual(enum.resolve_to_intvalue('SOMERANDOMSTR'), None)

    def test_type_checks_for_enums(self):
        rpc = RpcProcessor()

        enum = JsonEnumType('PhoneType', 'Type of a phone number')
        enum.add_value('HOME', 'Home phone')
        enum.add_value('WORK', 'Work phone')
        enum.add_value('MOBILE', 'Mobile phone')
        enum.add_value('FAX', 'FAX number')

        rpc.add_custom_type(enum)

        echo_enum_func = RpcFunction(echo_enum, 'echo_enum', 'Returns what it was given',
                'PhoneType', 'Same value as the first parameter')
        echo_enum_func.add_param('PhoneType', 'type', 'Type of phone number')

        rpc.add_function(echo_enum_func)

        reply = rpc.process_request('{"method": "echo_enum", "params": [-1], "id": 1}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError',
            'message':"echo_enum: '-1' is not a valid value for parameter 'type' of enum type 'PhoneType'"})

        reply = rpc.process_request('{"method": "echo_enum", "params": [4], "id": 2}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError',
            'message':"echo_enum: '4' is not a valid value for parameter 'type' of enum type 'PhoneType'"})

        reply = rpc.process_request('{"method": "echo_enum", "params": ["BLABLA"], "id": 3}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError',
            'message':"echo_enum: 'BLABLA' is not a valid value for parameter 'type' of enum type 'PhoneType'"})

        reply = rpc.process_request('{"method": "echo_enum", "params": [3], "id": 4}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], 3)

        reply = rpc.process_request('{"method": "echo_enum", "params": ["MOBILE"], "id": 5}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], 'MOBILE')

    def test_basic_type_checks_for_named_hashes(self):
        rpc = RpcProcessor()

        address_type = JsonHashType('Address', 'Street address')
        address_type.add_field('firstname', 'string', 'First name')
        address_type.add_field('lastname', 'string', 'Last name')
        address_type.add_field('street1', 'string', 'First address line')
        address_type.add_field('zipcode', 'int', 'Zip code')
        address_type.add_field('city', 'string', 'City')

        rpc.add_custom_type(address_type)

        echo_hash_func = RpcFunction(echo_hash, 'echo_hash', 'Returns what it was given',
                'hash', 'Same value as the first parameter')
        echo_hash_func.add_param('Address', 'address', 'Address hash')

        rpc.add_function(echo_hash_func)

        reply = rpc.process_request('{"method": "echo_hash", "params": ["String"], "id": 1}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message':
            "echo_hash: Named hash parameter 'address' of type 'Address' requires a hash value but got 'string'"})

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"firstname": "first", "lastname": "last", "street1": "", "zipcode": 56732, "city": ""}], "id": 2}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], {
            'firstname': 'first',
            'lastname': 'last',
            'street1': '',
            'zipcode': 56732,
            'city': '',
        })

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"firstname": "first", "lastname": "test", "street1": "", "zipcode": 56732, "city": "", "number": 42}], "id": 3}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError',
            'message': "echo_hash: Named hash parameter 'address' of type 'Address': Unknown field 'number'"
        })

    def test_type_checks_for_fields_of_named_hashes(self):
        rpc = RpcProcessor()

        custom_type = JsonHashType('CustomHash', 'Dummy named hash for testing')
        custom_type.add_field('boolfield', 'bool', 'Some bool')
        custom_type.add_field('stringfield', 'string', 'Some string')
        custom_type.add_field('intfield', 'int', 'Some integer')
        custom_type.add_field('floatfield', 'float', 'Some float')
        custom_type.add_field('arrayfield', 'array', 'City')
        custom_type.add_field('hashfield', 'hash', 'City')

        rpc.add_custom_type(custom_type)
        rpc.enable_named_hash_validation()

        echo_hash_func = RpcFunction(echo_hash, 'echo_hash', 'Returns what it was given',
                'hash', 'Same value as the first parameter')
        echo_hash_func.add_param('CustomHash', 'custom_hash', 'Some custom hash instance')

        rpc.add_function(echo_hash_func)

        # Call with an empty hash should get us an error mentioning the first missing field
        reply = rpc.process_request('{"method": "echo_hash", "params": [{}], "id": 1}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError',
            'message': "echo_hash: Named hash parameter 'custom_hash' of type 'CustomHash': Missing field 'boolfield'"
        })

        # Call with an invalid field should return the corresponding error
        reply = rpc.process_request('{"method": "echo_hash", "params": [{"boolfield": true, "stringfield": 5, "intfield": 5, "floatfield": 5.5, "arrayfield": [], "hashfield": {}}], "id": 2}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_hash: Expected value of type 'string' for parameter 'custom_hash.stringfield' but got value of type 'int'"})

        # Call with a valid hash should return the same hash without error
        reply = rpc.process_request('{"method": "echo_hash", "params": [{"boolfield": true, "stringfield": "test", "intfield": 5, "floatfield": 5.5, "arrayfield": [], "hashfield": {}}], "id": 3}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], {"boolfield": True, "stringfield": "test", "intfield": 5, "floatfield": 5.5, "arrayfield": [], "hashfield": {}})

    def test_type_checks_enums_in_named_hashes(self):
        rpc = RpcProcessor()

        enum = JsonEnumType('PhoneType', 'Type of a phone number')
        enum.add_value('HOME', 'Home phone')
        enum.add_value('WORK', 'Work phone')
        enum.add_value('MOBILE', 'Mobile phone')
        enum.add_value('FAX', 'FAX number')

        rpc.add_custom_type(enum)

        custom_hash = JsonHashType('CustomHash', 'Dummy named hash for testing')
        custom_hash.add_field('phonetype', 'PhoneType', 'Type of phone number')

        rpc.add_custom_type(custom_hash)

        echo_hash_func = RpcFunction(echo_hash, 'echo_hash', 'Returns what it was given',
                'hash', 'Same value as the first parameter')
        echo_hash_func.add_param('CustomHash', 'custom_hash', 'Some custom hash instance')

        rpc.add_function(echo_hash_func)
        rpc.enable_named_hash_validation()

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"phonetype": "TEST"}], "id": 1}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_hash: 'TEST' is not a valid value for parameter 'custom_hash.phonetype' of enum type 'PhoneType'"})

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"phonetype": []}], "id": 2}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_hash: Enum parameter 'custom_hash.phonetype' requires a value of type 'int' or 'string' but type was 'array'"})

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"phonetype": "HOME"}], "id": 3}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], {'phonetype': 'HOME'})

    def test_enum_type_check_in_add_function(self):
        rpc = RpcProcessor()

        echo_enum_func = RpcFunction(echo_enum, 'echo_enum', '', 'PhoneType', '')
        self.assertRaises(ValueError, rpc.add_function, echo_enum_func)

        echo_enum_func = RpcFunction(echo_enum, 'echo_enum', '', 'int', '')
        echo_enum_func.add_param('PhoneType', 'phonetype', '')
        self.assertRaises(ValueError, rpc.add_function, echo_enum_func)

        rpc = RpcProcessor()

        echo_enum_func = RpcFunction(echo_enum, 'echo_enum', '', 'PhoneType', '')
        enum = JsonEnumType('PhoneType', 'Type of a phone number')
        rpc.add_custom_type(enum)

        try:
            rpc.add_function(echo_enum_func)
        except ValueError:
            self.fail("add_function raised unexpected exception!")

        rpc = RpcProcessor()

        echo_enum_func = RpcFunction(echo_enum, 'echo_enum', '', 'int', '')
        echo_enum_func.add_param('PhoneType', 'phonetype', '')
        enum = JsonEnumType('PhoneType', 'Type of a phone number')
        rpc.add_custom_type(enum)

        try:
            rpc.add_function(echo_enum_func)
        except ValueError:
            self.fail("add_function raised unexpected exception!")

    def test_hash_type_check_in_add_function(self):
        rpc = RpcProcessor()

        echo_hash_func = RpcFunction(echo_hash, 'echo_hash', '', 'Address', '')
        self.assertRaises(ValueError, rpc.add_function, echo_hash_func)

        echo_hash_func = RpcFunction(echo_hash, 'echo_hash', '', 'hash', '')
        echo_hash_func.add_param('Address', 'address', '')
        self.assertRaises(ValueError, rpc.add_function, echo_hash_func)

        rpc = RpcProcessor()

        echo_hash_func = RpcFunction(echo_hash, 'echo_hash', '', 'Address', '')
        address = JsonHashType('Address', '')
        rpc.add_custom_type(address)

        try:
            rpc.add_function(echo_hash_func)
        except ValueError:
            self.fail("add_function raised unexpected exception!")

        rpc = RpcProcessor()

        echo_hash_func = RpcFunction(echo_hash, 'echo_hash', '', 'hash', '')
        echo_hash_func.add_param('Address', 'address', '')
        address = JsonHashType('Address', '')
        rpc.add_custom_type(address)

        try:
            rpc.add_function(echo_hash_func)
        except ValueError:
            self.fail("add_function raised unexpected exception!")

    def test_service_description(self):
        rpc = RpcProcessor()

        self.assertEqual(rpc.describe_service(), {'name': '', 'description': '',
            'version': '', 'custom_fields': {}})

        rpc.set_description("Example RPC Service",
                "This is an example service for ReflectRPC", "1.0",
                {'field1': 'test', 'field2': 42})

        expected_desc = {'name': 'Example RPC Service',
                'description': 'This is an example service for ReflectRPC',
                'version': '1.0', 'custom_fields': {'field1': 'test', 'field2': 42}
        }

        self.assertEqual(rpc.describe_service(), expected_desc)

    def test_authcheck(self):
        rpc = RpcProcessor()

        func = RpcFunction(authcheck, 'authcheck', 'Returns rpcinfo content as string',
                'string', 'Returns a string to prove we got the authentication information')
        func.require_rpcinfo()

        rpc.add_function(func)
        rpcinfo = {'authenticated': True, 'username': 'unittest'}
        reply = rpc.process_request('{"method": "authcheck", "params": [], "id": 1}',
                rpcinfo)
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], 'Authenticated: True; Username: unittest')

    def test_nested_named_hash_validation(self):
        rpc = RpcProcessor()

        type1_type = JsonHashType('Type1', 'First type in the hierarchy')
        type1_type.add_field('somestr', 'string', 'Some string')
        type1_type.add_field('type2', 'Type2', 'Embedded Type2')

        type2_type = JsonHashType('Type2', 'Second type in the hierarchy')
        type2_type.add_field('someint', 'int', 'Some int')
        type2_type.add_field('type3', 'Type3', 'Embedded Type3')

        type3_type = JsonHashType('Type3', 'Third type in the hierarchy')
        type3_type.add_field('somebool', 'bool', 'Some bool')

        rpc.add_custom_type(type1_type)
        rpc.add_custom_type(type2_type)
        rpc.add_custom_type(type3_type)

        echo_hash_func = RpcFunction(echo_hash, 'echo_hash', 'Returns what it was given',
                'hash', 'Same value as the first parameter')
        echo_hash_func.add_param('Type1', 'value', 'Type1 one Named Hash')

        rpc.add_function(echo_hash_func)

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"somestr": "mystr"}], "id": 1}')
        self.assertEqual(reply['error'], {'message': "echo_hash: Named hash parameter 'value' of type 'Type1': Missing field 'type2'", 'name': 'TypeError'})
        self.assertEqual(reply['result'], None)

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"somestr": "mystr", "type2": {"someint": 5}}], "id": 2}')
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message':
            "echo_hash: Named hash parameter 'value.type2' of type 'Type2': Missing field 'type3'"})
        self.assertEqual(reply['result'], None)

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"somestr": "mystr", "type2": {"someint": 5, "type3": {"somebool": 8}}}], "id": 3}')
        self.assertEqual(reply['error'], {'message': "echo_hash: Expected value of type 'bool' for parameter 'value.type2.type3.somebool' but got value of type 'int'", 'name': 'TypeError'})
        self.assertEqual(reply['result'], None)

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"somestr": "mystr", "type2": {"someint": 5, "type3": {"somebool": true}}}], "id": 4}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], {
            'somestr': 'mystr',
            'type2': {
                'someint': 5,
                'type3': {'somebool': True}
            }
        })

    def test_typed_arrays_basic(self):
        rpc = RpcProcessor()

        func = RpcFunction(echo_array, 'echo_array', 'Expects an array of ints and returns it',
                'array<int>', 'Returns the array passed by the caller')
        func.add_param('array<int>', 'numbers', 'An array of integer values')

        rpc.add_function(func)

        reply = rpc.process_request('{"method": "echo_array", "params": [[1, 2, 3, 4, 5, 6 ,7, 8, 9]], "id": 1}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], [1, 2, 3, 4, 5, 6, 7, 8, 9])

        # test what happens if we send a non-array type
        reply = rpc.process_request('{"method": "echo_array", "params": [5], "id": 2}')
        self.assertEqual(reply['error'], {'message': "echo_array: Expected value of type 'array<int>' for parameter 'numbers' but got value of type 'int'", 'name': 'TypeError'})
        self.assertEqual(reply['result'], None)

        reply = rpc.process_request('{"method": "echo_array", "params": [[1, 2, "invalid string", 9]], "id": 3}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_array: Expected value of type 'int' for parameter 'numbers[2]' but got value of type 'string'"})

    def test_typed_arrays_with_custom_types(self):
        rpc = RpcProcessor()

        example_type = JsonHashType('Example', 'A named hash')
        example_type.add_field('somestr', 'string', 'Some string')
        example_type.add_field('someint', 'int', 'Some integer')

        func = RpcFunction(echo_array, 'echo_array', 'Expects an array of examples and returns it',
                'array<Example>', 'Returns the array passed by the caller')
        func.add_param('array<Example>', 'examples', 'An array of integer values')

        rpc.add_custom_type(example_type)
        rpc.add_function(func)

        reply = rpc.process_request('{"method": "echo_array", "params": [[5, 6, 7]], "id": 1}')
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_array: Named hash parameter 'examples[0]' of type 'Example' requires a hash value but got 'int'"})
        self.assertEqual(reply['result'], None)

        reply = rpc.process_request('{"method": "echo_array", "params": [[{"somestr": "str", "someint": 5}, {"somestr": "str", "someint": true}]], "id": 2}')
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_array: Expected value of type 'int' for parameter 'examples[1].someint' but got value of type 'bool'"})
        self.assertEqual(reply['result'], None)

        reply = rpc.process_request('{"method": "echo_array", "params": [[{"somestr": "str1", "someint": 5}, {"somestr": "str2", "someint": 6}]], "id": 3}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], [{'somestr': 'str1', 'someint': 5}, {'somestr': 'str2', 'someint': 6}])

    def test_custom_types_with_typed_array_fields(self):
        rpc = RpcProcessor()

        example_type = JsonHashType('Example', 'A named hash')
        example_type.add_field('somestrs', 'array<string>', 'Some strings')
        example_type.add_field('someints', 'array<int>', 'Some integers')

        func = RpcFunction(echo_hash, 'echo_hash', 'Expects an Example hash and returns it',
                'Example', 'Returns the hash passed by the caller')
        func.add_param('Example', 'examples', 'An example hash')

        rpc.add_custom_type(example_type)
        rpc.add_function(func)

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"somestrs": "", "someints": ""}], "id": 1}')
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_hash: Expected value of type 'array<string>' for parameter 'examples.somestrs' but got value of type 'string'"})
        self.assertEqual(reply['result'], None)

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"somestrs": ["str1", "str2"], "someints": [1, 2, "test", 3]}], "id": 2}')
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_hash: Expected value of type 'int' for parameter 'examples.someints[2]' but got value of type 'string'"})
        self.assertEqual(reply['result'], None)

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"somestrs": ["str1", "str2"], "someints": [1, 2, 3]}], "id": 3}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], {'somestrs': ['str1', 'str2'], 'someints': [1, 2, 3]})

if __name__ == '__main__':
    unittest.main()
