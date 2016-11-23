import random

from fractions import Fraction

from common.math.invmod import ModularInverse
from common.math.linalg import Vector, LatticeBasisReduction
from common.tools.misc import RandomByteGenerator


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
    
    
class BiasedNonceECDSAKeyRecoveryAttack(object):
    
    N_MESSAGES = 17
    
    def __init__(self, ecdsa, mask_n):
        self.ecdsa = ecdsa
        self.mask_n = mask_n
        self.modinv = ModularInverse(self.ecdsa.q)
        
    def _rand_message(self):
        return RandomByteGenerator().value(30)
    
    def _get_sentinels(self):
        return Fraction(self.ecdsa.q, 2**self.mask_n),\
               Fraction(1, 2**self.mask_n)
    
    def _get_u_and_t(self, message):
        r, s = self.ecdsa.sign(message)
        q = self.ecdsa.q
        h = self.ecdsa.hash_function.int_hash(message)
        
        d1 = self.modinv.value(s * 2**self.mask_n)
        d2 = self.modinv.value((q-s) * 2**self.mask_n)
        
        t = (r*d1) % q
        u = (h*d2) % q
        
        return u, t
    
    def recover_key(self):
        while True:
            u_vector = Vector(self.N_MESSAGES+2)
            t_vector = Vector(self.N_MESSAGES+2)
            s_u, s_t = self._get_sentinels()
            u_vector[-1] = s_u
            t_vector[-2] = s_t
            basis = [u_vector, t_vector]
            for i in xrange(self.N_MESSAGES):
                message = self._rand_message()
                u, t = self._get_u_and_t(message)
                u_vector[i] = u
                t_vector[i] = t
                v = Vector(self.N_MESSAGES+2)
                v[i] = self.ecdsa.q
                basis.append(v)
            print 'reducing'
            reduced_basis = LatticeBasisReduction().reduce(basis)
            print 'done'
            for v in reduced_basis:
                if v[-1] == s_u:
                    print 'found!!', v
                    return v[-2] * (-2**self.mask_n)