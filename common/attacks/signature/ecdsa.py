import random

from collections import defaultdict
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
    
    N_MESSAGES = 20
    
    def __init__(self, ecdsa, mask_n):
        self.ecdsa = ecdsa
        self.mask_n = mask_n
        self.modinv = ModularInverse(self.ecdsa.q)
        self.s_u, self.s_t = self._get_sentinels()
        
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
    
    def _assemble_lattice_basis(self):
        u_vector = Vector(self.N_MESSAGES+2)
        t_vector = Vector(self.N_MESSAGES+2)
        u_vector[-1] = self.s_u
        t_vector[-2] = self.s_t
        basis = [u_vector, t_vector]
        for i in xrange(self.N_MESSAGES):
            message = self._rand_message()
            u, t = self._get_u_and_t(message)
            u_vector[i] = u
            t_vector[i] = t
            v = Vector(self.N_MESSAGES+2)
            v[i] = self.ecdsa.q
            basis.append(v)
        return basis
    
    def recover_key(self):
        # Idea:
        #   * Sign N_MESSAGES random messages and compute u and t values.
        #   * Assemble the lattice basis with vectors of dimension N_MESSAGES+2.
        #   * Compute the reduced basis.
        #   * Check the reduced vectors and take note of the candidate keys.
        #   * If any candidate key already appeared more than once, return it.
        #   * Otherwise, start over signing new messages.    
        candidates = defaultdict(lambda: 0)
        LLL = LatticeBasisReduction()
        while True:
            basis = self._assemble_lattice_basis()
            reduced_basis = LLL.reduce(basis)
            for v in reduced_basis:
                if v[-1] == self.s_u:
                    candidate_key = (v[-2] * (-2**self.mask_n)) % self.ecdsa.q
                    candidates[candidate_key] += 1
                    if candidates[candidate_key] > 1:
                        return candidate_key