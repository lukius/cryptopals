from common.challenge import CryptoChallenge
from common.tools.converters import HexToBytes
from common.tools.misc import FileLines
from common.attacks.xor import SingleByteXORDecrypter


class SingleByteXORFinder(object):
    
    def __init__(self, hex_strings):
        self.hex_strings = hex_strings
        
    def value(self):
        max_score = 0
        for hex_string in self.hex_strings:
            byte_string = HexToBytes(hex_string).value()
            _, plaintext, score = SingleByteXORDecrypter().\
                                    decrypt(byte_string, with_score=True)
            if score > max_score:
                candidate_plaintext = plaintext
                max_score = score
        return candidate_plaintext
    

class Set1Challenge04(CryptoChallenge):
    
    FILE = 'set1/data/4.txt'
    
    def expected_value(self):
        return 'Now that the party is jumping\n'

    def value(self):
        hex_strings = FileLines(self.FILE).value()
        return SingleByteXORFinder(hex_strings).value()