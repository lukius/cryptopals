import random

from common.math.modexp import ModularExp
from common.math.prime import Primes
from common.math.crt import ChineseRemainderTheorem


class PohligHellmannAttack(object):
    
    def __init__(self, p, q):
        self.p = p
        self.q = q
        self.modexp = ModularExp(self.p)
        
    def _get_remainder_for(self, r):
        # Get an h such that h^r = 1 mod p (due to Euler's Theorem).
        while True:
            h = random.randint(1, self.p-1)
            h = self.modexp.value(h, (self.p-1)/r)
            if h != 1:
                break
            
        # Guess the remainder by brute-forcing its possible values.
        for k in xrange(r):
            trial_key = self.modexp.value(h, k)
            if self._key_is_valid(trial_key, h):
                return k
        
    def _get_remainders(self):
        moduli = list()
        remainders = list()
        j = (self.p - 1) / self.q
        m = 1
        # Find factors of j = (p-1)/q
        for p in Primes():
            if j % p == 0 and j % (p*p) != 0:
                # For each factor p, compute the remainder
                #   b = x mod p (where x is the target's key)
                b = self._get_remainder_for(p)
                moduli.append(p)
                remainders.append(b)
                m *= p
                if m >= self.q:
                    break
        return remainders, moduli
        
    def _get_key(self, remainders, moduli):
        # Last step: use CRT to solve 
        #  x = remainders_i mod moduli_i
        crt = ChineseRemainderTheorem()
        x = crt.solve(remainders, moduli)
        return x % self.q
        
    def recover_key(self):
        remainders, moduli = self._get_remainders()
        return self._get_key(remainders, moduli)
    
    def _key_is_valid(self, trial_key, h):
        raise NotImplementedError