"""
Test the FilechainClient and FilechainServer class.
"""

import hashlib
import os
import signal
import time
import unittest
from pathlib import Path

from filechain.client.client import FilechainClient
from filechain.server.server import FilechainServer

HOST = "localhost"
PORT = 12341


class FilechainClientFilechainServerTests(unittest.TestCase):
    def test_send_file(self):
        pid = os.fork()
        if pid == 0:
            server = FilechainServer(HOST, PORT)
            server.start()
        else:
            # wait a few seconds to let the server sock start and listen
            time.sleep(2)

            client = FilechainClient(HOST, PORT)
            client.send_file("../test.txt")

            os.kill(pid, signal.SIGTERM)

    def test_check_file(self):
        pid = os.fork()
        if pid == 0:
            server = FilechainServer(HOST, PORT)
            server.start()
        else:
            # wait a few seconds to let the server sock start and listen
            time.sleep(2)

            try:
                client = FilechainClient(HOST, PORT)
                client.send_file("../test.txt")

                client.check_file("../test.txt")
            finally:
                os.kill(pid, signal.SIGTERM)

    def test_get_file(self):
        pid = os.fork()
        if pid == 0:
            server = FilechainServer(HOST, PORT)
            server.start()
        else:
            # wait a few seconds to let the server sock start and listen
            time.sleep(2)

            try:
                client = FilechainClient(HOST, PORT)
                client.send_file("../test.txt")

                file_hash = hashlib.sha256()

                with open("../test.txt", "rb") as f:
                    chunk = f.read(1024)
                    while chunk:
                        file_hash.update(chunk)
                        chunk = f.read(1024)

                client.get_file(file_hash.hexdigest(), "downloaded_file.txt")

                new_file_hash = hashlib.sha256()

                with open("downloaded_file.txt", "rb") as f:
                    chunk = f.read(1024)
                    while chunk:
                        new_file_hash.update(chunk)
                        chunk = f.read(1024)

                self.assertEqual(file_hash.hexdigest(), new_file_hash.hexdigest())
            finally:
                # delete the temp file
                Path("downloaded_file.txt").unlink(missing_ok=True)

                os.kill(pid, signal.SIGTERM)


if __name__ == '__main__':
    unittest.main()
