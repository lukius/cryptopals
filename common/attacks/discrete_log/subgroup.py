import random

from common.math.modexp import ModularExp
from common.math.prime import Primes
from common.math.crt import ChineseRemainderTheorem
from common.math.invmod import ModularInverse

from kangaroo import IntegerKangarooAttack


class SubgroupConfinementAttack(object):
    
    # If a factor exceeds this value, we stop the attack. We won't be able
    # to brute-force the key anymore.
    MAX_P = 2**24
    
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
            if p > self.MAX_P:
                break
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
        x, N = ChineseRemainderTheorem().solve(remainders, moduli)
        if N > self.q:
            return x % self.q, self.q
        else:
            return x, N
        
    def recover_key(self):
        remainders, moduli = self._get_remainders()
        return self._get_key(remainders, moduli)
    
    def _key_is_valid(self, trial_key, h):
        raise NotImplementedError

    def _target_public_key(self):
        raise NotImplementedError
    
    
class EnhancedSubgroupConfinementAttack(SubgroupConfinementAttack):
    
    def __init__(self, p, g, q):
        SubgroupConfinementAttack.__init__(self, p, q)
        self.g = g
        
    def recover_key(self):
        # Recovers the target's secret key x.
        
        # 1. Use the standard subgroup confinement attack to get
        #    x  = n mod r (r < q)
        n, r = SubgroupConfinementAttack.recover_key(self)

        # Check if we are already there (to make this attack sort of backward
        # compatible with the standard subgroup confinement attack).
        if r == self.q:
            return n

        # 2. Run the kangaroo attack.
        y = self._target_public_key()
        g_n = self.modexp.value(self.g, n)
        y_prime = (y * ModularInverse(self.p).value(g_n)) % self.p
        g_prime = self.modexp.value(self.g, r)
        
        kangaroo_attack = IntegerKangarooAttack(g_prime, self.p)
        y_prime_idx = kangaroo_attack.get_index(y_prime, a=0, b=(self.q-1)/r)
        if y_prime_idx is not None:
            return n + y_prime_idx * r