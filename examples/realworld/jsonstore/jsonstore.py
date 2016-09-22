#!/usr/bin/env python3

from txpostgres import txpostgres

from twisted.internet import reactor
from twisted.python import log, util

import json
import sys
import uuid

import reflectrpc
from reflectrpc import RpcProcessor
from reflectrpc import RpcFunction
from reflectrpc.twistedserver import TwistedJsonRpcServer

db_connections = {}

#
# This JSON-RPC service implements a JSON object store that uses PostgreSQL and
# its jsonb datatype as a storage backend.
#

# Helper functions

def get_db_connection():
    conn = txpostgres.Connection()
    d = conn.connect('host=localhost port=5432 user=postgres dbname=jsonstore')

    return conn, d

#
# Implementation of JSON-RPC functions
#

def get_object(rpcinfo, uuid):
    conn, d = get_db_connection()

    d.addCallback(lambda _: conn.runQuery("SELECT uuid, obj_name, data, updated FROM jsonstore WHERE uuid=%s", (uuid, )))
    def return_result(data):
        conn.close()

        data = data[0]
        obj = data[2]
        obj['_id'] = data[0]
        obj['_name'] = data[1]

        return obj

    d.addCallback(return_result)

    return d

def get_object_by_name(rpcinfo, obj_name):
    conn, d = get_db_connection()

    d.addCallback(lambda _: conn.runQuery("SELECT uuid, obj_name, data, updated FROM jsonstore WHERE obj_name=%s", (obj_name, )))
    def return_result(data):
        conn.close()

        data = data[0]
        obj = data[2]
        obj['_id'] = data[0]
        obj['_name'] = data[1]

        return obj

    d.addCallback(return_result)

    return d

def find_objects(rpcinfo, obj_filter):
    conn, d = get_db_connection()

    d.addCallback(lambda _: conn.runQuery("SELECT uuid, obj_name, data, updated FROM jsonstore WHERE data->>%s=%s", (obj_filter['field'], obj_filter['value'])))
    def return_result(data):
        conn.close()

        result = []

        for row in data:
            obj = row[2]
            obj['_id'] = row[0]
            obj['_name'] = row[1]
            result.append(obj)

        return result

    d.addCallback(return_result)

    return d

def insert_object(rpcinfo, obj):
    conn, d = get_db_connection()
    obj_json = json.dumps(obj)

    new_uuid = str(uuid.uuid4())
    d.addCallback(lambda _: conn.runOperation("INSERT INTO jsonstore (uuid, data) VALUES (%s, %s)",
        (new_uuid, obj_json)))
    def return_result(data):
        conn.close()

        return data

    d.addCallback(return_result)

    return d

def insert_object_with_name(rpcinfo, obj_name, obj):
    conn, d = get_db_connection()
    obj_json = json.dumps(obj)

    new_uuid = str(uuid.uuid4())
    d.addCallback(lambda _: conn.runOperation("INSERT INTO jsonstore (uuid, obj_name, data) VALUES (%s, %s, %s)",
        (new_uuid, obj_name, obj_json)))
    def return_result(data):
        conn.close()

        return data

    d.addCallback(return_result)

    return d

def update_object(rpcinfo, uuid, obj):
    conn, d = get_db_connection()
    obj_json = json.dumps(obj)

    d.addCallback(lambda _: conn.runOperation("UPDATE jsonstore SET data=%s WHERE uuid=%s",
        (obj_json, uuid)))
    def return_result(data):
        conn.close()

        return data

    d.addCallback(return_result)

    return d

def update_object_by_name(rpcinfo, name, obj):
    conn, d = get_db_connection()
    obj_json = json.dumps(obj)

    d.addCallback(lambda _: conn.runOperation("UPDATE jsonstore SET data=%s WHERE obj_name=%s",
        (obj_json, name)))
    def return_result(data):
        conn.close()

        return data

    d.addCallback(return_result)

    return d

def delete_object(rpcinfo, uuid):
    conn, d = get_db_connection()

    d.addCallback(lambda _: conn.runOperation("DELETE FROM jsonstore WHERE uuid=%s", (uuid, )))

    def return_result(data):
        conn.close()
        return True

    return d

