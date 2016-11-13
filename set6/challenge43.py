from common.challenge import CryptoChallenge
from common.hash.sha1 import SHA1
from common.math.invmod import ModularInverse
from common.math.modexp import ModularExp
from common.tools.converters import HexToBytes, HexToInt, IntToHex


class DSAPrivateKeyCracker(object):
    
    MAX_K = 65536
    
    def __init__(self, p, q, g):
        self.p = p
        self.q = q
        self.g = g
        
    def _get_key_from(self, k, h, r, s):
        r_inv = ModularInverse(self.q).value(r)
        return ((s*k - h) * r_inv) % self.q
    
    def _get_r_from(self, k):
        return ModularExp(self.p).value(self.g, k) % self.q
    
    def crack(self, message, signature):
        h = SHA1().int_hash(message)
        r, s = signature
        for k in range(self.MAX_K):
            r_k = self._get_r_from(k)
            if r != r_k:
                continue
            return self._get_key_from(k, h, r, s)
            
            
class Set6Challenge43(CryptoChallenge):
    
    P = '800000000000000089e1855218a0e7dac38136ffafa72eda7'+\
        '859f2171e25e65eac698c1702578b07dc2a1076da241c76c6'+\
        '2d374d8389ea5aeffd3226a0530cc565f3bf6b50929139ebe'+\
        'ac04f48c3c84afb796d61e5a4f9a8fda812ab59494232c7d2'+\
        'b4deb50aa18ee9e132bfa85ac4374d7f9091abc3d015efc87'+\
        '1a584471bb1'
        
    Q = 'f4f47f05794b256174bba6e9b396a7707e563c5b'
    
    G = '5958c9d3898b224b12672c0b98e06c60df923cb8bc999d119'+\
        '458fef538b8fa4046c8db53039db620c094c9fa077ef389b5'+\
        '322a559946a71903f990f1f7e0e025e2d7f7cf494aff1a047'+\
        '0f5b64c36b625a097f1651fe775323556fe00b3608c887892'+\
        '878480e99041be601a62166ca6894bdd41a7054ec89f756ba'+\
        '9fc95302291'
        
    STRING = 'For those that envy a MC it can be hazardous to your health\n'+\
             'So be friendly, a matter of life and death, just like a etch'+\
             '-a-sketch\n'
             
    R = 548099063082341131477253921760299949438196259240
    S = 857042759984254168557880549501802188789837994940
    
    KEY_HASH = '0954edd5e0afe5542a4adf012611a91912a3ec16'
    
    def _from_hex(self, integer):
        return HexToInt(integer).value()

    def expected_value(self):
        return HexToBytes(self.KEY_HASH).value()

    def value(self):
        p = self._from_hex(self.P)
        q = self._from_hex(self.Q)
        g = self._from_hex(self.G)
        signature = (self.R, self.S)
        
        key = DSAPrivateKeyCracker(p, q, g).crack(self.STRING, signature)
        hex_key = IntToHex(key).value()
        return SHA1().hash(hex_key)