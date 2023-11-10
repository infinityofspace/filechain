"""
Tests the Block and Blockchain class.
"""

import unittest
from copy import deepcopy

from filechain.blockchain.block import Block
from filechain.blockchain.chain import Blockchain


class BlockTests(unittest.TestCase):
    def test_getter(self):
        file_hash = b"123456"
        index_all = 1
        chunk = b"Earth is our home."
        index = 0
        block = Block(file_hash, index_all, chunk, index)

        self.assertEqual(block.file_hash, file_hash)
        self.assertEqual(block.index_all, index_all)
        self.assertEqual(block.chunk, chunk)
        self.assertEqual(block.index, index)

    def test_setter(self):
        block = Block(b"123456", 1, b"Earth is our home.", 0)

        self.assertEqual(block.previous_block_hash, None)
        self.assertEqual(block.block_hash, None)

        block.previous_block_hash = b"abc123"
        self.assertEqual(block.previous_block_hash, b"abc123")

        self.assertIsNotNone(block.block_hash)

    def test_index_all_zero(self):
        with self.assertRaises(AssertionError):
            Block(b"123456", 0, b"Earth is our home.", 0)

    def test_index_all_negative(self):
        with self.assertRaises(AssertionError):
            Block(b"123456", -1, b"Earth is our home.", 0)

    def test_index_too_large(self):
        with self.assertRaises(AssertionError):
            Block(b"123456", 1, b"Earth is our home.", 5)

    def test_index_negative(self):
        with self.assertRaises(AssertionError):
            Block(b"123456", 1, b"Earth is our home.", -1)


