from common.ciphers.pubkey import PublicKeyCipher
from common.math.gcd import GCD
from common.math.invmod import ModularInverse
from common.math.modexp import ModularExp
from common.math.prime import RandPrime


class RSA(PublicKeyCipher):
    
    DEFAULT_E = 65537
    DEFAULT_BITS = 2048
    
    def __init__(self, bits=None):
        PublicKeyCipher.__init__(self)
        bits = bits if bits is not None else self.DEFAULT_BITS
        self._init_parameters(bits)
        
    def _init_primes(self, bits):
        prime_generator = RandPrime()
        bitsize = 1+bits/2 if bits%2 else bits/2
        p = prime_generator.value(n=bitsize)
        q = prime_generator.value(n=bitsize)
        return p, q
        
    def _init_parameters(self, bits):
        p, q = self._init_primes(bits)
        totient = (p-1)*(q-1)
        self.n = p*q
        self.modexp = ModularExp(self.n)
        self.e = self._choose_e_from(totient)
        self.d = ModularInverse(totient).value(self.e)
        self.public_key = (self.e, self.n)
        
    def _choose_e_from(self, totient):
        # Choose 1 < e < totient s.t. e and totient are coprime.
        e = self.DEFAULT_E
        gcd = GCD()
        while gcd.value(e, totient) != 1:
            e += 2
        return e
    
    def _encrypt(self, int_plaintext):
        return self._exp_with(int_plaintext, self.e)
    
    def _decrypt(self, int_ciphertext):
        return self._exp_with(int_ciphertext, self.d)
    
    def _exp_with(self, integer, exponent):
        return self.modexp.value(integer, exponent)
    
    
class FixedERSA(RSA):
    
    def __init__(self, e, bits=None):
        self.e = e
        RSA.__init__(self, bits)
    
    def _choose_e_from(self, totient):
        return self.e
    
    def _init_primes(self, bits):
        gcd = GCD()
        while True:
            p, q = RSA._init_primes(self, bits)
            totient = (p-1)*(q-1)
            if gcd.value(self.e, totient) == 1:
                return p, q