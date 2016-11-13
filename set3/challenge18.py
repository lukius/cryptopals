from common.tools.base64 import Base64Decoder
from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import CTR


class Set3Challenge18(CryptoChallenge):

    STRING = 'L77na/nrFsKvynd6HzOoG7GHTLXsTVu9qvY/2syLXzhPweyyMTJULu/6/kXX0K'+\
             'SvoOLSFQ=='
    KEY = 'YELLOW SUBMARINE'

    def expected_value(self):
        return 'Yo, VIP Let\'s kick it Ice, Ice, baby Ice, Ice, baby '
    
    def value(self):
        ciphertext = Base64Decoder().decode(self.STRING)
        return AES(self.KEY).decrypt(ciphertext, mode=CTR(nonce=0)).bytes()
