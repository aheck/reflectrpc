#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import argparse
import json
import sys
import unittest

from reflectrpc.client import RpcClient
from reflectrpc.testing import ServerRunner

server_program = None

class ConformanceTest(unittest.TestCase):
    # Table driven conformance test that can also be run against
    # implementations in other programming languages
    def test_conformance(self):
        global server_program

        funcs_description = [{'description': 'Returns the message it was sent',
              'name': 'echo',
              'params': [{'description': 'The message we will send back',
                  'name': 'message',
                  'type': 'string'}],
              'result_desc': 'The message previously received',
              'result_type': 'string'},
              {'description': 'Adds two numbers',
                  'name': 'add',
                  'params': [{'description': 'First number to add',
                      'name': 'a',
                      'type': 'int'},
                      {'description': 'Second number to add',
                          'name': 'b',
                          'type': 'int'}],
                      'result_desc': 'Sum of the two numbers',
                      'result_type': 'int'},
              {'description': 'Subtracts one number from another',
                  'name': 'sub',
                  'params': [{'description': 'Number to subtract from',
                      'name': 'a',
                      'type': 'int'},
                      {'description': 'Number to subtract',
                          'name': 'b',
                          'type': 'int'}],
                      'result_desc': 'Difference of the two numbers',
                      'result_type': 'int'},
              {'description': 'Multiplies two numbers',
                  'name': 'mul',
                  'params': [{'description': 'First factor',
                      'name': 'a',
                      'type': 'int'},
                      {'description': 'Second factor',
                          'name': 'b',
                          'type': 'int'}],
                      'result_desc': 'Product of the two numbers',
                      'result_type': 'int'},
              {'description': 'Divide a number by another number',
                  'name': 'div',
                  'params': [{'description': 'Dividend',
                      'name': 'a',
                      'type': 'float'},
                      {'description': 'Divisor',
                          'name': 'b',
                          'type': 'float'}],
                      'result_desc': 'Ratio of the two numbers',
                      'result_type': 'float'},
              {'description': 'Test the phone type enum',
                  'name': 'enum_echo',
                  'params': [{'description': 'Type of phone number',
                      'name': 'phone_type',
                      'type': 'PhoneType'}],
                  'result_desc': 'Phone type',
                  'result_type': 'int'},
              {'description': 'Test the address hash type',
                      'name': 'hash_echo',
                      'params': [{'description': 'Address hash',
                          'name': 'address',
                          'type': 'Address'}],
                      'result_desc': 'Address hash',
                      'result_type': 'hash'},
              {'description': 'Test function for notify requests',
                      'name': 'notify',
                      'params': [{'description': 'A value to print on the server side',
                          'name': 'value',
                          'type': 'string'}],
                      'result_desc': '',
                      'result_type': 'bool'},
              {'description': 'Checks if we have an authenticated connection',
                      'name': 'is_authenticated',
                      'params': [],
                      'result_desc': 'The authentication status',
                      'result_type': 'bool'},
              {'description': 'Gets the username of the logged in user',
                      'name': 'get_username',
                      'params': [],
                      'result_desc': 'The username of the logged in user',
                      'result_type': 'string'}]

        types_description = [{'description': 'Type of a phone number',
                  'name': 'PhoneType',
                  'type': 'enum',
                  'values': [{'description': 'Home phone',
                      'intvalue': 0,
                      'name': 'HOME'},
                      {'description': 'Work phone',
                          'intvalue': 1,
                          'name': 'WORK'},
                      {'description': 'Mobile phone',
                          'intvalue': 2,
                          'name': 'MOBILE'},
                      {'description': 'FAX number',
                          'intvalue': 3,
                          'name': 'FAX'}]},
                      {'description': 'Street address',
                          'fields': [{'description': 'First name',
                              'name': 'firstname',
                              'type': 'string'},
                              {'description': 'Last name',
                                  'name': 'lastname',
                                  'type': 'string'},
                              {'description': 'First address line',
                                  'name': 'street1',
                                  'type': 'string'},
                              {'description': 'Second address line',
                                  'name': 'street2',
                                  'type': 'string'},
                              {'description': 'Zip code',
                                  'name': 'zipcode',
                                  'type': 'string'},
                              {'description': 'City',
                                  'name': 'city',
                                  'type': 'string'}],
                              'name': 'Address',
                              'type': 'hash'}]

        tests = [
                ['{"method": "echo", "params": ["Hello Server"], "id": 1}',
                 '{"result": "Hello Server", "error": null, "id": 1}'],
                ['{"method": "add", "params": [5, 6], "id": 2}',
                 '{"result": 11, "error": null, "id": 2}'],

                # test non-int IDs
                ['{"method": "echo", "params": ["Hello"], "id": "abcd1234"}',
                 '{"result": "Hello", "error": null, "id": "abcd1234"}'],
                ['{"method": "add", "params": [34, 67], "id": 3.14}',
                 '{"result": 101, "error": null, "id": 3.14}'],

                # test descriptions
                ['{"method": "__describe_service", "params": [], "id": 3}',
                 '{"result": {"version": "1.0", "name": "Example RPC Service", "description": "This is an example service for ReflectRPC", "custom_fields": {}}, "error": null, "id": 3}'],
                ['{"method": "__describe_functions", "params": [], "id": 4}',
                 '{"result": %s, "error": null, "id": 4}' % (json.dumps(funcs_description))],
                ['{"method": "__describe_custom_types", "params": [], "id": 5}',
                 '{"result": %s, "error": null, "id": 5}' % (json.dumps(types_description))]
        ]

        server = ServerRunner(server_program, 5500)
        server.run()

        client = RpcClient('localhost', 5500)

        self.maxDiff = None

        request = None
        expected_result = None
        result_str = None
        i = 0

        try:
            for test in tests:
                i += 1

                request = test[0]
                expected_result = json.loads(test[1])

                result_str = client.rpc_call_raw(request)
                result_dict = json.loads(result_str)
                self.assertEqual(result_dict, expected_result)
        except AssertionError as e:
            print("Test number %d failed: " % (i))
            print(request)

            raise e
        finally:
            server.stop()


parser = argparse.ArgumentParser(
        description="ReflectRPC conformance test to run against a server program that listens on localhost:5500")

parser.add_argument("server_program", metavar='SERVER', type=str,
        help="Server program to run the test against")

args = parser.parse_args()
server_program = args.server_program

# reset argv so unittest.main() does not try to interpret our arguments
sys.argv = [sys.argv[0]]

if __name__ == '__main__':
    unittest.main()
