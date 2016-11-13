from common.tools.base64 import Base64Encoder
from common.challenge import CryptoChallenge


class Set1Challenge01(CryptoChallenge):
    
    def expected_value(self):
        return 'SSdtIGtpbGxpbmcgeW91ciBicmFpbiBsaWtlIGEgcG9p'+\
               'c29ub3VzIG11c2hyb29t'

    def value(self):
        target_string = '49276d206b696c6c696e6720796f757220627261696e206c696b652'+\
                        '06120706f69736f6e6f7573206d757368726f6f6d'
        return Base64Encoder().encode_from_hex(target_string)