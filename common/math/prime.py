from Crypto.Util import number


class RandPrime(object):
    
    DEFAULT_BITS = 1024
    
    def value(self, n=None):
        # Compute a random n-bit prime number. 
        # TODO: implement Miller-Rabin in order to test primality.
        if n is None:
            n = self.DEFAULT_BITS
        return number.getPrime(n)
    
    
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