from __future__ import unicode_literals, print_function
from builtins import bytes, dict, list, int, float, str

import json
import sys

from cmd import Cmd

from reflectrpc.client import RpcClient
from reflectrpc.client import RpcError
import reflectrpc
import reflectrpc.cmdline

def print_types(types):
    for t in types:
        if t['type'] == 'enum':
            print('enum: %s' % (t['name']))
            print('Description: %s' % (t['description']))
            for value in t['values']:
                print('    [%d] %s - %s' % (value['intvalue'], value['name'], value['description']))
        elif t['type'] == 'hash':
            print('hash: %s' % (t['name']))
            print('Description: %s' % (t['description']))
            for field in t['fields']:
                print('    [%s] %s - %s' % (field['type'], field['name'], field['description']))
        else:
            print('Unknown class of custom type: %s' % (t['type']))

def print_functions(functions):
    for func_desc in functions:
        paramlist = [param['name'] for param in func_desc['params']]
        paramlist = ', '.join(paramlist)

        print("%s(%s) - %s" % (func_desc['name'], paramlist, func_desc['description']))
        for param in func_desc['params']:
            print("    [%s] %s - %s" % (param['type'], param['name'], param['description']))
        print("    Result: %s - %s" % (func_desc['result_type'], func_desc['result_desc']))

def split_exec_line(line):
    tokens = []
    curtoken = ''
    intoken = False
    instring = False
    lastc = ''
    arraylevel = 0
    hashlevel = 0

    for c in line:
        if c.isspace():
            if not intoken:
                lastc = c
                continue

            # end of token?
            if not arraylevel and not hashlevel and not instring:
                tokens.append(curtoken.strip())
                curtoken = ''
                intoken = False
        else:
            intoken = True

        if intoken:
            curtoken += c

        if c == '"':
            if lastc != '\\':
                instring = not instring
        elif c == '[':
            if not instring:
                arraylevel += 1
        elif c == ']':
            if not instring:
                arraylevel -= 1
        elif c == '{':
            if not instring:
                hashlevel += 1
        elif c == '}':
            if not instring:
                hashlevel -= 1

        lastc = c

    if len(curtoken.strip()):
        tokens.append(curtoken.strip())

    # type casting
    itertokens = iter(tokens)
    next(itertokens) # skip first token which is the method name
    for i, t in enumerate(itertokens):
        i += 1
        try:
            tokens[i] = json.loads(t)
        except ValueError as e:
            print("Invalid JSON in parameter %i:" % (i))
            print("'%s'" % (t))
            return None

    return tokens

