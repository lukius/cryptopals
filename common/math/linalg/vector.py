import random

from fractions import Fraction


class Vector(object):
    
    @classmethod
    def null(cls, n):
        return Vector(n)
    
    @classmethod
    def rand_int_vector(cls, n, lo=-100, hi=100):
        v = [random.randint(lo,hi) for _ in xrange(n)]
        return Vector(v)
    
    @classmethod
    def _new(cls, v, norm_sq):
        u = Vector(0)
        u.v = v
        u.norm_sq = norm_sq
        return u
    
    def __init__(self, obj):
        if isinstance(obj, int):
            self.v = [0 for _ in xrange(obj)]
            self.norm_sq = 0
        elif isinstance(obj, (list, tuple)):
            self.v = list(obj)
            self.norm_sq = sum([e*e for e in self.v])
            
    def _scalar_mult(self, x):
        vx = map(lambda e: e*x, self.v)
        return Vector._new(vx, x*x*self.norm_sq)
        
    def _dot(self, u):
        if id(self) == id(u):
            return self.norm_sq
        if len(u) != len(self.v):
            raise Exception
        return reduce(lambda s, (i,e): s + u[i]*e,
                      enumerate(self.v),
                      0)
        
    def __add__(self, u):
        if u == 0:
            return Vector._new(list(self.v), self.norm_sq)
        if not isinstance(u, (Vector,list)) or\
           len(u) != len(self.v):
            raise Exception
        
        vu = [0 for _ in xrange(len(self.v))]
        b = 0
        for i in xrange(len(self.v)):
            x = self.v[i] + u[i]
            vu[i] = x
            b += x*x       
        return Vector._new(vu, b)
    
    def __radd__(self, x):
        return self + x
    
    def __sub__(self, u):
        if u == 0:
            return Vector._new(list(self.v), self.norm_sq)
        if not isinstance(u, (Vector,list)) or\
           len(u) != len(self.v):
            raise Exception
        
        vu = [0 for _ in xrange(len(self.v))]
        b = 0
        for i in xrange(len(self.v)):
            x = self.v[i] - u[i]
            vu[i] = x
            b += x*x       
        return Vector._new(vu, b)
        
    def __mul__(self, x):
        if isinstance(x, Vector):
            return self._dot(x)
        if isinstance(x, (int, Fraction)):
            return self._scalar_mult(x)
        else:
            raise Exception
        
    def __rmul__(self, x):
        return self * x
    
    def __len__(self):
        return len(self.v)
    
    def __getitem__(self, i):
        return self.v[i]
    
    def __setitem__(self, i, k):
        x = self.v[i]
        self.v[i] = k
        self.norm_sq = self.norm_sq - x*x + k*k
        
    def __neg__(self):
        return self * (-1)
    
    def __eq__(self, u):
        if u == 0:
            return all(map(lambda (i,e): e == 0,
                       enumerate(self.v)))
        if not isinstance(u, Vector) or\
           len(u) != len(self.v):
            return False
        return all(map(lambda (i,e): e == u[i],
                       enumerate(self.v)))
        
    def __hash__(self):
        return id(self) ^ hash(self.v)
    
    def __repr__(self):
        return '(%s)' % (repr(self.v)[1:-1])