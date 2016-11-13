from common.tools.base64 import Base64Decoder
from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import CBC


class Set2Challenge10(CryptoChallenge):
    
    FILE = 'set2/data/10.txt'
    KEY = 'YELLOW SUBMARINE'
    IV = '\0' * 16
    
    def expected_value(self):
        return open('set1/data/6ans.txt', 'r').read()

    def value(self):
        ciphertext = Base64Decoder().decode_file(self.FILE)
        return AES(self.KEY).decrypt(ciphertext, mode=CBC(self.IV)).bytes()
