"""
Contains the Block class which contains the blockchain data.
"""

import hashlib
from typing import Optional


class Block:
    # pylint note: the block needs all attributes to represents a complete blocks
    """
    This class represents a block in block in the blockchain.
    The dependency to a previous block is implemented with the hash_previous_block value. It uses sha256 to calculate
    the hash of a block.
    """

    # hash of the whole previous block
    __previous_block_hash = None

    # hash of the whole block
    __block_hash = None

    def __init__(self,
                 file_hash: bytes,
                 index_all: int,
                 chunk: bytes,
                 index: int,
                 previous_block_hash: bytes = None) -> None:
        # pylint note: the constructor needs all required attributes to represents a complete blocks
        """
        Creates a new filechain block. This block represents a block in the blockchain.

        :param file_hash: the full hash of the original file (represents the hash variable of the task specification,
                         renamed to not collide with internal python object "hash" name)
        :param index_all: total number of blocks for this file
        :param chunk: 500 byte chunk of the file content
        :param index: index of the block for this file
        :param previous_block_hash: hash of the previous block
        """

        self.__file_hash = file_hash
        assert index_all > 0
        self.__index_all = index_all
        self.__chunk = chunk
        assert index_all > index >= 0
        self.__index = index

        if previous_block_hash is not None:
            self.previous_block_hash = previous_block_hash

        # hash of the content which is independent to other blocks
        self.__content_hash = hashlib.sha256(self.__file_hash
                                             + bytes(self.__index_all)
                                             + self.__chunk
                                             + bytes(self.__index)).digest()

    @property
    def file_hash(self) -> bytes:
        """
        Getter for the file hash of the block.

        :return: the hash of the file to which the block belongs
        """

        return self.__file_hash

    @property
    def index_all(self) -> int:
        """
        Getter for the total number of blocks which belongs to this file.

        :return: number of blocks which belongs to this file
        """

        return self.__index_all

    @property
    def chunk(self) -> bytes:
        """
        Getter for the chunks data.

        :return: the chunk data of this block
        """

        return self.__chunk

    @property
    def index(self) -> int:
        """
        Index of this block to represent the file. Can only be in the range of 0 to index_all.

        :return: the index of this block
        """

        return self.__index

    @property
    def content_hash(self) -> bytes:
        """
        Getter for the content hash.

        :return: sha256 hash of content of this block
        """

        return self.__content_hash

    @property
    def previous_block_hash(self) -> Optional[bytes]:
        """
        Getter for the previous block hash. Can be None if the block is not inserted in the blockchain.

        :return: the previous block hash
        """

        return self.__previous_block_hash

    @previous_block_hash.setter
    def previous_block_hash(self, block_hash: bytes) -> None:
        """
        Setter for the previous block hash. When setting the previous block hash the hash of the full block will be set.

        :param block_hash: the hash of the previous block
        """

        assert block_hash is not None

        self.__previous_block_hash = block_hash

        self.__set_block_hash()

    @property
    def block_hash(self) -> Optional[bytes]:
        """
        Getter for the block hash which is the sha256 hash of the property of the block.

        :return: sha256 hash of this block as bytes; can be None if the previous block hash is not set
        (e.g the block is not inserted in the chain)
        """

        return self.__block_hash

    def __set_block_hash(self):
        """
        Calculate the sha256 hash for this block and set the _block_hash property.
        The hash will be generated from the bytes representations of the class attributes with the following order:
            file_hash + index_all + chunk + + index + hash_previous
        """

        assert self.__previous_block_hash is not None

        self.__block_hash = hashlib.sha256(self.__file_hash
                                           + bytes(self.__index_all)
                                           + self.__chunk
                                           + bytes(self.__index)
                                           + self.__previous_block_hash).digest()
