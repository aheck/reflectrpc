from __future__ import unicode_literals
from builtins import bytes, dict, list, int, float, str

import errno
import os
import os.path
import sys
import signal
import socket
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

class ServerRunner(object):
    """
    Runs a server program in a subprocess and allows to stop it again
    """
    def __init__(self, path, port):
        self.directory = os.path.dirname(path)
        self.server_program = os.path.basename(path)
        self.port = 5500
        self.pid = None
        self.timeout = 5

    def wait_for_free_port(self):
        """
        Waits for a TCP port to become free

        Raises:
            PortFreeTimeout: If port doesn't become free after self.timeout seconds
        """
        start_time = time.time()
        sock = None
        while (time.time() - start_time < self.timeout):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('localhost', self.port))
                sock.close()
            except (ConnectionRefusedError, socket.error) as e:
                if type(e) == socket.error and e.errno != errno.ECONNREFUSED:
                    raise e

                # success
                sock.close()
                return

            time.sleep(0.5)

        raise PortFreeTimeout(self.port)

    def wait_for_port_in_use(self):
        """
        Waits for a TCP port to be ready for connections

        Raises:
            PortReadyTimeout: If the port is not ready after self.timeout seconds
        """
        start_time = time.time()
        sock = None
        while (time.time() - start_time < self.timeout):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('localhost', self.port))
                sock.close()
                return
            except (ConnectionRefusedError, socket.error) as e:
                if type(e) == socket.error and e.errno != errno.ECONNREFUSED:
                    raise e

                # still waiting
                sock.close()

        raise PortReadyTimeout(self.port)

    def run(self):
        # we don't fork before we know that the TCP port is free
        self.wait_for_free_port()

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
            self.wait_for_port_in_use()

    def stop(self):
        os.kill(self.pid, signal.SIGINT)
        os.waitpid(self.pid, 0)
        self.wait_for_free_port()
