import math

from Crypto.Util import number


class RandPrime(object):
    
    DEFAULT_BITS = 1024
    
    def value(self, n=None):
        # Compute a random n-bit prime number. 
        # TODO: implement Miller-Rabin in order to test primality.
        if n is None:
            n = self.DEFAULT_BITS
        return number.getPrime(n)

    
class PrimeSieve(object):
    
    def primes_until(self, n):
        # Find all prime numbers up to n.
        n = int(n)
        if n % 2 == 1:
            n += 1
        nums = [True] * (n/2)
        for k in xrange(3, int(math.sqrt(n))+1, 2):
            if nums[k/2]:
                for j in xrange((k*k)/2, n/2, k):
                    nums[j] = False
        return [2] + [2*k+1 for k in xrange(1, n/2) if nums[k]]           


def is_prime(n):
    return number.isPrime(n, false_positive_prob=1e-10)


def Primes():
    # (slow!) generator of prime numbers.
    yield 2
    p = 3
    while True:
        q = 3
        is_prime = True
        while q*q <= p:
            if p%q == 0:
                is_prime = False
                break
            q += 2
        if is_prime:
            yield p    
        p += 2