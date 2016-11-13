from common.challenge import CryptoChallenge
from common.ciphers.block.tools import ECBDecrypter, ECBEncryptionOracle
from common.tools.misc import RandomByteGenerator, AllEqual


class ECBEncryptionOracleWithRandomPrefix(ECBEncryptionOracle):
    
    def __init__(self):
        ECBEncryptionOracle.__init__(self)
        self.random_prefix = RandomByteGenerator().value()
    
    def encrypt(self, plaintext):
        plaintext = self.random_prefix + plaintext
        return ECBEncryptionOracle.encrypt(self, plaintext)


class ECBDecrypterForRandomPrefixOracle(ECBDecrypter):
    
    BLOCK_SIZE = 16
    EXPECTED_EQUAL_BLOCKS = 3
    
    def _search_equal_blocks_starting_point(self, ciphertext):
        for index, block in enumerate(ciphertext):
            next_blocks = [ciphertext.get_block(i)
                           for i in range(index+1,
                                          index+self.EXPECTED_EQUAL_BLOCKS)]
            all_blocks_equal = AllEqual(next_blocks).value(block)
            if all_blocks_equal:
                return index 
    
    def _discover_random_prefix_bypass_values(self):
        probe = 'X'*((1+self.EXPECTED_EQUAL_BLOCKS)*self.block_size - 1)
        ciphertext = self.oracle.encrypt(probe)
        start_index = self._search_equal_blocks_starting_point(ciphertext)
        target_block = ciphertext.get_block(start_index)
        for k in xrange(self.block_size, 2*self.block_size):
            output = self.oracle.encrypt('X'*k)
            if output.get_block(start_index) == target_block:
                #  * At start_index, non-random blocks start to appear.
                #  * Thus, we must ignore the first start_index blocks.
                self.skip_blocks = start_index
                #  * We have just found that k bytes fill the last random-byte
                #    block and make one block worth of Xs.
                #  * Thus, we must pad the last random-byte block with exactly
                #    k - block_size  bytes.
                self.pad_string = 'X'*(k - self.block_size)
                return
        
    def value(self):
        # TODO: fix block size calculation.
        self.block_size = self.BLOCK_SIZE
        self._discover_random_prefix_bypass_values()
        return ECBDecrypter._decrypt_string(self)
        

class Set2Challenge14(CryptoChallenge):

    def expected_value(self):
        return 'Rollin\' in my 5.0\n' +\
               'With my rag-top down so my hair can blow\n' +\
               'The girlies on standby waving just to say hi\n' +\
               'Did you stop? No, I just drove by\n'

    def value(self):
        oracle = ECBEncryptionOracleWithRandomPrefix()
        return ECBDecrypterForRandomPrefixOracle(oracle).value()