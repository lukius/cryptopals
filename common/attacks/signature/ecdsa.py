import random

from common.math.invmod import ModularInverse


class ECDSAKeySelectionAttack(object):
    
    def __init__(self, ecdsa):
        # Only uses the ECDSA object to retrieve its public key and parameters.
        self.ecdsa = ecdsa
        self.pubkey = self.ecdsa.get_public_key()[-1]
        self.modinv = ModularInverse(self.ecdsa.q) 
        
    def _compute_u(self, message, signature):
        r, s = signature
        h = self.ecdsa.hash_function.int_hash(message)
        w = self.modinv.value(s)
        u1 = (h*w) % self.ecdsa.q
        u2 = (r*w) % self.ecdsa.q
        return u1, u2        
    
    def generate_key(self, message, signature):
        x = random.randint(1, self.ecdsa.q-1)
        u1, u2 = self._compute_u(message, signature)
        t = (u1 + u2*x) % self.ecdsa.q
        R = u1*self.ecdsa.g + u2*self.pubkey
        
        new_G = self.modinv.value(t) * R
        new_key = x * new_G
        
        return new_key, new_G