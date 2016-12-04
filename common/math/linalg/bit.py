import random


class BitVector(object):
    
    @classmethod
    def random(cls, n):
        k = random.randint(0, 1 << n)
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
        I = [[(1 if i==j else 0) for i in xrange(n)] for j in xrange(n)]
        return cls._new(I)
    
    @classmethod
    def random(cls, n, m):
        M = [[random.randint(0,1) for _ in xrange(n)] for _ in xrange(m)]
        return cls._new(M)
    
    @classmethod
    def _new(cls, M):
        n = len(M)
        m = len(M[0])
        return BitMatrix(n, m, M)
    
    def __init__(self, n, m, M=None):
        self.n = n
        self.m = m
        self.M = M or [[0 for _ in xrange(n)] for _ in xrange(m)]
        
    def rows(self):
        return self.n
    
    def columns(self):
        return self.m
    
    def dim(self):
        return (self.n, self.m)
    
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
        if len(v) != self.n or not isinstance(v, BitVector):
            raise Exception
        
        for i in xrange(self.n):
            self[i,j] = v[i]
            
    def add_row(self, v):
        if len(v) != self.m or not isinstance(v, BitVector):
            raise Exception
        
        v = [v[i] for i in xrange(self.m)]
        self.M.append(v)
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
        
        result = [[0 for _ in xrange(self.n)] for _ in xrange(self.m)]
        
        for i in xrange(self.n):
            for j in xrange(self.m):
                result[i][j] = self[i,j] ^ M[i,j]
                
        return self._new(result)
    
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