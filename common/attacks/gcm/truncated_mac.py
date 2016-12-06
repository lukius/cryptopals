from common.attacks.gcm import GCMAuthSubkeyRecoveryAttack
from common.math.linalg.bit import BitVector, BitMatrix


class TruncatedMACGCMAttack(GCMAuthSubkeyRecoveryAttack):
    
    def __init__(self, aes, gcm, ciphertext, tag):
        GCMAuthSubkeyRecoveryAttack.__init__(self, aes, gcm)
        self.ciphertext = ciphertext
        self.tag = tag
        self._init_vectors()
    
    def _init_vectors(self):
        n = self.ciphertext.block_count()
        self.D = [BitVector(128)]
        i = 2
        while i <= n + 1:
            block = self.ciphertext.get_block(n - i + 1)
            z = self._to_field_elem(block)
            v = z.to_bit_vector()
            self.D.append(v)
            i <<= 1
            
    def _assemble_new_ciphertext(self, bitflips):
        D = [v.clone() for v in self.D]
        for i, b in enumerate(bitflips):
            D_index, bit_index = divmod(128+i, 128)
            if b == 1:
                D[D_index].flip(bit_index)
        n = self.ciphertext.block_count()
        for i in xrange(1, len(D)):
            z = self.GF2k.element(D[i])
            block = self._from_field_elem(z)
            self.ciphertext.replace_block(n - 2**i + 1, block)
            
    def _build_AD(self, D, Msq=None):
        AD = BitMatrix(128, 128)
        Msq = Msq_i = Msq or self.GF2k.to_bit_matrix(lambda z: z**2)
        for v in D[1:]:
            w = self.GF2k.element(v)
            Mv = self.GF2k.to_bit_matrix(lambda z: w*z)
            AD += Mv * Msq_i
            Msq_i *= Msq
        return AD
    
    def _AD_i(self, D_i, Msq_i):
        w = self.GF2k.element(D_i)
        Mv = self.GF2k.to_bit_matrix(lambda z: w*z)
        return Mv * Msq_i
    
    def _update_T_from_AD(self, T, AD, T_col, AD_rows):
        m = AD.columns()
        for i in xrange(AD_rows):
            for j in xrange(m):
                AD_cell = i*m + j
                T[AD_cell, T_col] = AD[i,j]
        return T
    
    def _build_dependency_matrix(self, X, r):
        # Dependency matrix where each column represents a bit in the blocks of
        # the ciphertext that we can flip and each row represents a cell in the
        # (AD*X) matrix. r is the number of rows of AD*X we can cover.
        T = BitMatrix(r*128, (len(self.D)-1)*128)
        D = [v.clone() for v in self.D]
        Msq = Msq_i = self.GF2k.to_bit_matrix(lambda z: z**2)
        AD = self._build_AD(D)
        for i in xrange(1, len(D)):
            AD_i0 = AD_i = self._AD_i(D[i], Msq_i)
            for j in xrange(128):
                AD += AD_i
                D[i].flip(j)
                AD_i = self._AD_i(D[i], Msq_i)
                AD += AD_i
                AD_X = AD*X if X else AD
                T = self._update_T_from_AD(T, AD_X, (i-1)*128 + j, r)
                D[i].flip(j)
            AD += AD_i
            AD += AD_i0
            Msq_i *= Msq
        return T
            
    def _find_valid_D(self, T, S):
        while True:
            v = S.rand_vector()
            self._assemble_new_ciphertext(v)
            result = self.aes.decrypt((self.ciphertext, self.tag),
                                      mode=self.gcm)
            if result[0] is True:
                return self._to_vectors(v)
            
    def _to_vectors(self, v):
        D = list()
        Dj = BitVector(128)
        for i, b in enumerate(v):
            j, k = divmod(i+128, 128)
            if k == 0:
                D.append(Dj)
                Dj = BitVector(128)
            Dj[k] = self.D[j][k] if b == 0 else (1-self.D[j][k])
        D.append(Dj)
        return D
    
    def _extend_K(self, K, D, X):
        AD = self._build_AD(D)
        AD_X = AD*X if X else AD
        # Get nonzero rows of AD_X.
        rows = list()
        for i in xrange(AD_X.rows()):
            row = AD_X[i]
            if row != 0:
                rows.append(row)
        if K is None:
            K = BitMatrix._new(rows)
        else:
            for row in rows:
                K.add_row(row)
        return K
    
    def recover_key(self):
        n = len(self.D) - 1
        r = n - 1
        K = X = None
        while True:
            T = self._build_dependency_matrix(X, r)
            S = T.kernel()
            D = self._find_valid_D(T,S)
            K = self._extend_K(K, D, X)
            X = K.kernel()
            r = (128*n) / X.columns()
            if r * X.columns() == 128*n:
                r -= 1
            if X.dim() == 1:
                v = X.basis()[0]
                z = self.GF2k.element(v)
                return self._from_field_elem(z)