from common.math.finite_field import GF2k
from common.math.poly.ring import GF2kPolyRing
from common.tools.converters import BytesToInt, IntToBytes


class GCMAuthSubkeyRecoveryAttack(object):
    
    BLOCK_SIZE = 16
    
    def __init__(self, aes, gcm):
        # AES-GCM only used as an oracle to identify the valid key among the
        # candidates.
        self.aes = aes
        self.gcm = gcm
        self.GF2k = GF2k(128, modulus='x^128 + x^7 + x^2 + x + 1')
        self.GF2k_X = GF2kPolyRing(self.GF2k)
        
    def _to_field_elem(self, block):
        int_block = BytesToInt(block).value()
        return self.GF2k.element(int_block)
    
    def _from_field_elem(self, x):
        return IntToBytes(x.n).value(self.BLOCK_SIZE)  
    
    def recover_key(self, *args, **kwargs):
        raise NotImplementedError          