class ChainTests(unittest.TestCase):

    @classmethod
    def setUp(cls) -> None:
        cls.blockchain = Blockchain()

        file_hash = b"abcdefghijkl"
        cls.blockchain.insert_block(Block(file_hash, 2, b"The moon is cool.", 0))
        cls.blockchain.insert_block(Block(file_hash, 2, b"The sun is also cool.", 1))

        file_hash = b"123456abc"
        cls.blockchain.insert_block(Block(file_hash, 3, b"The stars live in the universe.", 0))
        cls.blockchain.insert_block(Block(file_hash, 3, b"We live in the milky way.", 1))
        cls.blockchain.insert_block(Block(file_hash, 3, b"We live on the earth.", 2))

    def test_get_latest_block(self):
        file_hash = b"424242abc"
        new_block = Block(file_hash, 1, b"The moon is next to the earth.", 0)
        self.blockchain.insert_block(new_block)

        # check if the has of the previous block is correctly added to the new block
        self.assertEqual(new_block, self.blockchain.latest_block)

    def test_insert_block(self):
        prev_block = self.blockchain.latest_block

        file_hash = b"424242abc"
        new_block = Block(file_hash, 1, b"The moon is next to the earth.", 0)
        self.blockchain.insert_block(new_block)

        # check if the has of the previous block is correctly added to the new block
        self.assertEqual(new_block.previous_block_hash, prev_block.block_hash)

    def test_insert_block_duplicate(self):
        prev_block = self.blockchain.latest_block

        file_hash = b"abcdefghijkl"
        new_block = Block(file_hash, 2, b"The moon is cool.", 0)
        self.blockchain.insert_block(new_block)

        # check if the has of the previous block is correctly added to the new block
        self.assertEqual(new_block.previous_block_hash, prev_block.block_hash)

    def test_get_blocks_by_content_contains(self):
        new_block = Block(b"424242abc", 1, b"The moon is next to the earth.", 0)
        self.blockchain.insert_block(new_block)
        new_block_2 = Block(b"424242abc", 1, b"The moon is next to the earth.", 0)
        self.blockchain.insert_block(new_block_2)

        self.assertEqual(self.blockchain.get_blocks_by_content(new_block), [new_block, new_block_2])

    def test_get_blocks_by_content_not_contains(self):
        new_block = Block(b"424242abc", 1, b"The moon is next to the earth.", 0)

        self.assertEqual(self.blockchain.get_blocks_by_content(new_block), [])

    def test_get_block_by_hash_contains(self):
        new_block = Block(b"424242abc", 1, b"The moon is next to the earth.", 0)
        self.blockchain.insert_block(new_block)

        self.assertEqual(self.blockchain.get_block_by_hash(new_block.block_hash), new_block)

    def test_get_block_by_hash_not_contains(self):
        self.assertEqual(self.blockchain.get_block_by_hash(b"12345424242"), None)

    def test_contains_file_contains(self):
        file_hash = b"abcd12345"
        new_block = Block(file_hash, 2, b"The moon is next to the earth.", 0)
        self.blockchain.insert_block(new_block)
        new_block = Block(file_hash, 2, b"The moon is next to the earth 2.", 1)
        self.blockchain.insert_block(new_block)

        contains_file = self.blockchain.contains_file(file_hash)

        self.assertTrue(contains_file)

    def test_contains_file_not_contains(self):
        contains_file = self.blockchain.contains_file(b"this_file_hash_does_not_exist")

        self.assertFalse(contains_file)

    def test_get_file_blocks_contains(self):
        file_hash = b"424242abc"
        blocks = [
            Block(file_hash, 4, b"The moon is next to the earth.", 0),
            Block(file_hash, 4, b"The moon is smaller than the earth.", 1),
            Block(file_hash, 4, b"The moon has no moon.", 2),
            Block(file_hash, 4, b"The moon orbits around the earth.", 3)
        ]

        for block in blocks:
            self.blockchain.insert_block(block)

        blocks_from_chain = self.blockchain.get_file_blocks(file_hash)

        # this checks also the correct order of the blocks
        self.assertEqual(blocks_from_chain, blocks)

    def test_get_file_blocks_contains_2(self):
        # insert multiple other blocks between the file blocks
        file_hash = b"424242abc"
        blocks_file = [
            Block(file_hash, 4, b"The moon is next to the earth.", 0),
            Block(file_hash, 4, b"The moon is smaller than the earth.", 1),
            Block(file_hash, 4, b"The moon has no moon.", 2),
            Block(file_hash, 4, b"The moon orbits around the earth.", 3)
        ]

        blocks = [
            blocks_file[0],
            Block(b"123abc", 1, b"Hello world.", 0),
            blocks_file[1],
            Block(b"1234abc", 2, b"Hello world 1.", 0),
            Block(b"1234abc", 2, b"Hello world 2.", 1),
            blocks_file[2],
            blocks_file[3],
            Block(b"1235abc", 1, b"Hello world 42.", 0),
            Block(b"1236abc", 1, b"Hello world 4242.", 0),
        ]

        for block in blocks:
            self.blockchain.insert_block(block)

        blocks_from_chain = self.blockchain.get_file_blocks(file_hash)

        # this checks also the correct order of the blocks
        self.assertEqual(blocks_from_chain, blocks_file)

    def test_get_file_blocks_not_contains(self):
        blocks = self.blockchain.get_file_blocks(b"this_file_hash_does_not_exist")

        self.assertEqual(blocks, [])

    def test_verify_integrity_valid(self):
        self.assertTrue(self.blockchain.verify_integrity())

    def test_verify_integrity_empty_chain(self):
        blockchain = Blockchain()
        self.assertTrue(blockchain.verify_integrity())

    def test_verify_integrity_invalid(self):
        # modify some connections between blocks to make the chain invalid
        prev_block_hash = self.blockchain.latest_block.previous_block_hash
        block = self.blockchain.get_block_by_hash(prev_block_hash)
        block.previous_block_hash = b"this_hash_does_not_exist"

        self.assertFalse(self.blockchain.verify_integrity())

    def test_verify_integrity_missing_file_blocks(self):
        # only insert one out of two blocks
        new_block = Block(b"missing_blocks_file", 2, b"Hello world.", 0)
        self.blockchain.insert_block(new_block)

        self.assertFalse(self.blockchain.verify_integrity())

    def test_invalid_file_block_splitting(self):
        file_hash = b"424242abc"
        new_block = Block(file_hash, 3, b"The moon is next to the earth.", 0)
        self.blockchain.insert_block(new_block)
        new_block = Block(file_hash, 3, b"The moon is next to the earth 2.", 0)
        self.blockchain.insert_block(new_block)
        new_block = Block(file_hash, 3, b"The moon is next to the earth 3.", 0)
        self.blockchain.insert_block(new_block)

        with self.assertRaises(Blockchain.FileBlockSplitChangedException):
            new_block = Block(file_hash, 3, b"The moon is next to the earth.", 1)
            self.blockchain.insert_block(new_block)

    def test_verify_blocks_integrity_valid(self):
        blockchain2 = deepcopy(self.blockchain)

        A = Block(b"123abc123", 2, b"A", 0)
        blockchain2.insert_block(A)
        B = Block(b"123abc123", 2, b"B", 1)
        blockchain2.insert_block(B)
        C = Block(b"4242abc", 1, b"C", 0)
        blockchain2.insert_block(C)

        new_blocks = [A, B, C]

        self.assertTrue(self.blockchain.verify_blocks_integrity(new_blocks))

    def test_verify_blocks_integrity_valid_2(self):
        # valid prev block hash of a block in the middle

        blockchain2 = deepcopy(self.blockchain)

        temp_block_hash = self.blockchain.latest_block.previous_block_hash
        valid_prev_block_hash = self.blockchain.get_block_by_hash(temp_block_hash).block_hash

        A = Block(b"123abc123", 2, b"Test abc 123", 0, valid_prev_block_hash)
        blockchain2.insert_block(A)
        B = Block(b"123abc123", 2, b"Test abc 123 2", 1)
        blockchain2.insert_block(B)
        C = Block(b"4242abc", 1, b"4242 abc test", 0)
        blockchain2.insert_block(C)

        new_blocks = [A, B, C]

        self.assertTrue(self.blockchain.verify_blocks_integrity(new_blocks))

    def test_verify_blocks_integrity_invalid(self):
        # wrong order should return False

        blockchain2 = deepcopy(self.blockchain)

        A = Block(b"123abc123", 2, b"Test abc 123", 0)
        blockchain2.insert_block(A)
        B = Block(b"123abc123", 2, b"Test abc 123 2", 1)
        blockchain2.insert_block(B)
        C = Block(b"4242abc", 1, b"4242 abc test", 0)
        blockchain2.insert_block(C)

        new_blocks = [C, A, B]

        self.assertFalse(self.blockchain.verify_blocks_integrity(new_blocks))

    def test_verify_blocks_integrity_invalid_2(self):
        # modifying B block such that the chain link is wrong

        blockchain2 = deepcopy(self.blockchain)

        A = Block(b"123abc123", 2, b"Test abc 123", 0)
        blockchain2.insert_block(A)
        B = Block(b"123abc123", 2, b"Test abc 123 2", 1)
        blockchain2.insert_block(B)
        C = Block(b"4242abc", 1, b"4242 abc test", 0)
        blockchain2.insert_block(C)

        B.previous_block_hash = b""

        new_blocks = [A, B, C]

        self.assertFalse(self.blockchain.verify_blocks_integrity(new_blocks))

    def test_verify_blocks_integrity_invalid_3(self):
        # valid prev block hash but not valid chain

        blockchain2 = deepcopy(self.blockchain)

        A = Block(b"123abc123", 2, b"A", 0)
        blockchain2.insert_block(A)
        B = Block(b"123abc123", 2, b"B", 1)
        blockchain2.insert_block(B)
        C = Block(b"4242abc", 1, b"C", 0)
        blockchain2.insert_block(C)

        temp_block_hash = self.blockchain.latest_block.previous_block_hash
        valid_prev_block_hash = self.blockchain.get_block_by_hash(temp_block_hash).block_hash
        B.previous_block_hash = valid_prev_block_hash

        new_blocks = [A, B, C]

        self.assertFalse(self.blockchain.verify_blocks_integrity(new_blocks))

    def test_merge_blocks_1(self):
        # current chain: - A - B
        # longer chain 2: - A - B - C
        # merge blocks: A, B, C

        blockchain2 = deepcopy(self.blockchain)

        # new block A
        A = Block(b"A", 1, b"A", 0)
        blockchain2.insert_block(A)
        self.blockchain.insert_block(deepcopy(A))

        # new block B
        B = Block(b"B", 1, b"B", 0)
        blockchain2.insert_block(B)
        self.blockchain.insert_block(deepcopy(B))

        # new block C
        C = Block(b"C", 1, b"C", 0)
        blockchain2.insert_block(C)

        new_blocks = [A, B, C]

        added_blocks = self.blockchain.merge_blocks(new_blocks)

        # only block C should be added
        self.assertEqual(added_blocks, [C])

        # the updated chain should also be valid
        self.assertTrue(self.blockchain.verify_integrity())

    def test_merge_blocks_2(self):
        # current chain: - A - B
        # longer chain 2: - A - B - C - D
        # merge blocks: A, B, C, D

        blockchain2 = deepcopy(self.blockchain)

        # new block A
        A = Block(b"A", 1, b"A", 0)
        blockchain2.insert_block(A)
        self.blockchain.insert_block(deepcopy(A))

        # new block B
        B = Block(b"B", 1, b"B", 0)
        blockchain2.insert_block(B)
        self.blockchain.insert_block(deepcopy(B))

        # new block C
        C = Block(b"C", 1, b"C", 0)
        blockchain2.insert_block(C)

        D = Block(b"D", 1, b"D", 0)
        blockchain2.insert_block(D)

        new_blocks = [A, B, C, D]

        added_blocks = self.blockchain.merge_blocks(new_blocks)

        # only block C should be added
        self.assertEqual(added_blocks, [C, D])

        # the updated chain should also be valid
        self.assertTrue(self.blockchain.verify_integrity())

    def test_merge_blocks_conflict_1(self):
        # current chain: - B - C
        # longer chain 2: - B - D - E
        # merge blocks: D, E
        # conflicted blocks: C

        blockchain2 = deepcopy(self.blockchain)

        B = Block(b"B", 1, b"B", 0)
        blockchain2.insert_block(B)
        self.blockchain.insert_block(deepcopy(B))

        # new block C
        C = Block(b"C", 1, b"C", 0)
        self.blockchain.insert_block(C)

        # new block D
        D = Block(b"D", 1, b"D", 0)
        blockchain2.insert_block(D)

        # new block E
        E = Block(b"E", 1, b"E", 0)
        blockchain2.insert_block(E)

        new_blocks = [D, E]

        added_blocks = self.blockchain.merge_blocks(new_blocks)

        # blocks C, D and E should be added, C should be added at the end
        self.assertEqual(added_blocks, [D, E, C])

        # the updated chain should also be valid
        self.assertTrue(self.blockchain.verify_integrity())

    def test_merge_blocks_conflict_2(self):
        # current chain: - B - C - D
        # longer chain 2: - B - E - F - G
        # merge blocks: E, F, G
        # conflicted blocks: C, D

        blockchain2 = deepcopy(self.blockchain)

        B = Block(b"B", 1, b"B", 0)
        blockchain2.insert_block(B)
        self.blockchain.insert_block(deepcopy(B))

        C = Block(b"C", 1, b"C", 0)
        self.blockchain.insert_block(C)
        D = Block(b"D", 1, b"D", 0)
        self.blockchain.insert_block(D)

        E = Block(b"E", 1, b"E", 0)
        blockchain2.insert_block(E)
        F = Block(b"F", 1, b"F", 0)
        blockchain2.insert_block(F)
        G = Block(b"G", 1, b"G", 0)
        blockchain2.insert_block(G)

        new_blocks = [E, F, G]

        added_blocks = self.blockchain.merge_blocks(new_blocks)

        # blocks C, D and E should be added, C should be added at the end
        self.assertEqual(added_blocks, [E, F, G, C, D])

        # the updated chain should also be valid
        self.assertTrue(self.blockchain.verify_integrity())


if __name__ == '__main__':
    unittest.main()
