from __future__ import unicode_literals, print_function
from builtins import bytes, dict, list, int, float, str

import argparse
import sys

import reflectrpc
import reflectrpc.client
from reflectrpc.client import RpcClient
from reflectrpc.client import RpcError

def build_cmdline_parser(description):
    """
    Generic command-line parsing for ReflectRPC tools

    Args:
        description (str): Description of the program for which we parse
                           command-line args

    Returns:
        argparse.ArgumentParser: Preinitialized parser
    """
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("host", metavar='HOST', type=str, help="Host to connect to")
    parser.add_argument("port", metavar='PORT', type=int, help="Port to connect to (omit if HOST is a UNIX domain socket)")

    parser.add_argument('--http', default=False, action='store_true',
            help='Use HTTP as transport protocol')
    parser.add_argument('--http-path', default='',
            help='HTTP path to send RPC calls to (default is /rpc)')

    parser.add_argument('-t', '--tls', default=False, action='store_true',
            help='Use TLS authentication and encryption on the RPC connection')
    parser.add_argument('--check-hostname', default=False, action='store_true',
            help='Check server hostname against its TLS certificate')
    parser.add_argument('-C', '--ca', default='',
            help='Certificate Authority to check the server certificate against')
    parser.add_argument('-k', '--key', default='',
            help='Key for client authentication')
    parser.add_argument('-c', '--cert', default='',
            help='Certificate for client authentication')

    # make the PORT argument optional if HOST is a UNIX domain socket
    pos = -1
    for i, elem in enumerate(sys.argv):
        if elem.startswith('unix://'):
            pos = i
            break

    if pos > -1:
        sys.argv.insert(pos + 1, '0')

    return parser

def connect_client(args):
    """
    Create and connect a RpcClient object based on parsed command-line args

    Args:
        args (argparse.Namespace): 

    Returns:
        reflectrpc.RpcClient: Connected RpcClient client
    """
    client = RpcClient(args.host, args.port)

    if args.http:
        client.enable_http(args.http_path)

    if args.tls:
        client.enable_tls(args.ca, args.check_hostname)

    if args.cert and args.key:
        args.client.enable_client_auth(args.cert, args.key)

    return client

def fetch_service_metainfo(client):
    """
    Fetch all metainformation from a service
    """
    service_description = ''
    functions = []
    custom_types = []

    try:
        try:
            service_description = client.rpc_call('__describe_service')
        except RpcError:
            print("Call to '__describe_service' failed", file=sys.stderr)

        try:
            functions = client.rpc_call('__describe_functions')
        except RpcError:
            print("Call to '__describe_functions' failed", file=sys.stderr)

        try:
            custom_types = client.rpc_call('__describe_custom_types')
        except RpcError:
            print("Call to '__describe_custom_types' failed", file=sys.stderr)
    except reflectrpc.client.NetworkError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    return service_description, functions, custom_types
