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
        address_type.add_field('street2', 'string', 'Second address line')
        address_type.add_field('zipcode', 'string', 'Zip code')
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

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"name": "test", "number": 42}], "id": 2}')
        self.assertEqual(reply['error'], None)
        self.assertEqual(reply['result'], {'name': 'test', 'number': 42})

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

        # Call with an empty hash should get us an error mentioning all missing fields
        reply = rpc.process_request('{"method": "echo_hash", "params": [{}], "id": 1}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError',
            'message': "echo_hash: Named hash parameter 'custom_hash' of type 'CustomHash': Missing field 'boolfield'"
        })

        # Call with an invalid field should return the corresponding error
        reply = rpc.process_request('{"method": "echo_hash", "params": [{"boolfield": true, "stringfield": 5, "intfield": 5, "floatfield": 5.5, "arrayfield": [], "hashfield": {}}], "id": 2}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_hash: Named hash parameter 'custom_hash' of type 'CustomHash' has invalid field 'stringfield': Expected string but got int"})

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
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_hash: Named hash parameter 'custom_hash' of type 'CustomHash' has invalid field 'phonetype': 'TEST' is not a valid value"})

        reply = rpc.process_request('{"method": "echo_hash", "params": [{"phonetype": []}], "id": 2}')
        self.assertEqual(reply['result'], None)
        self.assertEqual(reply['error'], {'name': 'TypeError', 'message': "echo_hash: Named hash parameter 'custom_hash' of type 'CustomHash' has invalid field 'phonetype': Value must be of type 'int' or 'string' but type was 'array'"})

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


if __name__ == '__main__':
    unittest.main()
