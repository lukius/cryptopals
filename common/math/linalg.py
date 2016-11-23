import copy
import random

from fractions import Fraction


class BasisOrthogonalizer(object):
    
    # Computation of orthogonal basis using Gram-Schmidt.

    def _projection(self, u, v):
        if u == 0:
            return Vector.null(len(u))
        return Fraction(v*u, u*u) * u

    def orthogonalize(self, basis):
        Q = list()
        for i, v in enumerate(basis):
            w = v - sum([self._projection(u, v) for u in Q[:i]])
            Q.append(w)
        return Q


class LatticeBasisReduction(object):
    
    # Basis reduction using the LLL algorithm.
    
    DELTA = 0.99
    
    def _mu(self, u, v):
        return Fraction(v*u, v*v)   
    
    def reduce(self, basis):
        B = copy.copy(basis)
        orthogonalizer = BasisOrthogonalizer()
        Q = orthogonalizer.orthogonalize(basis)
        k = 1
        while k < len(B):
            for j in xrange(k-1, -1, -1):
                mu = self._mu(B[k], Q[j])
                if abs(mu) > 0.5:
                    B[k] = B[k] - B[j]*int(round(mu))
                    for i in xrange(k, len(Q)):
                        v = B[i]
                        w = v - sum([orthogonalizer._projection(u, v)\
                                     for u in Q[:i]])
                        Q[i] = w
            a = Q[k]*Q[k]
            b = (self.DELTA - self._mu(B[k], Q[k-1])**2) * (Q[k-1]*Q[k-1])
            if a >= b:
                k += 1
            else:
                B[k], B[k-1] = B[k-1], B[k]
                for i in xrange(k-1, len(Q)):
                    v = B[i]
                    w = v - sum([orthogonalizer._projection(u, v)\
                                 for u in Q[:i]])
                    Q[i] = w                
                k = max(k-1, 1)
        return B
                    
    
class Vector(object):
    
    @classmethod
    def null(cls, n):
        return Vector(n)
    
    @classmethod
    def rand_int_vector(cls, n, lo=-100, hi=100):
        v = [random.randint(lo,hi) for _ in xrange(n)]
        return Vector(v)
    
    def __init__(self, obj):
        if isinstance(obj, int):
            self.v = [0 for _ in xrange(obj)]
        elif isinstance(obj, (list, tuple)):
            self.v = list(obj)
        
    def _scalar_mult(self, x):
        vx = map(lambda e: e*x, self.v)
        return Vector(vx)
        
    def _dot(self, u):
        if len(u) != len(self.v):
            raise Exception
        return reduce(lambda s, (i,e): s + u[i]*e,
                      enumerate(self.v),
                      0)
        
    def __add__(self, u):
        if u == 0:
            return Vector(self.v)
        if not isinstance(u, Vector) or\
           len(u) != len(self.v):
            raise Exception        
        vu = map(lambda (i,e): e + u[i], enumerate(self.v))
        return Vector(vu)
    
    def __radd__(self, x):
        return self + x
    
    def __sub__(self, u):
        return self + (-u)
        
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
        self.v[i] = k
        
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