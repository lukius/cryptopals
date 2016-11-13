from common.challenge import CryptoChallenge
from common.tools.xor import HexXOR


class Set1Challenge02(CryptoChallenge):
    
    def expected_value(self):
        return '746865206b696420646f6e277420706c6179'

    def value(self):
        target_string1 = '1c0111001f010100061a024b53535009181c'
        target_string2 = '686974207468652062756c6c277320657965'
        return HexXOR(target_string1, target_string2).value()