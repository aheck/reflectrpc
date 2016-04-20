#!/usr/bin/env python3

from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import argparse
import json
import sys
import time
import unittest

from reflectrpc.client import RpcClient
from reflectrpc.testing import ServerRunner

parser = argparse.ArgumentParser(
        description="ReflectRPC benchmark to run against a server program that listens on localhost:5500")

args = parser.parse_args()

# reset argv so unittest.main() does not try to interpret our arguments
sys.argv = [sys.argv[0]]

client = RpcClient('localhost', 5500)

# ensure we are alread connected when the benchmark starts
client.rpc_call_raw('{"method": "echo", "params": ["Hello Server"], "id": 1}')

millis_start = int(round(time.time() * 1000))
num_requests = 5000

for i in range(num_requests):
    result = client.rpc_call_raw('{"method": "echo", "params": ["Hello Server"], "id": 1}')

millis_stop = int(round(time.time() * 1000))
millis_spent = millis_stop - millis_start

print("Requests: %d" % (num_requests))
print("Time: %d ms" % (millis_spent))
print("Requests per Second: %d" % (num_requests * (1000 / millis_spent)))
