import random

from common.math.structures import AbstractMonoid
from common.tools.misc import SetBits


class BitVector(object):
    
    @classmethod
    def random(cls, n):
        k = random.randint(0, (1 << n) - 1)
        return cls._new(n, k)
    
    @classmethod
    def li_subset(cls, vectors):
        li_vectors = list(vectors) 

        if vectors:
            M = BitMatrix._new([v.clone() for v in vectors])
            T, _ = BitMatrixRowReduction().reduce(M)
            for i in xrange(T.rows()):
                if T[i] == 0:
                    del li_vectors[i]
                
        return li_vectors
    
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
        
        return SetBits().value(self.k & x.k) % 2
    
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
    
    
class BitMatrix(AbstractMonoid):
    
    @classmethod
    def Id(cls, n):
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
        self.M_cols = list()
        for i in xrange(self.m):
            v = BitVector(self.n)
            for j in xrange(self.n):
                v[j] = self.M[j][i]
            self.M_cols.append(v)
            
    def clone(self):
        M = list()
        for v in self.M:
            M.append(v.clone())
        return self._new(M)
        
    def rows(self):
        return self.n
    
    def columns(self):
        return self.m
    
    def dim(self):
        return (self.n, self.m)
    
    # Monoid interface
    def identity(self):
        if self.n != self.m:
            raise Exception
        return BitMatrix.Id(self.n)
    
    # Monoid interface
    def add(self, M, N):
        return M.__mul__(N)

    def transpose(self):
        T = list()
        for v in self.M_cols:
            T.append(v)
        return self._new(T)
    
    def kernel(self):
        basis = list()
        T, S = BitMatrixRowReduction().reduce(self.transpose())
        for i in xrange(T.rows()):
            if T[i] == 0:
                basis.append(S[i])
        return GF2VectorSpace(basis, self.m)
    
    def set_column(self, j, v):
        if len(v) != self.n:
            raise Exception
        
        self.M_cols[j] = v
        for i in xrange(self.n):
            self[i,j] = v[i]
            
    def add_row(self, v):
        if len(v) != self.m or not isinstance(v, BitVector):
            raise Exception
        
        self.M.append(v.clone())
        self.n += 1
        for j in xrange(self.m):
            k = (self.M_cols[j].k << 1) + v[j]
            self.M_cols[j] = BitVector._new(self.n, k)
            
    def _mul_vec(self, v):
        if len(v) != self.m:
            raise Exception
        
        r = list()
        
        for i in xrange(self.n):
            r.append(self.M[i] * v)

        return BitVector(r) 

    def _mul_mat(self, M):
        if self.m != M.n:
            raise Exception
        
        set_bits = SetBits()
        R = list()
        
        for i in xrange(self.n):
            v = BitVector(M.m)
            for j in xrange(M.m):
                k = self.M[i].k & M.M_cols[j].k
                v[j] = set_bits.value(k) % 2
            R.append(v)
        
        return BitMatrix._new(R)
            
    def __add__(self, M):
        if not isinstance(M, BitMatrix):
            raise Exception
        if self.n != M.n or self.m != M.m:
            raise Exception
        
        R = list()
        
        for i in xrange(self.n):
            k = self.M[i].k ^ M.M[i].k
            u = BitVector._new(self.m, k)
            R.append(u)
                
        return self._new(R)
    
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
        if isinstance(pos, (int, long)):
            return self._get_row(pos)
        elif isinstance(pos, (tuple,list)):
            return self._get_cell(*pos)
        else:
            raise Exception
            
    def _get_cell(self, i, j):
        if 0 <= i < self.n and 0 <= j < self.m:
            return self.M[i][j]
        else:
            raise IndexError
        
    def _get_row(self, i):
        if 0 <= i < self.n:
            return self.M[i]
        else:
            raise IndexError

    def __setitem__(self, pos, x):
        if isinstance(pos, (int, long)):
            return self._set_row(pos, x)
        elif isinstance(pos, (tuple,list)):
            i, j = pos
            return self._set_cell(i, j, x)
        else:
            raise Exception        
        
    def _set_cell(self, i, j, x):
        if 0 <= i < self.n and 0 <= j < self.m:
            self.M[i][j] = x % 2
            self.M_cols[j][i] = x % 2
        else:
            raise IndexError
        
    def _set_row(self, i, x):
        if 0 <= i < self.n and len(x) == self.m:
            self.M[i] = x
            for j in xrange(len(x)):
                self.M_cols[j][i] = x[j]
        else:
            raise IndexError        
        
    def __len__(self):
        return self.n * self.m
    
    def __eq__(self, M):
        if not isinstance(M, BitMatrix) or self.dim() != M.dim():
            return False
        
        for i in xrange(self.n):
            if self[i] != M[i]:
                return False
            
        return True
    
    def __hash__(self):
        return reduce(lambda s,v: s ^ hash(v), self.M, 0)
    
    def __repr__(self):
        M_str = str()
        for i in xrange(self.n):
            s = '\n' if i > 0 else str()
            M_str += s + repr(self.M[i])
        return M_str
    
    
class GF2VectorSpace(object):
    
    def __init__(self, basis, n):
        self.n = n
        self.B = BitVector.li_subset(basis)
        
    def dim(self):
        return len(self.B)
    
    def basis(self):
        return self.B
    
    def to_matrix(self):
        B = [v.clone() for v in self.B]
        return BitMatrix._new(B)
    
    def rand_vector(self):
        if self.dim() > 0:
            scalars = [random.randint(0,1) for _ in xrange(self.dim())]
            return reduce(lambda v, (k,u): v + k*u,
                          zip(scalars, self.B),
                          BitVector(self.n))
            
    def __repr__(self):
        v_reprs = list()
        for v in self.B:
            v_reprs.append(repr(v))
        return '<%s>' % ', '.join(v_reprs)
    
    
class BitMatrixRowReduction(object):
    
    def _msb_index(self, v, i=None):
        i = i or 0
        while i < len(v) and v[i] == 0:
            i += 1
        return i
    
    def reduce(self, B):
        n, m = B.dim()
        d = {self._msb_index(B[0]) : 0}
        M = [B[0].clone()]
        I = [BitVector._new(n, 1<<(n-1))]
        for i in xrange(1, n):
            M.append(B[i].clone())
            I.append(BitVector._new(n, 1<<(n-i-1)))
            k = self._msb_index(M[i])
            if k not in d:
                d[k] = i
                continue
            while True:
                M[i] += M[d[k]]
                I[i] += I[d[k]]
                k = self._msb_index(M[i], k+1)
                if k == m:
                    break
                if k not in d:
                    d[k] = i
                    break
        return BitMatrix._new(M), BitMatrix._new(I)