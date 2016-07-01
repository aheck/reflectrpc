from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import errno
import os
import os.path
import sys
import signal
import socket
import threading
import time

if sys.version_info.major == 2:
    class ConnectionRefusedError(Exception):
        pass

class PortFreeTimeout(Exception):
    def __init__(self, port):
        self.port = port

    def __str__(self):
        return "PortFreeTimeout: Port %d is not free" % (self.port)

class PortReadyTimeout(Exception):
    def __init__(self, port):
        self.port = port

    def __str__(self):
        return "PortReadyTimeout: Port %d is not ready for TCP connections" % (self.port)

def wait_for_unix_socket_gone(socket_path, timeout):
    start_time = time.time()
    sock = None
    while (time.time() - start_time < timeout):
        if not os.path.exists(socket_path):
            return

        time.sleep(0.5)

    raise PortFreeTimeout(socket_path)

def wait_for_unix_socket_in_use(socket_path, timeout):
    start_time = time.time()
    sock = None
    while (time.time() - start_time < timeout):
        if os.path.exists(socket_path):
            return

        time.sleep(0.5)

    raise PortReadyTimeout(socket_path)

def wait_for_free_port(host, port, timeout):
    """
    Waits for a TCP port to become free

    Args:
        host (str): TCP host to wait for
        port (int): TCP port to wait for
        timeout (int): Timeout in seconds until we give up waiting

    Raises:
        PortFreeTimeout: If port doesn't become free after timeout seconds
    """
    start_time = time.time()
    sock = None
    while (time.time() - start_time < timeout):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.close()
        except (ConnectionRefusedError, socket.error) as e:
            if type(e) == socket.error and e.errno != errno.ECONNREFUSED:
                raise e

            # success
            sock.close()
            return

        time.sleep(0.5)

    raise PortFreeTimeout(port)

def wait_for_tcp_port_in_use(host, port, timeout):
    """
    Waits for a TCP port to become ready to accept connections

    Args:
        host (str): TCP host to wait for
        port (int): TCP port to wait for
        timeout (int): Timeout in seconds until we give up waiting

    Raises:
        PortReadyTimeout: If the port is not ready after timeout seconds
    """
    start_time = time.time()
    sock = None
    while (time.time() - start_time < timeout):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.close()
            return
        except (ConnectionRefusedError, socket.error) as e:
            if type(e) == socket.error and e.errno != errno.ECONNREFUSED:
                raise e

            # still waiting
            sock.close()

    raise PortReadyTimeout(port)

class FakeServer(object):
    """
    Runs a TCP server in a thread and replies from a list of pre-defined replies
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.replies = []
        self.requests = []

    def add_reply(self, reply):
        self.replies.append(reply)

    def run(self):
        self.thread = threading.Thread(target = self._run, args = ())
        self.thread.start()

        wait_for_tcp_port_in_use(self.host, self.port, 5)

    def _run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind((self.host, self.port))
        sock.listen(10)

        while self.replies:
            try:
                conn, addr = sock.accept()

                request = conn.recv(4096)
                if not len(request):
                    conn.close()
                    continue

                self.requests.append(request.decode('utf-8'))

                reply = self.replies.pop(0)
                conn.sendall(reply.encode('utf-8'))
                conn.sendall(b'\r\n')
                conn.close()
            except ConnectionResetError:
                pass

        sock.close()

    def stop(self):
        self.thread.join()
        if self.thread.is_alive():
            raise RuntimeError("Failed to join on FakeServer thread")

        wait_for_free_port(self.host, self.port, 5)

class ServerRunner(object):
    """
    Runs a server program in a subprocess and allows to stop it again
    """
    def __init__(self, path, port):
        self.directory = os.path.dirname(path)
        self.server_program = os.path.basename(path)
        self.host = 'localhost'
        self.port = port
        self.pid = None
        self.timeout = 5

    def run(self):
        # we don't fork before we know that the TCP port/UNIX socket is free
        if isinstance(self.port, int):
            wait_for_free_port(self.host, self.port, self.timeout)
        else:
            wait_for_unix_socket_gone(self.port, self.timeout)

        pid = os.fork()

        if not pid:
            # child
            os.chdir(self.directory)

            if self.server_program.endswith('.py'):
                python = sys.executable
                os.execl(python, python, self.server_program)
            else:
                os.execl(self.server_program, self.server_program)
        else:
            # parent
            self.pid = pid

            if isinstance(self.port, int):
                wait_for_tcp_port_in_use(self.host, self.port, self.timeout)
            else:
                wait_for_unix_socket_in_use(self.port, self.timeout)

    def stop(self):
        os.kill(self.pid, signal.SIGINT)
        os.waitpid(self.pid, 0)

        if isinstance(self.port, int):
            wait_for_free_port(self.host, self.port, self.timeout)
        else:
            wait_for_unix_socket_gone(self.port, self.timeout)
