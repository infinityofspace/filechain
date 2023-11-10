"""
Contains the client for connecting to a Filechain server and use specific server methods.
"""

import hashlib
from pathlib import Path
from typing import Union

from filechain.blockchain.block import Block
from filechain.config.const import CHUNK_SIZE
from filechain.server.server import FilechainServer
from filechain.sock.sock import FilechainSocket


class FilechainClient:
    """
    This class represents a client which connects to a filechain server and allowes to send, check and get a file in the
    blockchain.
    """

    def __init__(self, host: str, port: int) -> None:
        """
        Initialize a new Filechain client.

        :param host: hostname of the server to connect to
        :param port: port of the server to connect to
        """

        self.__host = host
        self.__port = port

    def __get_sock(self) -> FilechainSocket:
        filechain_sock = FilechainSocket()
        filechain_sock.connect((self.__host, self.__port))

        return filechain_sock

    def send_file(self, file_path: Union[Path, str], **kwargs) -> None:
        """
        Sends a file which should be send to the server and inserted into the blockchain.

        :param file_path: filepath of the file
        :param kwargs: other named arguments
        """

        file_path = Path(file_path)

        file_hash_digest, chunks = FilechainClient.__read_file(file_path)

        print("sha256 hash: {}".format(file_hash_digest.decode("utf-8")))

        filechain_sock = self.__get_sock()

        filechain_sock.send(FilechainServer.INSERT_BLOCKS_CMD)
        response = filechain_sock.receive()
        if response != FilechainServer.OK:
            raise RuntimeError(f"Something went wrong: {response}")

        # generate Block candidates and send them to the server
        for i, chunk in enumerate(chunks):
            block = Block(file_hash=file_hash_digest, index_all=len(chunks), chunk=chunk, index=i)
            filechain_sock.send(block)
        filechain_sock.send(FilechainServer.END)

        response = filechain_sock.receive()

        filechain_sock.close()

        if response == FilechainServer.OK:
            print("File was successfully send to the server.")
        else:
            raise RuntimeError(f"Something went wrong: {response}")

    def check_file(self, file_path: Union[Path, str], **kwargs) -> None:
        """
        Check if the given file exists in the Filechain.

        :param file_path: filepath of the file
        :param kwargs: any other named arguments
        """

        file_path = Path(file_path)

        file_hash_digest, _ = FilechainClient.__read_file(file_path)

        print("sha256 hash: {}".format(file_hash_digest.decode("utf-8")))

        filechain_sock = self.__get_sock()

        filechain_sock.send(FilechainServer.CONTAINS_FILE_CMD)
        response = filechain_sock.receive()
        if response != FilechainServer.OK:
            raise RuntimeError(f"Bad response from server: {response}")

        filechain_sock.send(file_hash_digest)

        contains_file = filechain_sock.receive()

        filechain_sock.close()

        if not isinstance(contains_file, bool):
            raise RuntimeError(f"Bad response from server: {response}")

        print("file in filechain: {}".format(contains_file))

    def get_file(self, file_hash: str, file_path: Union[Path, str], **kwargs) -> None:
        """
        Get the file from the Filechain and save it to a local file.

        :param file_hash: sha256 digest from the hash of the file
        :param file_path: path of the file where the file from the Filechain will be saved
        :param kwargs: any other named arguments
        """

        file_path = Path(file_path)

        if file_path.exists():
            raise FileNotFoundError("The path to the output file already exist.")

        filechain_sock = self.__get_sock()

        filechain_sock.send(FilechainServer.GET_FILE_CMD)
        response = filechain_sock.receive()
        if response != FilechainServer.OK:
            raise RuntimeError(f"Bad response from server: {response}")

        file_hash = bytes(file_hash, "utf-8")

        filechain_sock.send(file_hash)
        block = filechain_sock.receive()

        if block is None:
            print("ERROR: The file is not in the filechain.")
        else:
            with open(str(file_path), "wb") as file:
                while block != FilechainServer.END:
                    file.write(block.chunk)
                    block = filechain_sock.receive()

            print("File successfully received.")

        filechain_sock.close()

    @staticmethod
    def __read_file(file_path: Union[Path, str]):
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError("The file does not exist.")

        file_hash = hashlib.sha256()

        chunks = []

        # first load the whole file as chunks and calculate file hash
        # this can be optimized to support any file size (especially huge files) with an generator but then we have
        # to iter 2 times (first for the file hash and the second for file content)
        with open(str(file_path), "rb") as file:
            chunk = file.read(CHUNK_SIZE)
            while chunk:
                file_hash.update(chunk)
                chunks.append(chunk)

                chunk = file.read(CHUNK_SIZE)

        return bytes(file_hash.hexdigest(), "utf-8"), chunks
