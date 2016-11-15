from common.math.invmod import ModularInverse
from common.math.modexp import ModularExp
from common.math.prime import Primes


class NthRoot(object):

    def __init__(self, n):
        if n <= 0:
            raise RuntimeError('n should be positive')
        self.n = n

    def value(self, x):
        # Compute y s.t. y == [nth_root(x, self.n)]
        # [.] denotes the floor function.

        if x == 0:
            return 0
        
        # Find y in a binary search fashion.
        upper_limit = lower_limit = y = 1
        while upper_limit ** self.n < x:
            lower_limit = upper_limit
            upper_limit <<= 1
        while lower_limit < upper_limit:
            mid = (lower_limit+upper_limit)/2
            mid_value = mid**self.n
            if lower_limit < mid and mid_value < x:
                lower_limit = mid
            elif upper_limit > mid and mid_value > x:
                upper_limit = mid
            else:
                y = mid
                break
            
        return y
    

class ModularSquareRoot(object):
    
    def __init__(self, p):
        self.p = p
        self.modexp = ModularExp(self.p)
        
    def value(self, x):
        # Computes y s.t. y^2 = x mod p using Tonelli-Shanks.
        # IMPORTANT: p must be prime!
        
        # We first check whether x is a quadratic residue in Z_p.
        legendre_symbol = self.modexp.value(x, (self.p-1)/2)
        if legendre_symbol != 1:
            return None
        
        p_1 = self.p - 1
        s = 0
        # Find s such that p - 1 = Q * 2^s
        while p_1 % 2 == 0:
            p_1 /= 2
            s += 1
        Q = p_1
            
        # Find z such that z is a quadratic non-residue in Z_p.
        # It can be seen that the smallest such z is also a prime.
        for q in Primes():
            legendre_symbol = self.modexp.value(q, (self.p-1)/2)
            if legendre_symbol == self.p - 1:
                z = q
                break

        v = self.modexp.value(z, Q)
        r = self.modexp.value(x, (Q+1)/2)
        x1 = ModularInverse(self.p).value(x)
        
        while True:
            t = (r*r*x1) % self.p
            if t == 1:
                break
            i = 1
            t_sq = (t*t) % self.p
            while t_sq != 1:
                t_sq = (t_sq * t_sq) % self.p
                i += 1
            r = (r * self.modexp.value(v, 2**(s-i-1))) % self.p
            
        return r