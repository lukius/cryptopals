import random

from common.math.modexp import ModularExp
from common.math.prime import Primes
from common.math.crt import ChineseRemainderTheorem
from common.math.invmod import ModularInverse


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
    
    
class PollardKangarooAttack(object):
    
    DEFAULT_K = 20
    
    def __init__(self, p, g, k=None):
        self.p = p
        self.g = g
        self.k = k or self.DEFAULT_K
        self.modexp = ModularExp(self.p)
        
    def f(self, x):
        return self.modexp.value(2, x%self.k)
        
    def _compute_N(self):
        # N (i.e., the number of the tame kangaroo jumps) is computed as 
        # 4m, with
        #   m = ([(p-1)/k] * sum_j 2^j mod p) / (p-1), 0 <= j < k
        # i.e., the mean value of the outputs of f. It is scaled with a 
        # factor of 4 following Pollard's analysis: if N = \Theta * m with
        # \Theta = 4, the probability of missing the wild kangaroo is about
        # 0.02.
        s = (self.modexp.value(2,self.k) - 1) % self.p
        w = (self.p-1)//self.k
        s *= w
        s //= self.p-1
        return 4*s 
    
    def _advance_tame_kangaroo(self, N, a, b):
        x_N = 0
        y_N = self.modexp.value(self.g, b)
        for _ in xrange(N):
            f_y = self.f(y_N)
            x_N += f_y
            y_N = (y_N * self.modexp.value(self.g, f_y)) % self.p
        return x_N, y_N
    
    def _advance_wild_kangaroo(self, x_N, y_N, y, a, b):
        x_M = 0
        y_M = y
        while x_M < b - a + x_N:
            f_y = self.f(y_M)
            x_M += f_y
            y_M = (y_M * self.modexp.value(self.g, f_y)) % self.p
            
            if y_M == y_N:
                return b + x_N - x_M
        
    def get_index(self, y, a, b): 
        # Computes i such that g**i = y mod p (a <= i <= b)
        N = self._compute_N()
        x_N, y_N = self._advance_tame_kangaroo(N,a,b)
        return self._advance_wild_kangaroo(x_N, y_N, y, a, b)
        
    
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
        
        kangaroo_attack = PollardKangarooAttack(self.p, g_prime)
        y_prime_idx = kangaroo_attack.get_index(y_prime, a=0, b=(self.q-1)/r)
        if y_prime_idx is not None:
            return n + y_prime_idx * r