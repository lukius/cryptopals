from common.tools.base64 import Base64Decoder
from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import ECB

    
class Set1Challenge07(CryptoChallenge):
    
    ANSWER_FILE = 'set1/data/6ans.txt'
    FILE = 'set1/data/7.txt'
    
    def expected_value(self):
        return open(self.ANSWER_FILE, 'r').read()

    def value(self):
        key = 'YELLOW SUBMARINE'
        ciphertext = Base64Decoder().decode_file(self.FILE)
        return AES(key).decrypt(ciphertext, mode=ECB()).bytes()