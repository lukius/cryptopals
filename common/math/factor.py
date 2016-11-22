import random

from common.math.gcd import GCD
from common.math.prime import RandPrime, is_prime, PrimeSieve
from common.tools.misc import ByteSize


class PollardRho(object):
    
    def _g(self, x, n):
        return (x*x + 1) % n
    
    def value(self, n):
        x, y, d = 2, 2, 1
        gcd = GCD()
        while d == 1:
            x = self._g(x, n)
            y = self._g(self._g(y, n), n)
            d = gcd.value(int(abs(x-y)), n)
        return d
    
    
class NaiveFactorization(object):
    
    # Naive integer factorization, only useful for small numbers.
    
    def _factor_p(self, n, p):
        i = 0
        while n % p == 0:
            i += 1
            n /= p
        return i, n
    
    def value(self, n):
        i, n1 = self._factor_p(n, 2)
        factors = [(2,i)] if i > 0 else list()
        p = 3
        while p*p <= n:
            i, n1 = self._factor_p(n1, p)
            if i > 0:
                factors.append((p,i))
            p += 2
        if n1 > 1:
            factors.append((n1,1))
        return factors

        
class RhoBasedSmoothNumberGenerator(object):
    
    # Smooth number generator --slow if bitsize is large.
    # Given a bitsize N, SmoothNumber(N) is an object that, given p, can
    # generate p-smooth numbers n such that n+1 is prime and n+1 bitsize
    # is N. 
    
    # Fail if this number of iterations is exceeded.
    MAX_ITERATIONS = 1000
    
    def __init__(self, bitsize):
        self.bitsize = bitsize
        self.rho = PollardRho()
        self.fact = NaiveFactorization()
        
    def value(self, p):
        # Idea:
        #   * Get an N-bit random prime q and call n = q-1.
        #   * Using Pollard's Rho algorithm, find small factors of n and
        #     remove divide them out of n.
        #   * If one of the factors found is > p, start over.
        #   * Once done, we have n = 1. Since the factors found are "small",
        #     we can factor them with the naive algorithm above. 
        #   * Thus, factor everyone and put together the prime factors with
        #     their exponents. 
        for _ in xrange(self.MAX_ITERATIONS):
            q = int(RandPrime().value(self.bitsize))
            n = q-1
            rho_factors = list()
            while n > 1:
                m = self.rho.value(n)
                if m > p:
                    break
                rho_factors.append(m)
                n /= m
            if n == 1:
                factors = dict()
                for k in rho_factors:
                    k_factors = self.fact.value(k)
                    for (m,j) in k_factors:
                        i = factors.setdefault(m, 0)
                        factors[m] = i+j
                return q-1, factors.items()

            
class SieveBasedSmoothNumberGenerator(object):
    
    # Smooth number generator that uses a prime sieve.
    # Given a smoothness factor N, SmoothNumber(N) is an object that, given a
    # bitsize, generates N-smooth numbers n such that n+1 is prime and its bit
    # length is roughly bitsize.
    
    def __init__(self, p):
        # Precompute prime sieve.
        self.primes = PrimeSieve().primes_until(p)
        
    def _bitsize(self, n):
        return ByteSize(n).value()*8
        
    def value(self, bitsize, banned_primes=None):
        # Choose random primes in the sieve until their product bit length is
        # OK. Start over if the product plus 1 is not a prime number.
        # Optional argument banned_primes is to avoid these primes as factors.
        banned_primes = set(banned_primes or list())
        while True:
            n = 2
            chosen = set([2])
            while self._bitsize(n) < bitsize:
                p = random.choice(self.primes)
                if p in chosen or p in banned_primes:
                    continue
                n *= p
                chosen.add(p)
                if len(chosen) >= len(self.primes):
                    return
            if is_prime(n+1):
                return n, sorted(list(chosen))