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
        cpuinfo['cpus'] = []

        for entry in cpus:
            cpu = {}

            m = re.search(r'^processor\s*:\s+(\d+)$', data, re.MULTILINE)
            if m:
                cpu['processor'] = int(m.group(1))

            m = re.search(r'^vendor_id\s*:\s+(\w.+)$', data, re.MULTILINE)
            if m:
                cpu['vendor_id'] = m.group(1)

            m = re.search(r'^cpu family\s*:\s+(\d+)$', data, re.MULTILINE)
            if m:
                cpu['cpu_family'] = int(m.group(1))

            m = re.search(r'^model\s*:\s+(\d+)$', data, re.MULTILINE)
            if m:
                cpu['model'] = int(m.group(1))

            m = re.search(r'^model name\s*:\s+(\w.+)$', data, re.MULTILINE)
            if m:
                cpu['model_name'] = m.group(1)

            m = re.search(r'^stepping\s*:\s+(\d+)$', data, re.MULTILINE)
            if m:
                cpu['stepping'] = int(m.group(1))

            m = re.search(r'^cpu MHz\s*:\s+(\d+(\.\d+)?)$', data, re.MULTILINE)
            if m:
                cpu['cpu_mhz'] = float(m.group(1))

            m = re.search(r'^cache size\s*:\s+(\d+)\s+KB$', data, re.MULTILINE)
            if m:
                cpu['cache_size'] = int(m.group(1))

            m = re.search(r'^physical id\s*:\s+(\d+)$', data, re.MULTILINE)
            if m:
                cpu['physical_id'] = int(m.group(1))

            m = re.search(r'^core id\s*:\s+(\d+)$', data, re.MULTILINE)
            if m:
                cpu['core_id'] = int(m.group(1))

            m = re.search(r'^cpu cores\s*:\s+(\d+)$', data, re.MULTILINE)
            if m:
                cpu['cpu_cores'] = int(m.group(1))

            m = re.search(r'^fpu\s*:\s+(\w+)$', data, re.MULTILINE)
            if m:
                cpu['fpu'] = False
                if m.group(1) == 'yes':
                    cpu['fpu'] = True

            m = re.search(r'^flags\s*:\s+(\w.+)$', data, re.MULTILINE)
            if m:
                cpu['flags'] = m.group(1).split(' ')

            m = re.search(r'^bogomips\s*:\s+(\d+(\.\d+)?)$', data, re.MULTILINE)
            if m:
                cpu['bogomips'] = float(m.group(1))

            cpuinfo['cpus'].append(cpu)

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
cpuInfo.add_field('cpus', 'array<CPU>', 'Array of the CPUs available on the system')

cpu = reflectrpc.JsonHashType('CPU', 'Information about a single CPU')
cpu.add_field('processor', 'int', 'Number of this CPU (e.g. 0 for the first CPU in this system)')
cpu.add_field('vendor_id', 'string', 'Vendor name')
cpu.add_field('cpu_family', 'int', 'CPU family ID')
cpu.add_field('model', 'int', 'Model identifier')
cpu.add_field('model_name', 'string', 'Model name of this CPU')
cpu.add_field('stepping', 'int', 'Stepping of the CPU (which basically is the CPUs revision)')
cpu.add_field('cpu_mhz', 'float', 'Clock rate of this CPU in MHz')
cpu.add_field('cache_size', 'int', 'Size of the L2 cache of this CPU in KB')
cpu.add_field('physical_id', 'int', 'ID of the physical processor this CPU belongs to')
cpu.add_field('core_id', 'int', 'ID of CPU core this CPU entry represents')
cpu.add_field('cpu_cores', 'int', 'Number of CPU cores')
cpu.add_field('fpu', 'bool', 'Does this CPU have a floating point unit?')
cpu.add_field('flags', 'array', 'CPU flags describing features supported by this CPU')
cpu.add_field('bogomips', 'float', 'Bogus number to indicate the speed of this CPU')

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
jsonrpc.add_custom_type(cpu)

# register RPC functions
cpuinfo_func = reflectrpc.RpcFunction(get_cpuinfo, 'get_cpuinfo', 'Gets information about the system CPUs',
        'CPUInfo', 'System CPU information')
jsonrpc.add_function(cpuinfo_func)

meminfo_func = reflectrpc.RpcFunction(get_meminfo, 'get_meminfo', 'Gets information about the system memory',
        'MemInfo', 'System memory information')
jsonrpc.add_function(meminfo_func)

server = reflectrpc.twistedserver.TwistedJsonRpcServer(jsonrpc, '0.0.0.0', 5500)
server.run()
