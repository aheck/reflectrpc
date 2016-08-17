*********
Changelog
*********

0.7.5 (2016-08-17)
==================

- Fixes rpcsh crash with Python 2.7

0.7.4 (2016-08-11)
==================

- RPC functions run by the Twisted server can now return Deferreds to implement concurrent RPC services
- Linux sys info example service

0.7.3 (2016-07-24)
==================

- Support for UNIX domain sockets
- New rpcgencode tool to generate client code for a running RPC service

0.7.2 (2016-07-01)
==================

- Bugfixes
- Automatic generation of service documentation with the new rpcdoc tool
- HTTP Basic Auth for client and Twisted server
- Mechanism for passing context to RPC functions (rpcinfo)

0.7.1 (2016-05-12)
==================

- Adds missing package dependencies

0.7.0 (2016-05-11)
==================

- First release
