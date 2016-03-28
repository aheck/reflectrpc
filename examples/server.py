#!/usr/bin/env python3

import sys

sys.path.append('..')

import reflectrpc
import reflectrpc.simpleserver

def echo(message):
    return message

def add(a, b):
    return int(a) + int(b)

def sub(a, b):
    return int(a) - int(b)

def mul(a, b):
    return int(a) * int(b)

def div(a, b):
    return float(a) / float(b)

phone_type_enum = reflectrpc.JsonEnumType('PhoneType', 'Type of a phone number')
phone_type_enum.add_value('HOME', 'Home phone')
phone_type_enum.add_value('WORK', 'Work phone')
phone_type_enum.add_value('MOBILE', 'Mobile phone')
phone_type_enum.add_value('FAX', 'FAX number')

address_hash = reflectrpc.JsonHashType('Address', 'Street address')
address_hash.add_field('firstname', 'string', 'First name')
address_hash.add_field('lastname', 'string', 'Last name')
address_hash.add_field('street1', 'string', 'First address line')
address_hash.add_field('street2', 'string', 'Second address line')
address_hash.add_field('zipcode', 'string', 'Zip code')
address_hash.add_field('city', 'string', 'City')

def enum_echo(phone_type):
    return phone_type_enum.resolve(phone_type)

def hash_echo(address_hash):
    return address_hash

jsonrpc = reflectrpc.RpcProcessor()
jsonrpc.description = "This is an example service for ReflectRPC"

# register types
jsonrpc.add_custom_type(phone_type_enum)
jsonrpc.add_custom_type(address_hash)

echo_func = reflectrpc.RpcFunction(echo, 'echo', 'Returns the message it was sent',
        'string', 'The message previously received')
echo_func.add_param('string', 'message', 'The message we will send back')
jsonrpc.add_function(echo_func)

add_func = reflectrpc.RpcFunction(add, 'add', 'Adds two numbers', 'int',
        'Sum of the two numbers')
add_func.add_param('int', 'a', 'First number to add')
add_func.add_param('int', 'b', 'Second number to add')
jsonrpc.add_function(add_func)

sub_func = reflectrpc.RpcFunction(sub, 'sub', 'Subtracts one number from another', 'int',
        'Difference of the two numbers')
sub_func.add_param('int', 'a', 'Number to subtract from')
sub_func.add_param('int', 'b', 'Number to subtract')
jsonrpc.add_function(sub_func)

mul_func = reflectrpc.RpcFunction(mul, 'mul', 'Multiplies two numbers', 'int',
        'Product of the two numbers')
mul_func.add_param('int', 'a', 'First factor')
mul_func.add_param('int', 'b', 'Second factor')
jsonrpc.add_function(mul_func)

div_func = reflectrpc.RpcFunction(div, 'div', 'Divide a number by another number',
        'float', 'Ratio of the two numbers')
div_func.add_param('float', 'a', 'Dividend')
div_func.add_param('float', 'b', 'Divisor')
jsonrpc.add_function(div_func)

enum_echo_func = reflectrpc.RpcFunction(enum_echo, 'enum_echo', 'Test the phone type enum',
        'int', 'Phone type')
enum_echo_func.add_param('PhoneType', 'phone_type', 'Type of phone number')
jsonrpc.add_function(enum_echo_func)

hash_echo_func = reflectrpc.RpcFunction(hash_echo, 'hash_echo', 'Test the address hash type',
        'hash', 'Address hash')
hash_echo_func.add_param('Address', 'address', 'Address hash')
jsonrpc.add_function(hash_echo_func)

try:
    server = reflectrpc.simpleserver.SimpleJsonRpcServer(jsonrpc, 'localhost', 5500)
    server.run()
except KeyboardInterrupt:
    sys.exit(0)
