"""
Contains the Blockchain class which handles the Block insertion and various method to interact with the blockchain.
"""

from collections import defaultdict
from typing import Optional, List, Union

from filechain.blockchain.block import Block


class Blockchain:
    """
    This class represents a blockchain. The Blocks are linked with the hash of the block.
    """

    __latest_block = None

    # this is the first block and have to be equal in every blockchain so each blockchain can be verified
    INITIAL_BLOCK = Block(file_hash=b"",
                          index_all=1,
                          chunk=b"",
                          index=0,
                          previous_block_hash=bytes(0))

    class FileBlockSplitChangedException(Exception):
        """
        Exception when the splitting of a file changed.
        """

    def __init__(self, chain: List[Block] = None):
        """
        Initialise a new Blockchain. When there is no chain to start from the initial Block will be inserted as the
        first block.

        :param chain: list of blocks which will be used as the base for the blockchain
        """

        # NOTE: for a detailed description for this data structure take a look at the "Data Structure" section in the
        # Readme.md

        # contains all block hash to block object mapping
        self.__chain = {}

        # file hash to block content hash mapping and block content to block mapping for block search
        # and file access in O(1);
        # when a block is inserted multiple times final dict value contains a list of all block hashes;
        # this also allows O(1) check if all blocks are in the chain;
        # for this data structure the same file (identified by the file hash) can not be inserted with different block
        # splits -> these blocks violates the data integrity of the blockchain;
        # this dict also contains the total number of blocks for the file as the key "index_all"
        self.__files = defaultdict(lambda: defaultdict(list))

        if chain is None:
            # insert initial block into chain
            self.__chain[Blockchain.INITIAL_BLOCK.block_hash] = Blockchain.INITIAL_BLOCK
            # insert into file to blocks mapping data structure
            self.__files[Blockchain.INITIAL_BLOCK.file_hash][Blockchain.INITIAL_BLOCK.content_hash].append(
                Blockchain.INITIAL_BLOCK.block_hash)
            self.__latest_block = Blockchain.INITIAL_BLOCK
        else:
            self.__latest_block = chain[0]
            for block in chain:
                # insert block into chain
                self.__chain[block.block_hash] = block
                # insert into file to blocks mapping data structure
                self.__files[block.file_hash][block.content_hash].append(block.block_hash)
                self.__files[block.file_hash]["index_all"] = block.index_all

    @property
    def latest_block(self) -> Block:
        """
        Getter for the latest block in the chain.

        :return: the latest block in the chain
        """

        return self.__latest_block

    @property
    def len(self) -> int:
        """
        Getter for the total length of this chain.

        :return: total length of the chain
        """

        return len(self.__chain)

    @property
    def chain(self) -> List[Block]:
        """
        Getter for the whole chain in a incrementing time order (oldest to newest block) as a list.

        :return: list of all blocks ordered from oldest to newsest block
        """

        blocks = []

        block = self.__latest_block
        blocks.append(block)

        while block.previous_block_hash != bytes(0):
            block = self.__chain[block.previous_block_hash]
            blocks.append(block)

        return blocks

    def insert_block(self, new_block: Block) -> None:
        """
        Insert a new block at the end of the blockchain.

        :param new_block: the new block which should be inserted at the end of the blockchain

        :raises FileBlockSplitChanged: when the inserted file block comes from a different file block split aka invalid
                                       block, in this case the new block will not be inserted
        """

        # check if the file was already inserted and the block splits changed
        if file_blocks := self.__files.get(new_block.file_hash, None):
            if new_block.content_hash not in file_blocks and file_blocks["index_all"] + 1 == len(file_blocks):
                raise Blockchain.FileBlockSplitChangedException()
        else:
            # set the total number of file blocks
            self.__files[new_block.file_hash]["index_all"] = new_block.index_all

        # make the chain connection
        new_block.previous_block_hash = self.__latest_block.block_hash

        # insert block into chain
        self.__chain[new_block.block_hash] = new_block

        # insert into file to blocks mapping data structure
        self.__files[new_block.file_hash][new_block.content_hash].append(new_block.block_hash)

        self.__latest_block = new_block

    def get_block_by_hash(self, block_hash: bytes) -> Optional[Block]:
        """
        Get a block in the blockchain by its block hash.

        :param block_hash: hash of the block
        :return: the block when the block exists in the chain otherwise None
        """

        return self.__chain.get(block_hash, None)

    def get_blocks_by_content(self, block: Block) -> List[Block]:
        """
        Get all blocks in the chain which have the same block content as the provided block.

        :param block: the block with the content for which all blocks with the same content should be received
        :return: list of all blocks with this content
        """

        file_blocks = self.__files.get(block.file_hash, {})

        block_hashes = file_blocks.get(block.content_hash, [])

        blocks = []
        for block_hash in block_hashes:
            blocks.append(self.__chain[block_hash])

        return blocks

    def contains_file(self, file_hash: bytes) -> bool:
        """
        Check if the file of the given file hash is completely in the blockchain (e.g all blocks are in the chain).

        :param file_hash: the file hash to check
        :return: True if the file is completely in the the blockchain, False otherwise
        """

        file_blocks = self.__files.get(file_hash, None)

        # the file is not in the chain
        if file_blocks is None:
            return False

        # check the total number of blocks for this file
        return len(file_blocks) == file_blocks["index_all"] + 1

    def get_file_blocks(self, file_hash: bytes) -> List[Block]:
        """
        Get all blocks in the blockchain for a specified file hash. The blocks are ordered by their index.
        The returned blocks are not guaranteed to come from the same client, but can come from several different
        clients.

        :param file_hash: hash of the file which should be received
        :return: list of all blocks which belongs to the file
        """

        file_blocks = self.__files.get(file_hash, {})

        blocks = []

        for content_block_hashes in file_blocks.values():
            # skip the index_all key value mapping
            if isinstance(content_block_hashes, list):
                # always take the first block, since the content is exactly the same it does not matter which block we
                # take from the chain
                block = self.__chain[content_block_hashes[0]]
                blocks.insert(block.index, block)

        return blocks

    def verify_integrity(self) -> bool:
        """
        Verify the integrity of the chain by iterating trough the chain and check if the blocks of the prev block hashes
        are in the chain. Moreover it does check if all blocks of a files are in the chain.

        :return: True if the chain is valid, False otherwise
        """

        curr_block = self.__latest_block

        file_block_numbers = {}

        # do not insert when the file consists only of one block
        if curr_block.index_all - 1 > 0:
            file_block_numbers[curr_block.file_hash] = curr_block.index_all - 1

        # iterate through the chain
        while curr_block.previous_block_hash != bytes(0):
            curr_block = self.__chain.get(curr_block.previous_block_hash, None)

            if curr_block is None:
                return False

            # do not insert when the file consists only of one block
            if curr_block.index_all - 1 > 0:
                if curr_block.file_hash in file_block_numbers:
                    if file_block_numbers[curr_block.file_hash] - 1 == 0:
                        # remove when there are all blocks in the chain
                        del file_block_numbers[curr_block.file_hash]
                    else:
                        # decrement by 1 when there are remaining blocks
                        file_block_numbers[curr_block.file_hash] -= 1
                else:
                    file_block_numbers[curr_block.file_hash] = curr_block.index_all - 1

        # the last block have to be the initial block
        if curr_block.block_hash != Blockchain.INITIAL_BLOCK.block_hash:
            return False

        # check if all blocks of each file is also in the chain
        return len(file_block_numbers) == 0

    def verify_blocks_integrity(self, blocks: List[Block]) -> Union[None, bool]:
        """
        Check the validity of given blocks. A boolean will be returned which indicates the validity. When blocks are
        missing the validity can not be determined and None will be returned.
        To determine the validity of these blocks the current blockchain will be used.

        Note: All values are checked, even if some blocks are already included in the current blockchain. This ensures
              that there are no bad blocks

        :param blocks: list of blocks which should be verified with the current blockchain
        :return: True if the new blocks are valid, False otherwise; when the validity can not determined when blocks are
                 missing None will be returned
        """

        for i in range(len(blocks) - 1, -1, -1):
            block = blocks[i]

            if i == 0:
                # the last block have to link to one of the blocks or we miss blocks between our chain and the other
                if block.previous_block_hash in self.__chain:
                    return True
            elif blocks[i - 1].block_hash != block.previous_block_hash:
                return False

        return None

    def merge_blocks(self, new_blocks: List[Block]) -> List[Block]:
        """
        Solve the conflict between this blockchains and another longer blockchain.
        If there are blocks in this blockchain which are not in the other chain, then these blocks will be added on
        top of the longer chain to preserve the data. All added blocks will be returned as a list.

        :param new_blocks: list of new blocks in incrementing time order (oldest to latest)
        :return: list of blocks which are added to the blockchain during solving the conflict
        """

        # the block which is shared between both chains and which is the start of the conflicted blocks
        starting_conflicted_block = None

        added_blocks = []

        for block in reversed(new_blocks):
            if block.block_hash not in self.__chain:
                # insert block into data structure
                # cant use insert method here since we don't now the same block where both chains are forked
                self.__chain[block.block_hash] = block
                self.__files[block.file_hash][block.content_hash].append(block.block_hash)

                self.__files[block.file_hash]["index_all"] = block.index_all

                added_blocks.append(block)
                if block.previous_block_hash in self.__chain:
                    starting_conflicted_block = self.__chain[block.previous_block_hash]

        added_blocks.reverse()

        # there are no conflicted blocks
        if starting_conflicted_block.block_hash == self.__latest_block.block_hash:
            if added_blocks:
                # update latest block var
                self.__latest_block = added_blocks[-1]
            return added_blocks

        # find all conflicted blocks
        cur_block = self.__latest_block

        self.__latest_block = added_blocks[-1]

        conflicted_blocks = []

        while cur_block.block_hash != starting_conflicted_block.block_hash:
            conflicted_blocks.append(cur_block)
            # remove the conflicted block from the chain data structure
            del self.__chain[cur_block.block_hash]
            self.__files[cur_block.file_hash][cur_block.content_hash].remove(cur_block.block_hash)

            cur_block = self.__chain[cur_block.previous_block_hash]

        conflicted_blocks.reverse()

        for block in conflicted_blocks:
            # add the conflicted blocks at the end of the new blockchain
            self.insert_block(block)
            added_blocks.append(block)

        return added_blocks
