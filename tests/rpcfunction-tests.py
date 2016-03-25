#!/usr/bin/env python3

import sys
import unittest

sys.path.append('..')

from reflectrpc import RpcFunction

def dummy_function():
    pass

class RpcProcessorTests(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()
