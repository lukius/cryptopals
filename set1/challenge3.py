from common.challenge import CryptoChallenge
from common.tools.converters import HexToBytes
from common.attacks.xor import SingleByteXORDecrypter 


class Set1Challenge03(CryptoChallenge):
    
    STRING = '1b37373331363f78151b7f2b783431333d78397828372d363c7'+\
             '8373e783a393b3736'
    
    def expected_value(self):
        return 'Cooking MC\'s like a pound of bacon'

    def value(self):
        byte_string = HexToBytes(self.STRING).value()
        return SingleByteXORDecrypter().decrypt(byte_string)[1]