import json
import sys

from cmd import Cmd

from reflectrpc import RpcClient
from reflectrpc import RpcError
import reflectrpc

def print_functions(functions):
    for func_desc in functions:
        paramlist = [param['name'] for param in func_desc['params']]
        paramlist = ', '.join(paramlist)

        print("%s(%s) - %s" % (func_desc['name'], paramlist, func_desc['description']))
        for param in func_desc['params']:
            print("    [%s] %s - %s" % (param['type'], param['name'], param['desc']))
        print("    Result: %s - %s" % (func_desc['result_type'], func_desc['result_desc']))

def split_exec_line(line):
    tokens = []
    inquotes = False
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
    def __init__(self, host, port):
        super().__init__()

        self.client = RpcClient(host, port)

        try:
            self.functions = self.client.rpc_call('__describe_functions')
        except RpcError:
            self.functions = []

        self.prompt = '(rpc) '
        self.intro = "ReflectRpc Shell\n================\n\nType 'help' for available commands\n\nRPC server: %s:%i" % (host, port)

        self.host = host
        self.port = port

    def do_help(self, line):
        if not line:
            print("list - List all RPC functions advertised by the server")
            print("doc  - Shows the documentation of a RPC function")
            print("exec - Execute RPC call")
            print("raw  - Directly send a raw JSON-RPC message to the server")
            print("quit - Quit this program")
            print("help - Print this message. 'help [command]' prints a\n       detailed help message for a command")
            return

        if line == 'exec':
            print("Examples:")
            print("    exec echo \"Hello RPC server\"")
            print("    exec add 4 8")
        elif line == 'raw':
            pass
        elif line == 'doc':
            print("Examples:")
            print("    doc echo")
        elif line == 'list':
            print("List all RPC functions advertised by the server")
        elif line == 'quit':
            print("Quit this program")
        elif line == 'help':
            pass
        else:
            print("No help for unknown command:", line)

    def do_exec(self, line):
        tokens = split_exec_line(line)

        if not tokens:
            return

        method = tokens.pop(0)
        try:
            print("Server replied:", self.client.rpc_call(method, *tokens))
        except reflectrpc.RpcError as e:
            print("Error:", e)

    def do_raw(self, line):
        print(self.client.rpc_call_raw(line))

    def do_doc(self, line):
        if not line:
            print("You have to pass the name of a RPC function: 'doc [function]'")
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

    def do_greet(self, line):
        print("ReflectRpc Shell")

    def do_EOF(self, line):
        return True
