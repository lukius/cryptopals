from common.challenge import CryptoChallenge
from common.math.linalg.bit import BitMatrix
from common.math.poly import GF2k


class Set8Challenge64(CryptoChallenge):
    
    def _test_GF2k_linear_operations(self):
        F = GF2k(128, modulus='x^128 + x^7 + x^2 + x + 1')
        
        w = F.rand_element()
        r = F.rand_element()

        Mw = F.to_bit_matrix(lambda z: w*z)
        wr = (w*r).to_bit_vector()
        Mwr = Mw * r.to_bit_vector()
        
        self._assert_equals(wr, Mwr)
        
        Msq = F.to_bit_matrix(lambda z: z**2)
        r_sq = (r**2).to_bit_vector()
        Msq_r = Msq * r.to_bit_vector()
        
        self._assert_equals(r_sq, Msq_r)
        
    def _test_kernel_computation(self):
        while True:
            M = BitMatrix.random(5, 8)
            B = M.kernel()
            if B.dim() > 0:
                break
        
        v1 = B.rand_vector()
        v2 = B.rand_vector()
        
        self._assert_equals(0, M*v1)
        self._assert_equals(0, M*v2)
    
    def _validate(self):
        # 1. Validate squaring and multiplication in GF(2^k) as linear
        # operations.  
        self._test_GF2k_linear_operations()
        
        # 2. Validate computation of kernel of a linear transformation.
        self._test_kernel_computation()