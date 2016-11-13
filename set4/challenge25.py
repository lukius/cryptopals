from common.tools.base64 import Base64Decoder
from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES, RandomAccessAES
from common.ciphers.block.modes import ECB
from common.tools.misc import RandomByteGenerator
        

class RandomAccessAESDecrypter(object):
    
    def __init__(self, cipher):
        self.cipher = cipher
    
    def decrypt(self, ciphertext):
        ciphertext = ciphertext.bytes()
        return self.cipher.edit(ciphertext, 0, ciphertext).bytes()


class Set4Challenge25(CryptoChallenge):

    FILE = 'set4/data/25.txt'
    KEY = 'YELLOW SUBMARINE'
    BLOCK_SIZE = 16
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        ciphertext = Base64Decoder().decode_file(self.FILE)
        self.plaintext = AES(self.KEY).decrypt(ciphertext, mode=ECB()).bytes()
    
    def expected_value(self):
        return self.plaintext
    
    def value(self):
        key = RandomByteGenerator().value(self.BLOCK_SIZE)
        cipher = RandomAccessAES(key)
        ciphertext = cipher.encrypt(self.plaintext, nonce=0)
        return RandomAccessAESDecrypter(cipher).decrypt(ciphertext)