def delete_object_by_name(rpcinfo, name):
    conn, d = get_db_connection()

    d.addCallback(lambda _: conn.runOperation("DELETE FROM jsonstore WHERE obj_name=%s", (name, )))

    def return_result(data):
        conn.close()
        return True

    return d


# Declare custom types
objFilter = reflectrpc.JsonHashType('ObjFilter', 'A filter comparing one JSON field for equality')
objFilter.add_field('field', 'string', 'Name of the field to filter on')
objFilter.add_field('value', 'string', 'Name of the value to filter for')

# Create service object
jsonrpc = RpcProcessor()
jsonrpc.set_description("JSON Store Service",
        "JSON-RPC service for storing JSON objects in a PostgreSQL database",
        reflectrpc.version)

# Register custom types
jsonrpc.add_custom_type(objFilter)

# Register functions
get_object_func = RpcFunction(get_object, 'get_object', 'Gets a JSON object by its UUID',
        'hash', 'JSON object')
get_object_func.add_param('string', 'uuid', 'UUID of the JSON object to retrieve')
get_object_func.require_rpcinfo()
jsonrpc.add_function(get_object_func)

get_object_by_name_func = RpcFunction(get_object_by_name, 'get_object_by_name', 'Gets a JSON object by its name', 'hash', 'JSON object')
get_object_by_name_func.add_param('string', 'name', 'Name of the JSON object to retrieve')
get_object_by_name_func.require_rpcinfo()
jsonrpc.add_function(get_object_by_name_func)

find_objects_func = RpcFunction(find_objects, 'find_objects', 'Finds JSON objects which match a filter', 'array<hash>', 'List of matching JSON object')
find_objects_func.add_param('ObjFilter', 'filter', 'Filter for the JSON objects to retrieve')
find_objects_func.require_rpcinfo()
jsonrpc.add_function(find_objects_func)

insert_object_func = RpcFunction(insert_object, 'insert_object', 'Inserts a new JSON object',
        'bool', 'true on success, false on failure')
insert_object_func.add_param('hash', 'obj', 'The JSON object to insert')
insert_object_func.require_rpcinfo()
jsonrpc.add_function(insert_object_func)

insert_object_with_name_func = RpcFunction(insert_object_with_name, 'insert_object_with_name', 'Inserts a new JSON object with a user supplied name', 'bool', 'true on success, false on failure')
insert_object_with_name_func.add_param('string', 'obj_name', 'The name of the new JSON object')
insert_object_with_name_func.add_param('hash', 'obj', 'The JSON object to insert')
insert_object_with_name_func.require_rpcinfo()
jsonrpc.add_function(insert_object_with_name_func)

update_object_func = RpcFunction(update_object, 'update_object', 'Updates an existing JSON object',
        'bool', 'true on success, false on failure')
update_object_func.add_param('string', 'uuid', 'The UUID of the JSON object to update')
update_object_func.add_param('hash', 'obj', 'The new version of the JSON object')
update_object_func.require_rpcinfo()
jsonrpc.add_function(update_object_func)

update_object_by_name_func = RpcFunction(update_object_by_name, 'update_object_by_name', 'Updates an existing JSON object', 'bool', 'true on success, false on failure')
update_object_by_name_func.add_param('string', 'obj_name', 'The name of the JSON object to update')
update_object_by_name_func.add_param('hash', 'obj', 'The new version of the JSON object')
update_object_by_name_func.require_rpcinfo()
jsonrpc.add_function(update_object_by_name_func)

delete_object_func = RpcFunction(delete_object, 'delete_object', 'Deletes a JSON object identified by its UUID', 'bool', 'true on success, false on failure')
delete_object_func.add_param('string', 'uuid', 'UUID of the object to delete')
delete_object_func.require_rpcinfo()
jsonrpc.add_function(delete_object_func)

delete_object_by_name_func = RpcFunction(delete_object_by_name, 'delete_object_by_name', 'Deletes a JSON object identified by its name', 'bool', 'true on success, false on failure')
delete_object_by_name_func.add_param('string', 'name', 'Name of the object to delete')
delete_object_by_name_func.require_rpcinfo()
jsonrpc.add_function(delete_object_by_name_func)

# Run the server
server = reflectrpc.twistedserver.TwistedJsonRpcServer(jsonrpc, '0.0.0.0', 5500)
server.run()
