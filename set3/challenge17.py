import random

from common.tools.base64 import Base64Decoder
from common.challenge import CryptoChallenge
from common.tools.padders import InvalidPaddingException, PKCS7Unpadder
from common.tools.misc import RandomByteGenerator, FileLines
from common.tools.xor import ByteXOR
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import CBC


class CBCPaddingOracle(object):

    def __init__(self, key, iv):
        self.cipher = AES(key)
        self.iv = iv
        
    def has_valid_padding(self, ciphertext):
        try:
            self.cipher.decrypt(ciphertext, mode=CBC(self.iv))
            has_valid_padding = True
        except InvalidPaddingException:
            has_valid_padding = False
        return has_valid_padding
    

class CBCPaddingOracleAttack(object):
    
    def __init__(self, oracle):
        self.oracle = oracle
        
    def _decrypt_block(self, block, previous_block):
        return CBCPaddingOracleBlockDecrypter(self.oracle, block,
                                              previous_block).decrypt()
        
    def value(self, ciphertext, iv):
        plaintext = str()
        for (i, block) in enumerate(ciphertext):
            previous_block = iv if i == 0 else ciphertext.get_block(i-1)
            decrypted_block = self._decrypt_block(block, previous_block)
            if ciphertext.is_last_block_index(i):
                decrypted_block = PKCS7Unpadder(decrypted_block).value()
            plaintext += decrypted_block
        return plaintext
    

class CBCPaddingOracleBlockDecrypter(object):
    
    def __init__(self, oracle, block, previous_block):
        self.oracle = oracle
        self.block = block
        self.previous_block = previous_block
        self.block_size = len(block)
        # List of possible plaintexts for this block.
        self.plaintext_candidates = [str()]
    
    def _get_valid_padding_bytes(self, pad_size, tampered_block):
        index = self.block_size - pad_size
        valid_bytes = list()
        for byte in range(256):
            probe = tampered_block[:index] + chr(byte) + tampered_block[index+1:]
            ciphertext = probe + self.block
            if self.oracle.has_valid_padding(ciphertext):
                valid_bytes.append(byte)
        return valid_bytes

    def _find_valid_bytes(self, pad_size, plaintext):
        # Modify our previous block in order to make the padding bytes appear
        # during decryption. If j is the index of a plaintext byte 
        # already discovered, the block before our target block will have:
        # tampered_block[j] := previous_block[j] XOR plaintext[j] XOR pad_size
        # In consequence, when decrypting our target block, the following
        # operation will take place:
        # tampered_block[j] XOR (previous_block[j] XOR plaintext[j])
        # which follows from CBC encryption/decryption.
        # Thus, byte j of the decrypted block will equal pad_size.
        padding = chr(pad_size)*len(plaintext)
        tampered_block = ByteXOR(plaintext, padding, self.previous_block).\
                         value()
        return self._get_valid_padding_bytes(pad_size, tampered_block)

    def _get_valid_plaintext_candidate(self, pad_size):
        for candidate in self.plaintext_candidates:
            valid_bytes = self._find_valid_bytes(pad_size, candidate)
            # If we can keep finding bytes, this must be the actual plaintext.
            if valid_bytes:
                return candidate
            
    def _recover_plaintext_byte(self, pad_size, byte):
        # Since this byte enabled a valid padding, we have that
        # pad_size = plaintext[byte_index] XOR previous_block[byte_index]
        #                                  XOR probe[byte_index]
        # (where probe[byte_index] = byte).
        # Thus, 
        # plaintext[byte_index] = pad_size XOR byte
        #                                  XOR previous_block[byte_index] 
        byte_index = self.block_size - pad_size
        return chr(pad_size ^ byte ^ ord(self.previous_block[byte_index]))
        
    def decrypt(self):
        # Iterate pad sizes and get potential byte candidates for each one.
        # For pad size i, we will discover the plaintext byte at position
        # block_size - i. 
        for pad_size in range(1, self.block_size+1):
            if len(self.plaintext_candidates) > 1:
                # If we have more than one sequence of bytes, discard the
                # invalid ones and keep the one that is correct.
                # This typically happens for the last block, which is padded.
                # E.g., when guessing the last byte, we might find two possible
                # candidates, each one corresponding to a perfectly valid
                # padding:
                # ... 4 4 4 1
                # ... 4 4 4 4
                candidate = self._get_valid_plaintext_candidate(pad_size)
            else:
                candidate = self.plaintext_candidates[0]
            # Find bytes for position block_size - pad_size that make valid
            # paddings.
            valid_bytes = self._find_valid_bytes(pad_size, candidate)
            # From those bytes, recover the actual plaintext values.
            candidate_bytes = map(lambda byte: self._recover_plaintext_byte(pad_size, byte),
                                  valid_bytes)
            self.plaintext_candidates = map(lambda byte: byte + candidate,
                                            candidate_bytes)
        return self.plaintext_candidates[0]

    
class Set3Challenge17(CryptoChallenge):

    BLOCK_SIZE = 16
    INPUT_FILE = 'set3/data/17.txt'
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.plaintext = self._choose_plaintext()

    def _choose_plaintext(self):
        plaintexts = FileLines(self.INPUT_FILE).value()
        plaintext = random.choice(plaintexts) 
        return Base64Decoder().decode(plaintext)

    def expected_value(self):
        return self.plaintext
    
    def value(self):
        random_generator = RandomByteGenerator()
        key = random_generator.value(self.BLOCK_SIZE)
        iv = random_generator.value(self.BLOCK_SIZE)
        ciphertext = AES(key).encrypt(self.plaintext, mode=CBC(iv))
        oracle = CBCPaddingOracle(key, iv)
        return CBCPaddingOracleAttack(oracle).value(ciphertext, iv)