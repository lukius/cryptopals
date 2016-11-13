import random

from common.challenge import CryptoChallenge
from common.ciphers.stream.mt19937 import MersenneTwisterCipher
from common.random.mt19937 import MersenneTwister
from common.tools.misc import RandomByteGenerator
from common.tools.xor import ByteXOR


class CustomMersenneTwisterCipher(object):
    
    def __init__(self):
        self.key = random.randint(0, 65535)
        self.cipher = MersenneTwisterCipher(self.key)
        prefix_size = random.randint(1, 50)
        self.prefix = RandomByteGenerator().value(prefix_size)
        
    def get_key(self):
        return self.key
    
    def encrypt(self, plaintext):
        plaintext = self.prefix + plaintext
        return self.cipher.encrypt(plaintext)


class MersenneTwisterCipherKeyRecover(object):

    PLAINTEXT = 'X'*14
    
    def  __init__(self, cipher):
        self.cipher = cipher

    def _seed_generates_key_bytes(self, seed, key_bytes, prefix_size):
        byte_count = prefix_size + len(key_bytes)
        prng = MersenneTwister(seed)
        byte_string = prng.rand_bytes(byte_count)
        return byte_string[prefix_size:] == key_bytes
        
    def _recover_key_from(self, ciphertext):
        prefix_size = len(ciphertext) - len(self.PLAINTEXT)
        ciphertext = ciphertext[prefix_size:]
        key_bytes = ByteXOR(self.PLAINTEXT, ciphertext).value()
        for seed in range(2**16):
            if self._seed_generates_key_bytes(seed, key_bytes, prefix_size):
                return seed
        
    def value(self):
        ciphertext = self.cipher.encrypt(self.PLAINTEXT)
        return self._recover_key_from(ciphertext)


class Set3Challenge24(CryptoChallenge):
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.cipher = CustomMersenneTwisterCipher()
    
    def expected_value(self):
        return self.cipher.get_key()
    
    def value(self):
        return MersenneTwisterCipherKeyRecover(self.cipher).value()