"""
Contains the server for hosting the Filechain and allowing clients and other server to connect and access the filechain.
"""

import logging
import socket
from threading import Thread, Lock

from filechain.blockchain.chain import Blockchain
from filechain.sock.sock import FilechainSocket


class FilechainServer:
    """
    This class represents a server which listens on the specified port and allows other server and clients to access
    the filechain.
    """

    OK = "ok"
    END = "end"
    ERROR = "error"

    UNKNOWN_CMD_ERROR = "unknown_cmd_error"
    INSERT_BLOCKS_CMD = "insert_blocks"
    CONTAINS_FILE_CMD = "contains_file"
    GET_FILE_CMD = "get_file"
    NEW_BLOCKS_AVAILABLE_CMD = "new_blocks_available"
    GET_BLOCK_CMD = "get_block"
    REGISTER_SERVER_CMD = "register_server"

    __known_server_addresses = set()

    def __init__(self, host: str, port: int, connections=20):
        """
        Create a filechain server and initialize an empty Blockchain.

        :param host: the hostname to listen on
        :param port: the port to listen on
        :param connections: number of max concurrent connection of this server
        """

        self.__host = host
        self.__port = port
        self.__connections = connections

        self.__sock_threads_lock = Lock()
        self.__sock_threads = {}

        self.__blockchain = Blockchain()
        self.__blockchain_lock = Lock()

    def handle_client_requests(self, sock: FilechainSocket) -> None:
        """
        Handle the connection to a client or server.

        :param sock: socket of the connection
        """

        cmd = sock.receive()

        if cmd is None:
            logging.error("empty cmd sequence")
            sock.send(FilechainServer.ERROR)
            sock.close()
            return

        if cmd == FilechainServer.INSERT_BLOCKS_CMD:
            sock.send(FilechainServer.OK)

            blocks = []

            block = sock.receive()
            while block != FilechainServer.END:
                blocks.append(block)
                block = sock.receive()

            try:
                # get the blockchain lock to prevent race condition and multiple writer at the same time
                with self.__blockchain_lock:
                    for block in blocks:
                        self.__blockchain.insert_block(block)

                    blockchain_len = self.__blockchain.len

                sock.send(FilechainServer.OK)

                self.__broadcast_new_blocks(blockchain_len, blocks)
            except Blockchain.FileBlockSplitChangedException as exception:
                sock.send((FilechainServer.ERROR, exception))
            finally:
                sock.close()
        elif cmd == FilechainServer.CONTAINS_FILE_CMD:
            sock.send(FilechainServer.OK)

            file_hash = sock.receive()

            contains_file = self.__blockchain.contains_file(file_hash)
            sock.send(contains_file)

            sock.close()
        elif cmd == FilechainServer.GET_FILE_CMD:
            sock.send(FilechainServer.OK)
            file_hash = sock.receive()

            # get all blocks which are from the file
            blocks = self.__blockchain.get_file_blocks(file_hash)
            if len(blocks) == 0:
                sock.send(None)
            else:
                for block in blocks:
                    sock.send(block)
                sock.send(FilechainServer.END)

            sock.close()
        elif cmd == FilechainServer.REGISTER_SERVER_CMD:
            sock.send(FilechainServer.OK)

            new_server_addr = sock.receive()

            # broadcast the current known server addresses of this server
            sock.send(self.__known_server_addresses)

            # add the server to the known server addresses
            self.__known_server_addresses.add(new_server_addr)

            # send the current blockchain so the new server have the current chain of this server
            sock.send(self.__blockchain.chain)

            sock.close()
        elif cmd == FilechainServer.NEW_BLOCKS_AVAILABLE_CMD:
            sock.send(FilechainServer.OK)

            # add this server to the known hosts
            server_addr = sock.receive()
            self.__known_server_addresses.add(server_addr)

            chain_len = sock.receive()
            new_blocks = sock.receive()

            sock.close()

            # we lock the blockchain until we finally synced our chain, this makes it easier to prevent any kind of race
            # condition
            with self.__blockchain_lock:
                # check if the other blockchain is longer than this blockchain;
                # if they have equal length we wait for new blocks so one chain fork have to be longer than the other
                if chain_len > self.__blockchain.len:
                    # verify the new_blocks
                    new_blocks_validity = self.__blockchain.verify_blocks_integrity(new_blocks)
                    if new_blocks_validity is None:
                        # the new blocks can not be verified because we miss some blocks
                        # request the missing blocks until the new blocks can be verified or the chain start is reached

                        while True:
                            missing_block_sock = FilechainSocket(socket.AF_INET, socket.SOCK_STREAM)
                            missing_block_sock.connect(sock.addr)

                            missing_block_sock.send(FilechainServer.GET_BLOCK_CMD)
                            missing_block_sock.send(new_blocks[0].prev_block_hash)
                            missing_block = missing_block_sock.receive()
                            missing_block_sock.close()

                            new_blocks.insert(0, missing_block)

                            new_blocks_validity = self.__blockchain.verify_blocks_integrity(new_blocks)

                            if new_blocks_validity:
                                added_blocks = self.__blockchain.merge_blocks(new_blocks)
                                # broadcast the blocks which are added on longer blockchain to all other server
                                self.__broadcast_new_blocks(self.__blockchain.len, added_blocks)
                            elif new_blocks_validity is not None:
                                print("New blocks chain is not valid. The blocks will be ignored.")
                                break
                    elif new_blocks_validity:
                        added_blocks = self.__blockchain.merge_blocks(new_blocks)
                        # broadcast the blocks which are added on longer blockchain to all other server
                        self.__broadcast_new_blocks(self.__blockchain.len, added_blocks)
                    else:
                        print("New blocks chain is not valid. The blocks will be ignored.")
                elif chain_len < self.__blockchain.len:
                    # notify the server about this new and longer blockchain
                    # send the latest block, since we dont know which blocks the other server is missing
                    # the other server will automatically request other required blocks if needed
                    blocks = [self.__blockchain.latest_block]

                    self.__broadcast_new_blocks(self.__blockchain.len, blocks)
        elif cmd == FilechainServer.GET_BLOCK_CMD:
            sock.send(FilechainServer.OK)
            block_hash = sock.receive()

            sock.send(self.__blockchain.get_block_by_hash(block_hash))

            sock.close()
        else:
            sock.send(FilechainServer.UNKNOWN_CMD_ERROR)
            sock.close()

        # remove itself from the running/active thread dict
        with self.__sock_threads_lock:
            del self.__sock_threads[sock.addr]

    def __broadcast_new_blocks(self, new_chain_len, new_blocks):
        # send new blocks to each known server
        for addr in self.__known_server_addresses:
            broadcast_sock = FilechainSocket(socket.AF_INET, socket.SOCK_STREAM)
            broadcast_sock.connect(addr)

            broadcast_sock.send(FilechainServer.NEW_BLOCKS_AVAILABLE_CMD)

            response = broadcast_sock.receive()
            if response != FilechainServer.OK:
                raise RuntimeError(f"Bad response from server: {response}")

            # send the hostname and port of this server to the other server can also contact this server
            broadcast_sock.send((self.__host, self.__port))

            broadcast_sock.send(new_chain_len)
            broadcast_sock.send(new_blocks)

            broadcast_sock.close()

    def start(self, register_node_addr=None, **kwargs) -> None:
        """
        Start the Filechain server and accept connections. If the register_node_addr is given, then first register this
        server in the network and sync the whole chain.

        :param register_node_addr: address tuple (hostname, port) of the server to contact for registration and sync
        :param kwargs: any other named arguments
        """

        # check if this node should enter an existing network and sync the current blockchain
        if register_node_addr:
            print("Using server on {}:{} to sync and enter the filechain network".format(*register_node_addr))
            self.__known_server_addresses.add(register_node_addr)

            register_node_sock = FilechainSocket(socket.AF_INET, socket.SOCK_STREAM)
            register_node_sock.connect(register_node_addr)

            register_node_sock.send(FilechainServer.REGISTER_SERVER_CMD)

            response = register_node_sock.receive()
            if response != FilechainServer.OK:
                raise RuntimeError(f"Something went wrong: {response}")

            # tell the server on which addr this server listens for other connections
            register_node_sock.send((self.__host, self.__port))

            # receive the known server of this server
            server_addresses = register_node_sock.receive()
            self.__known_server_addresses.update(server_addresses)

            # sync the current blockchain of this network
            chain = register_node_sock.receive()
            self.__blockchain = Blockchain(chain)

            # check the integrity of the synced chain
            if not self.__blockchain.verify_integrity():
                raise RuntimeError("The synced blockchain is not valid.")

        filechain_sock = FilechainSocket(socket.AF_INET, socket.SOCK_STREAM)
        filechain_sock.bind((self.__host, self.__port))
        filechain_sock.listen(self.__connections)

        print("Server started successfully on {}:{}".format(self.__host, self.__port))

        try:
            while True:
                sock, addr = filechain_sock.accept()

                print("connection from {}:{}".format(*addr))

                thread = Thread(target=self.handle_client_requests, args=(sock,))
                with self.__sock_threads_lock:
                    self.__sock_threads[addr] = (thread, sock)
                thread.start()
        finally:
            # close the server socket
            filechain_sock.close()

            # wait for all running threads to finish their work
            for thread, sock in self.__sock_threads.items():
                thread.join()
                try:
                    sock.close()
                except Exception as exception:
                    print(exception)
