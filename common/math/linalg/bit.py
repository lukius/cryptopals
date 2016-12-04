import random


class BitVector(object):
    
    @classmethod
    def random(cls, n):
        k = random.randint(0, (1 << n) - 1)
        return cls._new(n, k)
    
    @classmethod
    def _new(cls, n, k):
        v = BitVector(n)
        v.k = k
        return v
    
    def __init__(self, obj):
        if isinstance(obj, (int,long)):
            self.n = obj
            self.k = 0
        elif isinstance(obj, (list, tuple)):
            self.n = len(obj)
            self.k = 0
            i = 1 << (self.n - 1)
            for b in obj:
                if b == 1:
                    self.k += i
                i >>= 1
                
    def clone(self):
        return self._new(self.n, self.k)
                
    def flip(self, i):
        self[i] = 1 - self[i]
            
    def __add__(self, x):
        if not isinstance(x, BitVector) or self.n != x.n:
            raise Exception
        r = self.k ^ x.k
        return self._new(self.n, r)
    
    def __radd__(self, x):
        return self.__add__(x)
    
    def __mul__(self, x):
        if isinstance(x, (int,long)):
            x %= 2
            if x == 1:
                return self.clone()
            else:
                return BitVector._new(self.n, 0)
            
        if not isinstance(x, BitVector) or self.n != x.n:
            raise Exception
        
        i = self.n
        r = 0
        b = 1 << self.n
        while i > 0:
            b >>= 1
            if self.k & b and x.k & b:
                r += 1
            i -= 1
            
        return r % 2
    
    def __rmul__(self, x):
        return self.__mul__(x)
    
    def __len__(self):
        return self.n
    
    def __getitem__(self, i):
        if i < 0 or i >= self.n:
            raise IndexError
        i = self.n - i - 1
        return (self.k & (1 << i)) >> i
    
    def __setitem__(self, i, k):
        if i < 0 or i >= self.n:
            raise IndexError
        i = self.n - i - 1
        if k % 2 == 0:
            self.k ^= (self.k & (1 << i))
        else:
            self.k |= 1 << i
        
    def __eq__(self, u):
        if u == 0:
            return self.k == 0
        if not isinstance(u, BitVector):
            return False
        return self.n == u.n and self.k == u.k
    
    def __ne__(self, u):
        return not self.__eq__(u)
        
    def __hash__(self):
        return hash(self.n) ^ hash(self.k)
    
    def __repr__(self):
        v = list()
        k = self.k
        while k > 0:
            v.insert(0, '1' if k&1 else '0')
            k >>= 1
        if len(v) < self.n:
            v = ['0']*(self.n - len(v)) + v
        return '(%s)' % (','.join(v))
    
    
