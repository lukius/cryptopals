from common.challenge import CryptoChallenge
from common.tools.misc import FileLines


class ECBEncryptionFinder(object):
    
    BLOCK_SIZE = 16
    
    def __init__(self, hex_strings):
        self.hex_strings = hex_strings
        
    def _less_than(self, number1, number2):
        return number2 is None or number1 < number2
        
    def _build_block_set(self, hex_string):
        return set(hex_string[i:i+2*self.BLOCK_SIZE]
                   for i in range(0, len(hex_string), 2*self.BLOCK_SIZE))
        
    def value(self):
        min_blocks = None
        for hex_string in self.hex_strings:
            block_set = self._build_block_set(hex_string)
            size = len(block_set)
            if self._less_than(size, min_blocks):
                candidate_string = hex_string
                min_blocks = len(block_set)
        return candidate_string
    

class Set1Challenge08(CryptoChallenge):
    
    FILE = 'set1/data/8.txt'
    
    def expected_value(self):
        return 'd880619740a8a19b7840a8a31c810a3d08649af70dc06f4fd5d2d69c744' +\
               'cd283e2dd052f6b641dbf9d11b0348542bb5708649af70dc06f4fd5d2d6' +\
               '9c744cd2839475c9dfdbc1d46597949d9c7e82bf5a08649af70dc06f4fd' +\
               '5d2d69c744cd28397a93eab8d6aecd566489154789a6b0308649af70dc0' +\
               '6f4fd5d2d69c744cd283d403180c98c8f6db1f2a3f9c4040deb0ab51b29' +\
               '933f2c123c58386b06fba186a'

    def value(self):
        hex_strings = FileLines(self.FILE).value()
        return ECBEncryptionFinder(hex_strings).value()