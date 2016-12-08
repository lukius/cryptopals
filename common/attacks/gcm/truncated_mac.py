from common.attacks.gcm import GCMAuthSubkeyRecoveryAttack
from common.math.linalg.bit import BitVector, BitMatrix


class TruncatedMACGCMAttack(GCMAuthSubkeyRecoveryAttack):
    
    def __init__(self, aes, gcm, ciphertext, tag):
        GCMAuthSubkeyRecoveryAttack.__init__(self, aes, gcm)
        self.ciphertext = ciphertext
        self.tag = tag
        self.tag_len = len(self.tag)*8
        self._init_vectors()
        self._precompute_AD_i()
    
    def _init_vectors(self):
        n = self.ciphertext.block_count()
        self.D = [BitVector(128)]
        i = 1
        while 2**i <= n:
            block = self.ciphertext.get_block(n - 2**i + 1)
            z = self._to_field_elem(block)
            v = z.to_bit_vector()
            self.D.append(v)
            i += 1
            
    def _precompute_AD_i(self):
        self.AD = [None]
        Msq = Msq_i = self.GF2k.to_bit_matrix(lambda z: z**2)
        D_i = BitVector(128)
        for i in xrange(1, len(self.D)):
            self.AD.append(list())
            for j in xrange(128):
                D_i[j] = 1
                AD_i = self._AD_i(D_i, Msq_i)
                D_i[j] = 0
                self.AD[i].append(AD_i)
            Msq_i *= Msq

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
            k = i*m
            for j in xrange(m):
                AD_cell = k + j
                T[AD_cell, T_col] = AD[i, j]
        return T
    
    def _build_dependency_matrix(self, X, r):
        # Dependency matrix where each column represents a bit in the blocks of
        # the ciphertext that we can flip and each row represents a cell in the
        # (AD*X) matrix. r is the number of rows of AD*X we can cover.
        T = BitMatrix(r*X.columns(), (len(self.D)-1)*128)
        for i in xrange(1, len(self.D)):
            for j in xrange(128):
                AD_i = self.AD[i][j]
                AD_X = AD_i*X
                self._update_T_from_AD(T, AD_X, (i-1)*128 + j, r)
        return T
    
    def _assemble_new_ciphertext(self, bitflips):
        C = self._new_ciphertext_blocks_from(bitflips)
        n = self.ciphertext.block_count()
        for i in xrange(1, len(C)):
            z = self.GF2k.element(C[i])
            block = self._from_field_elem(z)
            self.ciphertext.replace_block(n - 2**i + 1, block)
            
    def _find_valid_D(self, T):
        S = T.kernel()
        while True:
            v = S.rand_vector()
            self._assemble_new_ciphertext(v)
            result = self.aes.decrypt((self.ciphertext, self.tag),
                                      mode=self.gcm)
            if result[0] is True:
                return self._to_vectors(v)
            
    def _new_ciphertext_blocks_from(self, bitflips):
        D = [v.clone() for v in self.D]
        return self._flip_bits_on_vectors(bitflips, D)

    def _to_vectors(self, bitflips):
        vectors = [BitVector(128) for _ in self.D]
        return self._flip_bits_on_vectors(bitflips, vectors)
    
    def _flip_bits_on_vectors(self, bitflips, vectors):
        for i, b in enumerate(bitflips):
            v_index, bit_index = divmod(128+i, 128)
            if b == 1:
                vectors[v_index].flip(bit_index)
        return vectors
    
    def _recompute_X(self, D, X):
        AD = self._build_AD(D)
        AD_X = AD*X
        n_rows = 0
        zero_rows = 0
        vectors = list()
        # Get nonzero rows of AD_X.
        for i in xrange(AD_X.rows()):
            row = AD_X[i]
            if row != 0:
                vectors.append(row)
                n_rows += 1
            else:
                zero_rows += 1
            if n_rows + zero_rows == self.tag_len:
                break 

        if n_rows != 0:
            li_vectors = BitVector.li_subset(vectors)
            K = BitMatrix._new(li_vectors)
            new_X = K.kernel().to_matrix().transpose()
            X *= new_X
        
        return n_rows != 0, X
    
    def recover_key(self):
        n = len(self.D) - 1
        r = n - 1
        X = BitMatrix.identity(128)
        should_build_T = True
        
        while True:
            if should_build_T:
                T = self._build_dependency_matrix(X, r)
            D = self._find_valid_D(T)
            should_build_T, X = self._recompute_X(D, X)
            if X.columns() == 1:
                break
            r = (128*n) / X.columns()
            if r * X.columns() == 128*n:
                r -= 1
            r = min(r, self.tag_len - 1)
            
        h = X.transpose()[0]
        z = self.GF2k.element(h)
        return self._from_field_elem(z)