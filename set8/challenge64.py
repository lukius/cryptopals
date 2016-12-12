from common.attacks.gcm.truncated_mac import TruncatedMACGCMAttack
from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import GCM
from common.math.finite_field import GF2k
from common.math.linalg.bit import BitMatrix
from common.tools.misc import RandomByteGenerator


class Challenge64GCM(GCM):
    
    # Custom GCM implementation for this challenge. Precomputes the portion of
    # the GHASH that is not affected by the differences introduced into the
    # ciphertex by the truncated MAC attack. This speeds up the vector
    # discovery phase after finding the kernel of the dependency matrix.
    
    def __init__(self, iv, tag_length=None):
        GCM.__init__(self, iv, tag_length=tag_length)
        self.hash = None
        
    def _is_power_of_2(self, i):
        return i & (i-1) == 0
        
    def _precompute_(self, ciphertext):
        self.hash = 0
        n = ciphertext.block_count() + 1
        h = self._to_field_elem(self.H)
        for block in ciphertext:
            if not self._is_power_of_2(n):
                z = self._to_field_elem(block)
                self.hash += z * h**n
            n -= 1
        
    def _ghash(self, cipher, auth_data, ciphertext):
        if self.hash is None:
            self._precompute_(ciphertext)
        n = ciphertext.block_count()
        j = 2
        h = self._to_field_elem(self.H)
        ghash = self.hash
        while j <= n:
            block = ciphertext.get_block(n - j + 1)
            z = self._to_field_elem(block)
            ghash += z * h**j
            j <<= 1
        len_C = len(ciphertext)*8
        L = self.field.element(len_C)         
        return ghash + L*h  
        
        

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

        r_sq = (r**4).to_bit_vector()
        Msq_r = (Msq**2) * r.to_bit_vector()
        
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
        
    def _test_key_recovery(self):
        byte_generator = RandomByteGenerator()
        gcm_iv = byte_generator.value(12)
        aes_key = byte_generator.value(16)
        # NOTE: the 32-bit tag attack works but takes a considerable amount of
        # time to complete, even with concurrency optimizations. This 16-bit
        # version is faster and still the code is exactly the same, no changes
        # needed (apart from obviously using 2^17 blocks in the following line
        # and changing below the tag length to 32).
        message = byte_generator.value(16 * 2**9)

        aes = AES(aes_key)
        gcm = Challenge64GCM(gcm_iv, tag_length=16)
        c, t = aes.encrypt(message, mode=gcm)
        
        attack = TruncatedMACGCMAttack(aes, gcm, c, t)
        key = attack.recover_key()
        
        self._assert_equals(gcm.H, key)        
    
    def _validate(self):
        # 1. Validate squaring and multiplication in GF(2^k) as linear
        # operations.  
        self._test_GF2k_linear_operations()
        
        # 2. Validate computation of kernel of a linear transformation.
        self._test_kernel_computation()
        
        # 3. Perform key recovery attack.
        self._test_key_recovery()