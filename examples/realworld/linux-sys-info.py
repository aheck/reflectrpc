#!/usr/bin/env python3

import re

from twisted.internet import threads, reactor, defer

import reflectrpc
from reflectrpc.twistedserver import TwistedJsonRpcServer

#
# This example RPC service shows how to use ReflectRPC to create a production
# service using Twisted for concurrency
#
# The service runs only on Linux and provides access to system level
# information in the /proc filesystem.
#

def get_cpuinfo():
    # callback function for blocking file IO
    def read_cpuinfo_file():
        data = ''
        with open('/proc/cpuinfo', 'r') as f:
            data=f.read()

        return data

    # callback function for parsing the file data once it has been read and for
    # wrapping it into a CPUInfo structure that can be sent to the client
    def parse_data(data):
        cpuinfo = {}
        cpuinfo['numCPUs'] = 0

        data = data.rstrip()
        cpus = data.split('\n\n')

        cpuinfo['numCPUs'] = len(cpus)

        return cpuinfo

    # read the /proc file in a thread and return a deferred
    d = threads.deferToThread(read_cpuinfo_file)
    # setup the callback to parse the file data once it is ready
    d.addCallback(parse_data)

    return d

def get_meminfo():
    # callback function for blocking file IO
    def read_meminfo_file():
        data = ''
        with open('/proc/meminfo', 'r') as f:
            data=f.read()

        return data

    # callback function for parsing the file data once it has been read and for
    # wrapping it into a MemInfo structure that can be sent to the client
    def parse_data(data):
        result = {}
        result['memTotal'] = 0
        result['memFree'] = 0
        result['memAvailable'] = 0
        result['cached'] = 0
        result['swapTotal'] = 0
        result['swapFree'] = 0

        m = re.search(r'^MemTotal:\s+(\d+)\s+kB$', data, re.MULTILINE)
        if m:
            result['memTotal'] = int(m.group(1))

        m = re.search(r'^MemFree:\s+(\d+)\s+kB$', data, re.MULTILINE)
        if m:
            result['memFree'] = int(m.group(1))

        m = re.search(r'^MemAvailable:\s+(\d+)\s+kB$', data, re.MULTILINE)
        if m:
            result['memAvailable'] = int(m.group(1))

        m = re.search(r'^Cached:\s+(\d+)\s+kB$', data, re.MULTILINE)
        if m:
            result['cached'] = int(m.group(1))

        m = re.search(r'^SwapTotal:\s+(\d+)\s+kB$', data, re.MULTILINE)
        if m:
            result['swapTotal'] = int(m.group(1))

        m = re.search(r'^SwapFree:\s+(\d+)\s+kB$', data, re.MULTILINE)
        if m:
            result['swapFree'] = int(m.group(1))

        return result

    # read the /proc file in a thread and return a deferred
    d = threads.deferToThread(read_meminfo_file)
    # setup the callback to parse the file data once it is ready
    d.addCallback(parse_data)

    return d

# create custom types
cpuInfo = reflectrpc.JsonHashType('CPUInfo', 'Information about CPUs')
cpuInfo.add_field('numCPUs', 'int', 'Number of CPUs')

memInfo = reflectrpc.JsonHashType('MemInfo', 'Information about system memory')
memInfo.add_field('memTotal', 'int', 'Total system memory in kB')
memInfo.add_field('memFree', 'int', 'Free memory in kB')
memInfo.add_field('memAvailable', 'int', 'Available memory in kB')
memInfo.add_field('cached', 'int', 'Cached pages in kB')
memInfo.add_field('swapTotal', 'int', 'Total swap memory in kB')
memInfo.add_field('swapFree', 'int', 'Free swap memory in kB')

# create service
jsonrpc = reflectrpc.RpcProcessor()
jsonrpc.set_description("Linux System Information Service",
        "This JSON-RPC service provides access to live system information of a Linux server",
        reflectrpc.version)

# register types
jsonrpc.add_custom_type(memInfo)
jsonrpc.add_custom_type(cpuInfo)

# register RPC functions
cpuinfo_func = reflectrpc.RpcFunction(get_cpuinfo, 'get_cpuinfo', 'Gets information about the system CPUs',
        'CPUInfo', 'System CPU information')
jsonrpc.add_function(cpuinfo_func)

meminfo_func = reflectrpc.RpcFunction(get_meminfo, 'get_meminfo', 'Gets information about the system memory',
        'MemInfo', 'System memory information')
jsonrpc.add_function(meminfo_func)

server = reflectrpc.twistedserver.TwistedJsonRpcServer(jsonrpc, '0.0.0.0', 5500)
server.run()
