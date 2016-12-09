import threading

from common.attacks.gcm import GCMAuthSubkeyRecoveryAttack
from common.math.linalg.bit import BitVector, BitMatrix
from common.tools.concurrency import ConcurrentTask, ConcurrentTaskManager


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
        # To speed up the computation of the dependency matrices, we can first
        # precompute an array of matrices AD[1..n-1][0..127] where AD[i][j]
        # represents the i-th component of the summation that defines AD 
        # for an array of bit vectors D where the only 1 bit is D[i][j]. 
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

    def _AD_i(self, D_i, Msq_i):
        w = self.GF2k.element(D_i)
        Mv = self.GF2k.to_bit_matrix(lambda z: w*z)
        return Mv * Msq_i

    def _build_AD(self, D):
        AD = BitMatrix(128, 128)
        Msq = Msq_i = self.GF2k.to_bit_matrix(lambda z: z**2)
        for v in D[1:]:
            w = self.GF2k.element(v)
            Mv = self.GF2k.to_bit_matrix(lambda z: w*z)
            AD += Mv * Msq_i
            Msq_i *= Msq
        return AD

    def _build_dependency_matrix(self, X, r):
        # Dependency matrix where each column represents a bit in the blocks of
        # the ciphertext that we can flip and each row represents a cell in the
        # (AD*X) matrix. r is the number of rows of AD*X we can cover.
        T = BitMatrix(r*X.columns(), (len(self.D)-1)*128)

        with ConcurrentTaskManager() as task_manager:
            for i in xrange(1, len(self.D)):
                task_i = TComputationTask(T, i, r, self.AD[i], X)
                task_manager.add_task(task_i)
        
        return T
    
    def _find_valid_D(self, T):
        S = T.kernel()
        
        with ConcurrentTaskManager() as task_manager:
            tasks = [VectorDiscoveryTask(self, S)
                     for _ in xrange(task_manager.pool_size())]
            winner_task = task_manager.compete(tasks)
            
        return winner_task.result()
            
    def _recompute_X(self, D, X):
        AD = self._build_AD(D)
        AD_X = AD*X
        n_rows = 0
        zero_rows = 0
        vectors = list()
        
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
        X = BitMatrix.Id(128)
        should_build_T = True
        # r is the current number of rows of AD * X that we can nullify. 
        r = n - 1
        
        # Idea:
        #  * Build dependency matrix T from current X and r.
        #  * Find its kernel S and try random vectors in this vector space
        #    until we can assemble a ciphertext that passes validation.
        #  * Map this vector to difference vectors D[1],...,D[n].
        #  * Compute AD * X from D and find the nonzero rows from the first
        #    tag_len rows.
        #  * Compute the kernel of the linear map yielded by these nonzero rows.
        #  * Right-multiply the transposed matrix of the basis of this kernel
        #    with X (this is the new X).
        #  * Start over after recomputing r from X. Stop when X has only one
        #    column.
        while True:
            if should_build_T:
                # Only compute T if we have at least one nonzero rows.
                # Otherwise, we were unlucky with the random vector chosen; we
                # should try again.
                T = self._build_dependency_matrix(X, r)
            D = self._find_valid_D(T)
            should_build_T, X = self._recompute_X(D, X)
            if X.columns() == 1:
                break
            # As we need to have strictly less equations than free variables,
            # we need to ensure that r * X.columns() < 128 * n. Thus,
            # r <  (128*n) / X.columns(). 
            r = (128*n) / X.columns()
            if r * X.columns() == 128*n:
                r -= 1
            # Also, there has to be at least one nonzero row in AD * X.
            r = min(r, self.tag_len - 1)
         
        # X is a 128x1 bit matrix, and its column should be the authentication
        # subkey. We convert it to a field element z and finally we return
        # the byte string it represents.    
        h = X.transpose()[0]
        z = self.GF2k.element(h)
        
        return self._from_field_elem(z)
    
    
class TComputationTask(ConcurrentTask):
    
    MERGE_LOCK = threading.Lock()
    
    def __init__(self, T, i, r, AD_i, X):
        ConcurrentTask.__init__(self)
        self.i = i
        self.r = r
        self.AD_i = AD_i
        self.X = X
        self.T = list()
        self.on_finished = lambda: self.merge(T)
        
    def merge(self, T):
        M = self.queue.get()
        T_col = (self.i-1)*128
        for j, column in enumerate(M):
            with self.MERGE_LOCK:
                T.set_column(T_col + j, column) 
    
    def run(self):
        for j in xrange(128):
            AD_ij = self.AD_i[j]
            AD_X = AD_ij * self.X

            m = AD_X.columns()
            column = BitVector(self.r*m)
            
            for i in xrange(self.r):
                k = i*m
                for l in xrange(m):
                    AD_cell = k + l
                    column[AD_cell] = AD_X[i, l]
                    
            self.T.append(column)
            
        self.queue.put(self.T)
        
        
class VectorDiscoveryTask(ConcurrentTask):
    
    def __init__(self, parent, S):
        ConcurrentTask.__init__(self)
        self.parent = parent
        self.S = S
        self.queue.put(self.parent.ciphertext)
        
    def _new_ciphertext_blocks_from(self, bitflips):
        D = [v.clone() for v in self.parent.D]
        return self._flip_bits_on_vectors(bitflips, D)
    
    def _to_vectors(self, bitflips):
        vectors = [BitVector(128) for _ in xrange(len(self.parent.D))]
        return self._flip_bits_on_vectors(bitflips, vectors)
    
    def _flip_bits_on_vectors(self, bitflips, vectors):
        for i, b in enumerate(bitflips):
            v_index, bit_index = divmod(128+i, 128)
            if b == 1:
                vectors[v_index].flip(bit_index)
        return vectors       
        
    def _assemble_new_ciphertext(self, bitflips):
        C = self._new_ciphertext_blocks_from(bitflips)
        n = self.ciphertext.block_count()
        for i in xrange(1, len(C)):
            z = self.parent.GF2k.element(C[i])
            block = self.parent._from_field_elem(z)
            self.ciphertext.replace_block(n - 2**i + 1, block)
            
    def result(self):
        return self.queue.get()      
    
    def run(self):
        self.ciphertext = self.queue.get()
        while True:
            v = self.S.rand_vector()
            self._assemble_new_ciphertext(v)
            data = (self.ciphertext, self.parent.tag)
            result = self.parent.aes.decrypt(data, mode=self.parent.gcm)
            if result[0] is True:
                D = self._to_vectors(v)
                self.queue.put(D)
                break