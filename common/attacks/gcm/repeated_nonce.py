from common.attacks.gcm import GCMAuthSubkeyRecoveryAttack
from common.math.poly.factor import GF2kPolyFactorization
from common.tools.padders import RightPadder
from common.tools.misc import RandomByteGenerator
from common.tools.blockstring import BlockString


class RepeatedNonceGCMAttack(GCMAuthSubkeyRecoveryAttack):
    
    def _pad(self, string):
        len_str = len(string)
        offset = -len_str % self.BLOCK_SIZE
        return RightPadder(string).value(len_str + offset, char='\x00')
    
    def _build_blockstrings(self, a1, c1, a2, c2):
        a1 = self._pad(a1)
        a2 = self._pad(a2)
        
        pad_c1 = '\x00'*(-len(c1) % self.BLOCK_SIZE)
        pad_c2 = '\x00'*(-len(c2) % self.BLOCK_SIZE)
        
        return a1+c1+pad_c1, a2+c2+pad_c2

    def _build_t(self, t1, t2):
        return self._to_field_elem(t1) + self._to_field_elem(t2)
    
    def _build_polynomial_2(self, a1, c1, a2, c2):
        len_a1, len_c1 = 8*len(a1), 8*len(c1)    
        len_a2, len_c2 = 8*len(a2), 8*len(c2)
        
        B1, B2 = self._build_blockstrings(a1, c1, a2, c2)
        
        N = B1.block_count()
        if len(B2) > len(B1):
            B2, B1 = B1, B2
            N = B2.block_count()
        n_2 = B2.block_count() if B2 else 0
        
        j = N+1
        i = 0
        q = 0
        x = self.GF2k_X.x()

        for i in xrange(N):
            block1 = B1.get_block(i)
            elem = self._to_field_elem(block1)
            if i >= N - n_2:
                block2 = B2.get_block(i - N + n_2)
                elem2 = self._to_field_elem(block2)
                elem += elem2
            q += elem * x**j
            j -= 1
            
        l1 = self.GF2k.element((len_a1 << 64) + len_c1)   
        l2 = self.GF2k.element((len_a2 << 64) + len_c2)   
        q += (l1 + l2) * x
        
        return q 
    
    def _build_polynomial_1(self, data1, data2):
        c1, a1, t1 = data1
        c2, a2, t2 = data2
        t = self._build_t(t1, t2)
        q = self._build_polynomial_2(a1, c1, a2, c2)
        return q + t
    
    def _is_actual_key(self, k, data1, data2):\
        # Idea:
        #   * Build MAC polynomial q1 out of a1 and c1.
        #   * Compute s = q1(k) + t1.
        #   * Use a random message to generate a new polynomial q2.
        #   * Set t3 = q2(k) + s as its tag and use the oracle to validate it.
        #   * If the tag is valid, we found the key.
        c1, a1, t1 = data1
        c2, a2, _ = data2
        
        t1 = self._to_field_elem(t1)
        q1 = self._build_polynomial_2(a1, c1, str(), str())
        s = q1(k) + t1

        c3 = BlockString(RandomByteGenerator().value(len(c2)))
        q2 = self._build_polynomial_2(a2, c3, str(), str())
        t3 = self._from_field_elem(q2(k) + s)

        result = self.aes.decrypt((c3, a2, t3), mode=self.gcm)
        
        return result[0] is True
    
    def _find_candidates(self, factors):
        candidates = list()
        x = self.GF2k_X.x()
        for q, _ in factors:
            if q.degree() == 1:
                k = (q+x).coefficient()
                candidates.append(k)
        return candidates
    
    def recover_key(self, data1, data2):
        # Idea:
        #   * Build polynomial q(h) from the auth data and ciphertexts.
        #   * Define p(h) = q(h) + [t1 + t2], where t1 and t2 are the tags.
        #   * Factor p over GF(2^128) and check its degree 1 factors.
        #   * For every one of these, say f, consider the candidate key
        #        k = f(h) + h
        #      (these f are already monic; the factor algorithm was coded
        #       like this on purpose)
        #   * Check if k is valid (see method above) and if so return it
        #     after converting it to a byte string. 
        p = self._build_polynomial_1(data1, data2)
        factors = GF2kPolyFactorization().factor(p)
        candidates = self._find_candidates(factors)
        for candidate in candidates:
            if self._is_actual_key(candidate, data1, data2):
                return self._from_field_elem(candidate)