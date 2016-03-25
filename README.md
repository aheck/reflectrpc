# ReflectRPC #

ReflectRPC is a Python library implementing a RPC client and server using the JSON-RPC 1.0 protocol. What sets it apart from most other such implementations is that it allows the client to get a comprehensive description of the functions exposed by the server. This includes type information of parameters and return values as well as human readable JavaDoc-like descriptions of all fields. To retrieve this information the client only has to call the special RPC function *\_\_describe\_functions* and it will get a data structure containing the whole description of all RPC functions provided by the server.

This ability to use reflection is utilized by the included JSON-RPC shell *rpcsh*. It can connect to every JSON-RPC server serving line terminated JSON-RPC 1.0 over a plain socket and can be used to call RPC functions on the server and display the results. If the server implements the *\_\_describe\_functions* interface it can also list all RPC functions provided by the server and show a description of the functions and their parameters.

## Example ##

Write a function and register it (including its documentation):
```python
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

## Datatypes ##

ReflectRPC supports the following datatypes:

|Type   |Description                        |
|-------|:----------------------------------|
|bool   | true or false                     |
|int    | integer number                    |
|float  | floating point number             |
|string | string                            |
|array  | JSON array with arbitrary content |
|hash   | JSON hash with arbitrary content  |
|base64 | Base64 encoded binary data        |

## Reporting Errors ##

A common problem when writing RPC services is reporting errors to the user. On
the one hand you want to report as much information about a problem to the
user to make life as easy as possible for him. On the other hand you have to
hide internal errors for security reasons and only make errors produced by the
client visible outside because otherwise you make life easy for people who want
to break into your server.

Therefore when a RPC function is called ReflectRPC catches all exceptions and
returns only a generic "internal error" in the JSON-RPC reply. To return more
information about an error to the user you can derive custom exception classes
from *JsonRpcError*. All exceptions that are of this class or a subclass
are serialized and returned to the client.

This allows to serialize exceptions and return them to the user but at the
same time gives you fine-grained control over what error information actually
leaves the server.

### Example ###

We can define two RPC functions named *internal_error()* and *json_error()* to
demonstrate this behaviour. The first function raises a *ValueError*. Internal
exceptions like this must not be visible to the client. The function
*json_error()* on the other hand raises an exception of type *JsonRpcError*.
Since this exception is specially defined for the sole purpose of being
returned to the client it will be serialized and returned as a JSON-RPC error
object.

```python
def internal_error():
    raise ValueError("This should not be visible to the client")

def json_error():
    raise reflectrpc.JsonRpcError("User-visible error")

rpc = reflectrpc.RpcProcessor()

error_func1 = reflectrpc.RpcFunction(internal_error, 'internal_error', 'Produces internal error',
        'bool', '')
error_func2 = reflectrpc.RpcFunction(json_error, 'json_error', 'Raises JsonRpcError',
        'bool', '')

rpc.add_function(error_func1)
rpc.add_function(error_func2)
```

Now a call to *internel_error()* will yield the following response from the
server:

```javascript
{"result": null, "error": "Internal error", "id": 1}
```

While the result of *json_error()* will look like this:

```javascript
{"result": null, "error": {"name": "JsonRpcError", "message": "User error"}, "id": 2}

Both results are as expected. You can send back your own errors over JSON-RPC in
a controlled manner but internal errors are hidden from the client.
```

## Contact ##

Andreas Heck <<aheck@gmx.de>>
