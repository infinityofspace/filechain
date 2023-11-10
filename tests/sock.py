"""
Test the FilechainSocket class.
"""

import os
import socket
import time
import unittest

from filechain.sock.sock import FilechainSocket

HOST = "localhost"
PORT = 12345


class FilechainSocketTests(unittest.TestCase):
    def test_connection(self):
        addr = (HOST, PORT)

        pid = os.fork()
        if pid == 0:
            # wait a few seconds to let the server sock start and listen
            time.sleep(2)

            sock = FilechainSocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)
            sock.close()
        else:
            # the main process runs the client
            sock = FilechainSocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(addr)

            sock.listen(1)

            s, addr = sock.accept()
            sock.close()
            s.close()

            # if the connection was not stabled we would not reach this
            self.assertTrue(True)

    def test_send_arbitrary_data(self):
        addr = (HOST, PORT)

        data = {"abc": 42}

        pid = os.fork()
        if pid == 0:
            # wait a few seconds to let the server sock start and listen
            time.sleep(2)

            sock = FilechainSocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(addr)

            sock.send(data)
            sock.close()

            return
        else:
            # the main process runs the client
            sock = FilechainSocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(addr)
            sock.listen(1)

            s, addr = sock.accept()

            # close original socket
            sock.close()

            response = s.receive()

            self.assertEqual(response, data)

            s.close()


if __name__ == '__main__':
    unittest.main()