class ReflectRpcShell(Cmd):
    def __init__(self, client):
        if issubclass(Cmd, object):
            super().__init__()
        else:
            Cmd.__init__(self)

        self.client = client

    def connect(self):
        self.client.enable_auto_reconnect()

        try:
            self.retrieve_service_description()
            self.retrieve_functions()
            self.retrieve_custom_types()
        except reflectrpc.client.NetworkError as e:
            print(e, file=sys.stderr)
            print('', file=sys.stderr)
            reflectrpc.cmdline.connection_failed_error(self.client.host,
                    self.client.port, True)
        except reflectrpc.client.HttpException as e:
            if e.status == '401':
                print('Authentication failed\n', file=sys.stderr)
                reflectrpc.cmdline.connection_failed_error(self.client.host,
                        self.client.port, True)

            raise e

        self.prompt = '(rpc) '
        if self.client.host.startswith('unix://'):
            self.intro = "ReflectRPC Shell\n================\n\nType 'help' for available commands\n\nRPC server: %s" % (self.client.host)
        else:
            self.intro = "ReflectRPC Shell\n================\n\nType 'help' for available commands\n\nRPC server: %s:%i" % (self.client.host, self.client.port)

        if self.service_description:
            self.intro += "\n\nSelf-description of the Service:\n================================\n"
            if self.service_description['name']:
                self.intro += self.service_description['name']
                if self.service_description['version']:
                    self.intro += " (%s)\n" % (self.service_description['version'])
            if self.service_description['description']:
                self.intro += self.service_description['description']

    def retrieve_service_description(self):
        self.service_description = ''
        try:
            self.service_description = self.client.rpc_call('__describe_service')
        except RpcError:
            pass

    def retrieve_functions(self):
        self.functions = []
        try:
            self.functions = self.client.rpc_call('__describe_functions')
        except RpcError:
            pass

    def retrieve_custom_types(self):
        self.custom_types = []
        try:
            self.custom_types = self.client.rpc_call('__describe_custom_types')
        except RpcError:
            pass

    def complete_doc(self, text, line, start_index, end_index):
        return self.function_completion(text, line)

    def complete_exec(self, text, line, start_index, end_index):
        return self.function_completion(text, line)

    def complete_notify(self, text, line, start_index, end_index):
        return self.function_completion(text, line)

    def function_completion(self, text, line):
        if len(line.split()) > 2:
            return []

        if len(line.split()) == 2 and text == '':
            return []

        result = [f['name'] for f in self.functions if f['name'].startswith(text)]

        if len(result) == 1 and result[0] == text:
            return []

        return result

    def complete_type(self, text, line, start_index, end_index):
        if len(line.split()) > 2:
            return []

        if len(line.split()) == 2 and text == '':
            return []

        result = [t['name'] for t in self.custom_types if t['name'].startswith(text)]

        if len(result) == 1 and result[0] == text:
            return []

        return result

    def do_help(self, line):
        if not line:
            print("list   - List all RPC functions advertised by the server")
            print("doc    - Show the documentation of a RPC function")
            print("type   - Show the documentation of a custom RPC type")
            print("types  - List all custom RPC types advertised by the server")
            print("exec   - Execute an RPC call")
            print("notify - Execute an RPC call but tell the server to send no response")
            print("raw    - Directly send a raw JSON-RPC message to the server")
            print("quit   - Quit this program")
            print("help   - Print this message. 'help [command]' prints a")
            print("         detailed help message for a command")
            return

        if line == 'list':
            print("List all RPC functions advertised by the server")
        elif line == 'doc':
            print("Show the documentation of an RPC function")
            print("Example:")
            print("    doc echo")
        elif line == 'type':
            print("Shos the documentation of a custom RPC type")
            print("Example:")
            print("    type PhoneType")
        elif line == 'types':
            print("List all custom RPC types advertised by the server")
        elif line == 'exec':
            print("Execute an RPC call")
            print("Examples:")
            print("    exec echo \"Hello RPC server\"")
            print("    exec add 4 8")
        elif line == 'notify':
            print("Execute an RPC call but tell the server to send no response")
            print("Example:")
            print("    notify rpc_function")
        elif line == 'raw':
            print("Directly send a raw JSON-RPC message to the server")
            print("Example:")
            print('    raw {"method": "echo", "params": ["Hello Server"], "id": 1}')
        elif line == 'quit':
            print("Quit this program")
        elif line == 'help':
            pass
        else:
            print("No help available for unknown command:", line)

    def do_type(self, line):
        if not line:
            print("You have to pass the name of a custom RPC type: 'type [typename]'")
            return

        t = [t for t in self.custom_types if t['name'] == line]

        if not t:
            print("Unknown custom RPC type:", line)

        print_types(t)

    def do_types(self, line):
        for t in self.custom_types:
            print(t['name'])

    def do_exec(self, line):
        tokens = split_exec_line(line)

        if not tokens:
            return

        method = tokens.pop(0)
        try:
            result = self.client.rpc_call(method, *tokens)
            print("Server replied:", json.dumps(result, indent=4, sort_keys=True))
        except RpcError as e:
            print(e)

    def do_notify(self, line):
        tokens = split_exec_line(line)

        if not tokens:
            return

        method = tokens.pop(0)
        self.client.rpc_notify(method, *tokens)

    def do_raw(self, line):
        print(self.client.rpc_call_raw(line))

    def do_doc(self, line):
        if not line:
            print("You have to pass the name of an RPC function: 'doc [function]'")
            return

        function = [func for func in self.functions if func['name'] == line]

        if not function:
            print("Unknown RPC function:", line)

        print_functions(function)

    def do_list(self, line):
        for func in self.functions:
            paramlist = [param['name'] for param in func['params']]
            print("%s(%s)" % (func['name'], ', '.join(paramlist)))

    def do_quit(self, line):
        sys.exit(0)

    def do_EOF(self, line):
        sys.exit(0)
