#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import sys
import unittest

sys.path.append('..')

from reflectrpc import RpcFunction

def dummy_function():
    pass

class RpcFunctionTests(unittest.TestCase):
    def test_valid_types_in_constructor(self):
        try:
            RpcFunction(dummy_function, 'dummy',
                    'Dummy function', 'int', 'Return value')
        except:
            self.fail("Constructor of RpcFunction raised unexpected exception!")

        try:
            RpcFunction(dummy_function, 'dummy',
                    'Dummy function', 'bool', 'Return value')
        except:
            self.fail("Constructor of RpcFunction raised unexpected exception!")

        try:
            RpcFunction(dummy_function, 'dummy',
                    'Dummy function', 'float', 'Return value')
        except:
            self.fail("Constructor of RpcFunction raised unexpected exception!")

        try:
            RpcFunction(dummy_function, 'dummy',
                    'Dummy function', 'string', 'Return value')
        except:
            self.fail("Constructor of RpcFunction raised unexpected exception!")

        try:
            RpcFunction(dummy_function, 'dummy',
                    'Dummy function', 'array', 'Return value')
        except:
            self.fail("Constructor of RpcFunction raised unexpected exception!")

        try:
            RpcFunction(dummy_function, 'dummy',
                    'Dummy function', 'hash', 'Return value')
        except:
            self.fail("Constructor of RpcFunction raised unexpected exception!")

        try:
            RpcFunction(dummy_function, 'dummy',
                    'Dummy function', 'base64', 'Return value')
        except:
            self.fail("Constructor of RpcFunction raised unexpected exception!")

    def test_invalid_type_in_constructor(self):
        self.assertRaises(ValueError, RpcFunction, dummy_function, 'dummy',
                'Dummy function', 'noint', 'Return value of invalid type')

    def test_valid_types_in_add_param(self):
        dummy_func = RpcFunction(dummy_function, 'dummy',
                'Dummy function', 'int', 'Return value')

        try:
            dummy_func.add_param('int', 'a', 'First parameter')
        except:
            self.fail("add_param raised unexpected exception!")

        try:
            dummy_func.add_param('bool', 'a', 'First parameter')
        except:
            self.fail("add_param raised unexpected exception!")

        try:
            dummy_func.add_param('float', 'a', 'First parameter')
        except:
            self.fail("add_param raised unexpected exception!")

        try:
            dummy_func.add_param('string', 'a', 'First parameter')
        except:
            self.fail("add_param raised unexpected exception!")

        try:
            dummy_func.add_param('array', 'a', 'First parameter')
        except:
            self.fail("add_param raised unexpected exception!")

        try:
            dummy_func.add_param('hash', 'a', 'First parameter')
        except:
            self.fail("add_param raised unexpected exception!")

        try:
            dummy_func.add_param('base64', 'a', 'First parameter')
        except:
            self.fail("add_param raised unexpected exception!")

    def test_invalid_type_in_add_param(self):
        dummy_func = RpcFunction(dummy_function, 'dummy',
                'Dummy function', 'int', 'Return value')
        self.assertRaises(ValueError, dummy_func.add_param, 'noint', 'a', 'First parameter')

    # Custom type tests
    #
    # custom types start with a captial letter and their check is postponed to
    # the time the function gets registered so they should always be accepted
    # when building a RpcFunction object, whether they exist or not

    def test_custom_type_as_result_type(self):
        try:
            RpcFunction(dummy_function, 'dummy',
                'Dummy function', 'ImaginaryCustomType', 'Return value')
        except:
            self.fail("RpcFunction constructor raised unexpected exception!")

    def test_custom_type_in_add_param(self):
        dummy_func = RpcFunction(dummy_function, 'dummy',
                'Dummy function', 'int', 'Return value')
        try:
            dummy_func.add_param('ImaginaryCustomType', 'a', 'First parameter')
        except:
            self.fail("add_param raised unexpected exception!")

if __name__ == '__main__':
    unittest.main()
