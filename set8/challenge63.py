from common.challenge import CryptoChallenge
from common.math.poly import GF2k
from common.math.gcd import ExtendedGCD


class Set8Challenge63(CryptoChallenge):
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        
    def _test_GF2k(self):
        GF2_4 = GF2k(4, 'X^4 + X + 1')
        
        a = GF2_4.element('X^3 + X + X^2 + 1')
        b = GF2_4.element(3)
        self._assert_equals('X^3 + X^2 + X + 1', str(a))
        self._assert_equals('X + 1', str(b))
        
        c = a + b
        self._assert_equals('X^3 + X^2', str(c))

        c = a - b
        self._assert_equals('X^3 + X^2', str(c))
        
        c = a * b
        self._assert_equals('X', str(c))
        
        d = c.invert()
        self._assert_equals(1, c*d)
        self._assert_equals(1, d*c)
        
        d1 = c**3
        d2 = c*c*c
        self._assert_equals(d1, d2)
        
        a = GF2_4.rand_element()
        b = GF2_4.rand_element()
        
        q = a / b
        r = a % b
        q1, r1 = divmod(a, b) 
        self._assert_equals(q1, q)
        self._assert_equals(r1, r)
        self._assert_equals(a, q*b + r)
        
        u, v, gcd = ExtendedGCD().value(a, b)
        self._assert_equals(gcd, u*a + v*b)
    
    def _test_GCM(self):
        pass
    
    def _test_factorization(self):
        pass
    
    def _test_key_recovery(self): 
        pass
    
    def _validate(self):
        # 1. Test GF(2^k) implementation.
        self._test_GF2k()
    
        # 2. Test GCM implementation.
        self._test_GCM()
    
        # 3. Test polynomial factorization.
        self._test_factorization()
    
        # 4. Perform key recovery attack on GCM.
        self._test_key_recovery()