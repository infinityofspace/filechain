"""
This module contains the socket Class for the filechain.
"""

import pickle
import socket
from typing import Any, Tuple, Union

from filechain.config.const import SOCKET_BUFFER_SIZE


class FilechainSocket:
    """
    The socket class can not be inherited (see: https://www.mail-archive.com/python-list@python.org/msg126934.html)
    so we have to use a wrapper class instead.
    """

    SOCK_DATA_END = b"<FILECHAIN_DATA_END>"

    __data_buffer = b""

    __addr = None

    def __init__(self, family=-1, sock_type=-1, sock=None, addr=None, **kwargs):
        if sock:
            self.__sock = sock
            self.__addr = addr
        else:
            self.__sock = socket.socket(family=family, type=sock_type, **kwargs)

    def send(self, data) -> None:
        """
        Send the provided data to the server.
        The data will be converted to bytes by pickle.

        :param data: the data to be send
        """

        pickle_data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)

        self.__sock.send(pickle_data)
        self.__sock.send(FilechainSocket.SOCK_DATA_END)

    def receive(self):
        """
        Receive data from the socket.
        The received data will be converted to the python object with pickle
        """

        buffer = self.__data_buffer

        # search for the end socket keyword data
        end_pattern_idx = buffer.find(FilechainSocket.SOCK_DATA_END)
        while end_pattern_idx == -1:
            chunk = self.__sock.recv(SOCKET_BUFFER_SIZE)
            if not chunk:
                raise RuntimeError("socket connection broken")
            buffer += chunk
            end_pattern_idx = buffer.find(FilechainSocket.SOCK_DATA_END)

        self.__data_buffer = buffer[end_pattern_idx + len(FilechainSocket.SOCK_DATA_END):]

        return pickle.loads(buffer[:end_pattern_idx])

    def connect(self, addr: Union[tuple, str, bytes]) -> None:
        """
        Connect the socket to the given address.

        :param addr: address (host, port) to connect to
        """

        self.__addr = addr

        self.__sock.connect(addr)

    def accept(self) -> Tuple[Any, Any]:
        """
        Accept a socket connection and return an new FilechainSocket for this connection.

        :return: tuple (FilechainSocket, address) of this accepted connection
        """

        sock, addr = self.__sock.accept()

        filechain_sock = FilechainSocket(sock=sock, addr=addr)

        return filechain_sock, addr

    def bind(self, addr) -> None:
        """
        Bind the given address.

        :param addr: address (host, port) to bind
        """

        self.__sock.bind(addr)

    def listen(self, *args, **kwargs) -> None:
        """
        Start waiting for connection to this socket.

        :param args: any positional argument
        :param kwargs: any named arguments
        """

        self.__sock.listen(*args, **kwargs)

    def close(self) -> None:
        """
        Close this socket.
        """

        self.__sock.close()

    @property
    def addr(self) -> Tuple[str, int]:
        """
        Getter for the socket address.

        :return: the socket address as tuple (host, port)
        """

        return self.__addr
