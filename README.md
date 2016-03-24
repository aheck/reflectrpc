# ReflectRPC

ReflectRPC is a Python library implementing a RPC client and server using the JSON-RPC 1.0 protocol. What sets it apart from most other such implementations is that it allows the client to get a comprehensive description of the functions exposed by the server. This includes type information of parameters and return values as well as human readable JavaDoc-like descriptions of all fields. To retrieve this information the client only has to call the special RPC function *\_\_describe\_functions* and it will get a data structure containing the whole description of all RPC functions provided by the server.

This ability to use reflection is utilized by the included JSON-RPC shell *rpcsh*. It can connect to every JSON-RPC server serving line terminated JSON-RPC 1.0 over a plain socket and can be used to call RPC functions on the server and display the results. If the server implements the *\_\_describe\_functions* interface it can also list all RPC functions provided by the server and show a description of the functions and their parameters.

## Example

Write a function and register it (including its documentation):
```
def add(a, b):
    return int(a) + int(b)

jsonrpc = reflectrpc.RpcProcessor()

add_func = reflectrpc.RpcFunction(add, 'add', 'Adds two numbers', 'int',
        'Sum of the two numbers')
add_func.add_param('int', 'a', 'First int to add')
add_func.add_param('int', 'b', 'Second int to add')
jsonrpc.add_function(add_func)

server = reflectrpc.simpleserver.SimpleJsonRpcServer(jsonrpc, 'localhost', 5500)
server.run()
```

Connect to the server:
> ./rpcsh localhost 5500

![rpcsh](/pics/intro.png)

Now you can get a list of RPC functions available on the server:

![List remote functions](/pics/list.png)

You can take a look at the documentation of a function and its parameters:

![Show documentation of remote function](/pics/doc.png)

You can call it from *rpcsh*

![Execute remote function](/pics/exec.png)

Or send a literal JSON-RPC request to the server

![Send raw JSON-RPC request to server](/pics/raw.png)

To get an overview of what *rpcsh* can do just type *help*

![Help](/pics/help.png)