class BitMatrix(object):
    
    @classmethod
    def identity(cls, n):
        I = [BitVector([(1 if i==j else 0) for i in xrange(n)])
             for j in xrange(n)]
        return cls._new(I)
    
    @classmethod
    def random(cls, n, m):
        M = [BitVector.random(m) for _ in xrange(n)]
        return cls._new(M)
    
    @classmethod
    def _new(cls, M):
        n = len(M)
        m = len(M[0])
        return BitMatrix(n, m, M)
    
    def __init__(self, n, m, M=None):
        self.n = n
        self.m = m
        self.M = M or [BitVector(m) for _ in xrange(n)]
        
    def rows(self):
        return self.n
    
    def columns(self):
        return self.m
    
    def dim(self):
        return (self.n, self.m)
    
    def swap_rows(self, i, j):
        self.M[i], self.M[j] = self.M[j], self.M[i]
    
    def transpose(self):
        T = BitMatrix(self.m, self.n)
        for i,v in enumerate(self.M):
            T.set_column(i, v)
        return T
    
    def kernel(self):
        def msb_index(v, i=None):
            i = i or 0
            while i < len(v) and v[i] == 0:
                i += 1
            return i
        
        basis = list()

        T = self.transpose()
        W = sorted(enumerate(T.M), key=lambda x: msb_index(x[1]))
        I = list()
        for i, _ in W:
            row = BitVector([(1 if i==j else 0) for j in xrange(T.n)])
            I.append(row)
        I = self._new(I)
        
        k = msb_index(W[0][1])
        k_row = 0
        i = 1
        
        while i < T.n:
            j = msb_index(W[i][1], k) 
            if j == len(W[i][1]):
                break
            if j > k:
                k = j
                k_row = i
                i += 1
                continue
            W[i] = (W[i][0], W[i][1] + W[k_row][1])
            I.M[i] += I.M[k_row]
            k1 = msb_index(W[i][1], j+1)
            if k1 == len(W[i][1]):
                basis.append(I.M[i])
                i += 1
            else:
                j = i
                while j < T.n - 1 and k1 > msb_index(W[j+1][1], k):
                    W[j], W[j+1] = W[j+1], W[j]
                    I.swap_rows(j, j+1)
                    j += 1
                if j == i:
                    k = k1
                    k_row = i
                    i += 1
                
        while i < T.n:
            j = msb_index(W[i][1], k)
            if j == len(W[i][1]):
                basis.append(I.M[i])
            i += 1
            
        return GF2VectorSpace(basis, self.m)
    
    def pow(self, M, i):
        # TODO: refactor.
        result = BitMatrix.identity(M.n)
        while i > 0:
            if i % 2 == 1:
                result *= M
            i >>= 1
            M = M*M
        return result    
        
    def set_column(self, j, v):
        if len(v) != self.n:
            raise Exception
        
        for i in xrange(self.n):
            self[i,j] = v[i]
            
    def add_row(self, v):
        if len(v) != self.m or not isinstance(v, BitVector):
            raise Exception
        
        self.M.append(v.clone())
        self.n += 1
            
    def _mul_vec(self, v):
        if len(v) != self.m:
            raise Exception
        
        r = BitVector(self.n)
        
        for i in xrange(self.n):
            for j in xrange(self.m):
                r[i] ^= self[i,j] * v[j]
            
        return r 

    def _mul_mat(self, M):
        if self.m != M.n:
            raise Exception
        
        R = BitMatrix(self.n, M.m)
        
        for i in xrange(self.n):
            for j in xrange(self.m):
                for k in xrange(self.m):
                    R[i,j] ^= self[i,k] * M[k,j]
        
        return R
            
    def __add__(self, M):
        if not isinstance(M, BitMatrix):
            raise Exception
        if self.n != M.n or self.m != M.m:
            raise Exception
        
        R = BitMatrix(self.n, self.m)
        
        for i in xrange(self.n):
            for j in xrange(self.m):
                R[i,j] = self[i,j] ^ M[i,j]
                
        return R
    
    def __mul__(self, obj):
        if isinstance(obj, BitVector):
            return self._mul_vec(obj)
        elif isinstance(obj, BitMatrix):
            return self._mul_mat(obj)
        else:
            raise Exception
        
    def __pow__(self, i):
        if self.n != self.m:
            raise Exception
        return self.pow(self, i)
            
    def __getitem__(self, pos):
        i, j = pos
        if 0 <= i < self.n and 0 <= j < self.m:
            return self.M[i][j]
        else:
            raise IndexError

    def __setitem__(self, pos, x):
        i, j = pos
        if 0 <= i < self.n and 0 <= j < self.m:
            self.M[i][j] = x % 2
        else:
            raise IndexError
        
    def __len__(self):
        return self.n * self.m
    
    def __repr__(self):
        M_str = str()
        for i in xrange(self.n):
            s = '\n' if i > 0 else str()
            M_str += s + repr(self.M[i])
        return M_str
    
    
class GF2VectorSpace(object):
    
    def __init__(self, basis, n):
        # TODO: assuming linearly independent vectors.
        self.n = n
        self.basis = set(basis)
        
    def dim(self):
        return len(self.basis)
    
    def rand_vector(self):
        if self.dim() > 0:
            scalars = [random.randint(0,1) for _ in xrange(self.dim())]
            return reduce(lambda v, (k,u): v + k*u,
                          zip(scalars, self.basis),
                          BitVector(self.n))
            
    def __repr__(self):
        v_reprs = list()
        for v in self.basis:
            v_reprs.append(repr(v))
        return '<%s>' % ', '.join(v_reprs)