from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import GCM
from common.math.gcd import ExtendedGCD
from common.math.poly import GF2k, GF2PolyRing, GF2kPolyRing
from common.math.poly_factor import SquarefreeFactorization,\
                                    DistinctDegreeFactorization,\
                                    EqualDegreeFactorization,\
                                    GF2kPolyFactorization
from common.tools.misc import RandomByteGenerator


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
        while True:
            b = GF2_4.rand_element()
            if b != 0:
                break
        
        q = a / b
        r = a % b
        q1, r1 = divmod(a, b) 
        self._assert_equals(q1, q)
        self._assert_equals(r1, r)
        self._assert_equals(a, q*b + r)
        
        u, v, gcd = ExtendedGCD().value(a, b)
        self._assert_equals(gcd, u*a + v*b)
    
    def _test_GCM(self):
        plaintext = 'The tag length t must be fixed for any fixed value of the key'
        auth_data = 'A tag length of 128 bits should be used whenever possible'
        iv = RandomByteGenerator().value(16)
        
        key = RandomByteGenerator().value(16)
        aes = AES(key)
        
        ciphertext, tag = aes.encrypt((plaintext, auth_data), mode=GCM(iv))
        result = aes.decrypt((ciphertext, auth_data, tag), mode=GCM(iv))
        self._assert_equals(True, result[0])
        self._assert_equals(plaintext, result[1].bytes())
    
        result = aes.decrypt((ciphertext, auth_data, tag+'x'), mode=GCM(iv))
        self._assert_equals(False, result[0])
        
        result = aes.decrypt((ciphertext, auth_data+'x', tag), mode=GCM(iv))
        self._assert_equals(False, result[0])
        
        iv = RandomByteGenerator().value(204)
        ciphertext, tag = aes.encrypt((plaintext, auth_data), mode=GCM(iv))
        result = aes.decrypt((ciphertext, auth_data, tag), mode=GCM(iv))
        self._assert_equals(True, result[0])
        self._assert_equals(plaintext, result[1].bytes())
        
    def _test_square_free_factorization(self):
        GF2_X = GF2PolyRing()
        x = GF2_X.x()
        
        a = x**2 + x + 1
        b = x + 1
        p = a**4 * b
         
        factors = SquarefreeFactorization().factor(p)
        self._assert_equals(2, len(factors))
        for (q, k) in factors:
            self._assert_in(q, [a,b])
            if q == a:
                self._assert_equals(4, k)
            else:
                self._assert_equals(1, k)
                
        a = x**50 + x**43 + x + 1
        b = x
        c = x**2 + 1
        p = a**6 * b**3 * c**2
        factors = SquarefreeFactorization().factor(p)

        r = 1
        for q, k in factors:
            r *= q**k
        self._assert_equals(p, r)
        
    def _test_distinct_degree_factorization(self):
        GF2_X = GF2PolyRing()
        x = GF2_X.x()
        
        deg_1 = x*(x+1)
        deg_3 = (x**3 + x**2 + 1)*(x**3 + x + 1)
        deg_4 = (x**4 + x + 1)*(x**4 + x**3 + 1)*(x**4 + x**3 + x**2 + x + 1)
        p = deg_1 * deg_3 * deg_4
        deg = {1 : deg_1, 3 : deg_3, 4 : deg_4}
        
        factors = DistinctDegreeFactorization().factor(p)
        for q, k in factors:
            self._assert_in(k, deg.keys())
            self._assert_equals(q, deg[k])

    def _test_equal_degree_factorization(self):
        GF2_X = GF2PolyRing()
        x = GF2_X.x()
        
        a = x**4 + x + 1
        b = x**4 + x**3 + 1
        c = x**4 + x**3 + x**2 + x + 1
        p = a*b*c
        
        factors = EqualDegreeFactorization().factor(p, 4)
        self._assert_equals(3, len(factors))
        for q in factors:
            self._assert_in(q, [a,b,c])
            
    def _test_GF2k_factorization(self):
        G = GF2k(128, modulus='x^128 + x^7 + x^2 + x + 1')
        GF2k_X = GF2kPolyRing(G)
        x = GF2k_X.x()
        z = G.x()
        
        a = (z**54+1)*x**2 + z*x + z**32 + 1
        b = (z**10+ z + 1)*x**7 + z*x + z**7 + z**5
        p = z * a**2 * b**3
        
        factors = GF2kPolyFactorization().factor(p)
        
        p1 = 1
        for q, k in factors:
            p1 *= q**k
        
        self._assert_equals(p1, p.to_monic())
    
    def _test_key_recovery(self): 
        pass
    
    def _validate(self):
        # 1. Test GF(2^k) implementation.
        self._test_GF2k()
    
        # 2. Test GCM implementation.
        self._test_GCM()
    
        # 3. Test square-free factorization over GF(2)[X].
        self._test_square_free_factorization()

        # 4. Test distinct degree factorization over GF(2)[X].
        self._test_distinct_degree_factorization()
        
        # 5. Test equal degree factorization over GF(2)[X].
        self._test_equal_degree_factorization()
        
        # 6. Test factorization over GF(2^128)[X].
        self._test_GF2k_factorization()
    
        # 7. Perform key recovery attack on GCM.
        self._test_key_recovery()