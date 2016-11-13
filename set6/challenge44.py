from common.challenge import CryptoChallenge
from common.hash.sha1 import SHA1
from common.math.invmod import ModularInverse
from common.tools.converters import HexToBytes, HexToInt, IntToHex
from common.tools.misc import FileLines


class DSAPrivateKeyCrackerFromRepeatedNonce(object):
    
    def __init__(self, p, q, g):
        self.p = p
        self.q = q
        self.g = g
        
    def _get_key_from(self, k, h, signature):
        r, s = signature
        r_inv = ModularInverse(self.q).value(r)
        return ((s*k - h) * r_inv) % self.q
    
    def _get_k_from(self, hashes, signatures):
        hash_diff = (hashes[0] - hashes[1]) % self.q
        s_diff = (signatures[0][1] - signatures[1][1]) % self.q
        s_diff_inv = ModularInverse(self.q).value(s_diff)
        return (hash_diff*s_diff_inv) % self.q
    
    def crack(self, messages, signatures):
        hashes = map(lambda message: SHA1().int_hash(message), messages)
        k = self._get_k_from(hashes, signatures)
        return self._get_key_from(k, hashes[0], signatures[0])
            
            
class Set6Challenge44(CryptoChallenge):
    
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
        
    KEY_HASH = 'ca8f6f7c66fa362d40760d135b763eb8527d3d52'
    
    FILE = 'set6/data/44.txt'
    
    def _from_hex(self, integer):
        return HexToInt(integer).value()

    def expected_value(self):
        return HexToBytes(self.KEY_HASH).value()
    
    def _find_messages_and_signatures_for_same_k(self):
        same_k_dict = dict()
        data = FileLines(self.FILE).value()
        for line_index in range(0, len(data), 4):
            msg = data[line_index].split('msg: ')[1]
            s = int(data[line_index+1].split('s: ')[1])
            r = int(data[line_index+2].split('r: ')[1])
            if r in same_k_dict:
                old_msg, old_s = same_k_dict[r]
                messages = [msg, old_msg]
                signatures = [(r, s), (r, old_s)]
                break
            same_k_dict[r] = (msg, s)
        return messages, signatures
            
    def value(self):
        p = self._from_hex(self.P)
        q = self._from_hex(self.Q)
        g = self._from_hex(self.G)
        
        messages, signatures = self._find_messages_and_signatures_for_same_k()
        
        key = DSAPrivateKeyCrackerFromRepeatedNonce(p, q, g).crack(messages, 
                                                                   signatures)
        hex_key = IntToHex(key).value()
        return SHA1().hash(hex_key)