# ReflectRPC #

[![Build Status](https://travis-ci.org/aheck/reflectrpc.svg?branch=master)](https://travis-ci.org/aheck/reflectrpc) [![Documentation Status](https://readthedocs.org/projects/reflectrpc/badge/?version=latest)](http://reflectrpc.readthedocs.io/en/latest/?badge=latest) [![PyPI](https://img.shields.io/pypi/v/reflectrpc.svg)](https://pypi.python.org/pypi/reflectrpc)

Self-describing JSON-RPC services made easy

## Contents

- [What is ReflectRPC?](#what-is-reflectrpc)
- [Installation](#installation)
- [Features](#features)
- [Datatypes](#datatypes)
- [Custom Datatypes](#custom-datatypes)
- [Returning Errors](#returning-errors)
- [Serving RPCs](#serving-rpcs)
- [Generating Documentation](#generating-documentation)
- [Generating Client Code](#generating-client-code)
- [Supported Python Versions](#supported-python-versions)
- [License](#license)
- [How to Contribute](#how-to-contribute)
- [Contact](#contact)

## What is ReflectRPC? ##

ReflectRPC is a Python library implementing an RPC client and server using
the JSON-RPC 1.0 protocol. What sets it apart from most other such
implementations is that it allows the client to get a comprehensive
description of the functions exposed by the server. This includes type
information of parameters and return values as well as human readable
JavaDoc-like descriptions of all fields. To retrieve this information the
client only has to call the special RPC function *\_\_describe\_functions* and
it will get a data structure containing the whole description of all RPC
functions provided by the server.

This ability to use reflection is utilized by the included JSON-RPC shell
*rpcsh*. It can connect to every JSON-RPC server serving line terminated
JSON-RPC 1.0 over a plain socket and can be used to call RPC functions on the
server and display the results. If the server implements the
*\_\_describe\_functions* interface it can also list all RPC functions provided
by the server and show a description of the functions and their parameters.

ReflectRPC does not change the JSON-RPC 1.0 protocol in any way and strives to
be as compatible as possible. It only adds some special builtin RPC calls to
your service to make it self-describing. That way any JSON-RPC 1.0 compliant
client can talk to it while a client aware of ReflectRPC can access the extra
features it provides.

### Example ###

Write a function and register it (including its documentation):
```python
import reflectrpc
import reflectrpc.simpleserver

def add(a, b):
    return int(a) + int(b)

rpc = reflectrpc.RpcProcessor()

add_func = reflectrpc.RpcFunction(add, 'add', 'Adds two numbers', 'int',
        'Sum of the two numbers')
add_func.add_param('int', 'a', 'First int to add')
add_func.add_param('int', 'b', 'Second int to add')
rpc.add_function(add_func)

server = reflectrpc.simpleserver.SimpleJsonRpcServer(rpc, 'localhost', 5500)
server.run()
```

Connect to the server:
> rpcsh localhost 5500

![rpcsh](/pics/intro.png)

Now you can get a list of RPC functions available on the server:

![List remote functions](/pics/list.png)

You can take a look at the documentation of a function and its parameters:

![Show documentation of remote function](/pics/doc.png)

You can call it from *rpcsh*:

![Execute remote function](/pics/exec.png)

Or send a literal JSON-RPC request to the server:

![Send raw JSON-RPC request to server](/pics/raw.png)

To get an overview of what *rpcsh* can do just type *help*:

![Help](/pics/help.png)

## Installation ##

ReflectRPC is available in the Python Package Index. Therefore you can easily
install it with a single command:

> pip install reflectrpc

## Features ##

- JSON-RPC 1.0 (it doesn't get any more simple than that)
- Registration and documentation of RPC calls is done in one place
- Type checking
- Special RPC calls allow to get descriptions of the service, available
    functions, and custom types
- Interactive shell (*rpcsh*) to explore an RPC service and call its functions
- Baseclass for exceptions that are to be serialized and replied to the
    caller while all other exceptions are suppressed as internal errors
- Custom types enum and named hashes (like structs in C)
- Protocol implementation is easily reusable in custom servers
- Twisted-based server that supports TCP and UNIX Domain Sockets, line-based
    plain sockets, HTTP, HTTP Basic Auth, TLS, and TLS client auth
- Client that supports TCP and UNIX Domain Sockets, line-based plain sockets,
    HTTP, HTTP Basic Auth, TLS, and TLS client auth
- Create HTML documentation from a running RPC service by using the program *rpcdoc*
- Create documented client code from a running RPC service with the program *rpcgencode*

## Datatypes ##

ReflectRPC supports the following basic datatypes:

|Type   |Description                        |
|-------|:----------------------------------|
|bool   | true or false                     |
|int    | integer number                    |
|float  | floating point number             |
|string | string                            |
|array  | JSON array with arbitrary content |
|hash   | JSON hash with arbitrary content  |
|base64 | Base64 encoded binary data        |

## Custom Datatypes ##

There are two types of custom datatypes you can define: Enums and named hashes.
For that you have to create an instance of the class *JsonEnumType* or
*JsonHashType*, respectively. This object is filled similarly to *RpcProcessor*
and then registered to your *RpcProcessor* by calling the *add_custom_type*
method.

But lets look at an example:

```python
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

rpc = reflectrpc.RpcProcessor()
rpc.add_custom_type(phone_type_enum)
rpc.add_custom_type(address_hash)
```

This creates an enum named *PhoneType* and a named hash type to hold street
addresses which is named *Address* and registers them to an *RpcProcessor*.
These new types can now be used with all RPC functions that are to be added
to this *RpcProcessor* simply by using their instead of one of the basic
datatype names. All custom type names have to start with an upper-case letter.

Custom types can be inspected in *rpcsh* with the *type* command:

![Inspecting custom datatypes in rpcsh](/pics/customtypes.png)

## Returning Errors ##

A common problem when writing RPC services is returning errors to the user. On
the one hand you want to report as much information about a problem to the
user to make life as easy as possible for him. On the other hand you have to
hide internal errors for security reasons and only make errors produced by the
client visible outside because otherwise you make life easy for people who want
to break into your server.

Therefore when an RPC function is called ReflectRPC catches all exceptions and
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

Now a call to *internal_error()* will yield the following response from the
server:

```javascript
{"result": null, "error": {"name": "InternalError", "message": "Internal error"}, "id": 1}
```

While the result of *json_error()* will look like this:

```javascript
{"result": null, "error": {"name": "JsonRpcError", "message": "User error"}, "id": 2}
```

Both results are as expected. You can send back your own errors over JSON-RPC in
a controlled manner but internal errors are hidden from the client.

## Serving RPCs ##

When you build an RPC service you want to serve it over a network of course.
To make this as easy as possible ReflectRPC already comes with two different
server implementations. The first one is named *SimpleJsonRpcServer* and if
you've read the first example section of this document you've already seen
some example code. *SimpleJsonRpcServer* is a very simple server that serves
JSON-RPC requests over a plain TCP socket, with each JSON message being delimited
by a <CR><LF> linebreak.

That's how it is used:

```python
import reflectrpc
import reflectrpc.simpleserver

# create an RpcProcessor object and register your functions
...

server = reflectrpc.simpleserver.SimpleJsonRpcServer(rpc, 'localhost', 5500)
server.run()
```

Since this server only handles one client at a time you only want to use it for
testing purposes. For production use there is a concurrent server
implementation that is also much more feature rich. It is based on the Twisted
framework.

The following example creates a *TwistedJsonRpcServer* that behaves exactly as
the *SimpleJsonRpcServer* and serves line-delimited JSON-RPC messages over a
plain TCP socket:

```python
import reflectrpc
import reflectrpc.twistedserver

# create an RpcProcessor object and register your functions
...

server = reflectrpc.twistedserver.TwistedJsonRpcServer(rpc, 'localhost', 5500)
server.run()
```

Of course it is powered by Twisted and can handle more than one connection at
a time. This server also support TLS encryption, TLS client authentication and
HTTP as an alternative to line-delimited messages.

The following example code creates a *TwistedJsonRpcServer* that serves JSON-RPC
over HTTP (JSON-RPC message are to be sent as POST requests to '/rpc'). The
connection is encrypted with TLS and the client has to present a valid
certificate that is signed by the CA certificate in the file *clientCA.crt*:

```python
import reflectrpc
import reflectrpc.twistedserver

# create an RpcProcessor object and register your functions
...

jsonrpc = rpcexample.build_example_rpcservice()
server = reflectrpc.twistedserver.TwistedJsonRpcServer(jsonrpc, 'localhost', 5500)
server.enable_tls('server.pem')
server.enable_client_auth('clientCA.crt')
server.enable_http()
server.run()
```

### Custom Servers ###

If you have custom requirements and want to write your own server that is no
problem at all. All you have to do is pass the request string you receive from
your client to the *process_request* method of an *RpcProcessor* object. It
will the reply as a dictionary or *None* in case of a JSON-RPC notification.
If you get a dictionary you encode it as JSON and send it back to the client.

```python
# create an RpcProcessor object and register your functions
...

reply = rpc.process_request(line)

# in case of a notification request process_request returns None
# and we send no reply back
if reply:
    reply_line = json.dumps(reply)
    send_data(reply_line.encode("utf-8"))
```

### Authentication ###

Some protocols like e.g. TLS with client authentication allow to authenticate
the client. Normally, your RPC functions have no idea about in what context
they are called so they also know nothing about authentication. You can change
this by calling the method *require_rpcinfo* on your *RpcFunction* object. Your
function will then be called with a Python dict called *rpcinfo* as its first
parameter which provides your RPC function with some context information:

```python
def whoami(rpcinfo):
    if rpcinfo['authenticated']:
        return 'Username: ' + rpcinfo['username']

    return 'Not logged in'

func = RpcFunction(whoami, 'whoami', 'Returns login information',
        'string', 'Login information')
func.require_rpcinfo()
```

Of course your function has to declare an additional parameter for the
*rpcinfo* dict.

You can also use *rpcinfo* in a custom server to pass your own context
information. Just call *process_request* with your custom *rpcinfo* dict as a
second parameter:

```python
rpcinfo = {
    'authenticated': False,
    'username': None,
    'mydata': 'SOMEUSERDATA'
}

reply = rpc.process_request(line, rpcinfo)
```

This dict will then be passed to every RPC function that declared that it wants
to get the *rpcinfo* dict while all other RPC functions will know nothing about
it.

## Generating Documentation ##

To generate HTML documentation for a running service just call *rpcdoc* from the
commandline and tell it which server to connect to and where to write its
output:

> rpcdoc localhost 5500 doc.html

It will output some formatted HTML documentation for your service:

![HTML Documentation](/pics/htmldocs.png)

## Generating Client Code ##

It is nice to have a generic JSON-RPC client like the one in
*reflectrpc.client.RpcClient*. But it is even nicer to have a client library
that is specifically made for your particular service. Such a client library
should expose all the RPC calls of your service and have docstrings with the
description of your functions and their parameters, as well as the typing
information.

Such a client can be generated with the following command:

> rpcgencode localhost 5500 client.py

And it will look something like this:

![Generated Client](/pics/generated-client.png)

## Supported Python Versions ##

ReflectRPC supports the following Python versions:

- CPython 2.7
- CPython 3.3
- CPython 3.4
- CPython 3.5

Current versions of PyPy should also work.

## License ##

ReflectRPC is licensed under the MIT license

## How to Contribute ##

Pull requests are always welcome.

If you create a pull request for this project you agree that your code will
be released under the terms of the MIT license.

Ideas for improvements can be found in the TODO file.

## Contact ##

Andreas Heck <<aheck@gmx.de>>
