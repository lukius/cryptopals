import copy
import random
import cxx_linalg

from fractions import Fraction


class LatticeBasisReduction(object):
    
    # Basis reduction using the LLL algorithm.
    
    DELTA = 0.99
    
    def _mu(self, u, v):
        return Fraction(v*u, v.norm_sq) 
    
    def _sum_proj(self, v, i, Q):
        w = [0 for _ in xrange(len(v))]
        v1 = [0 for _ in xrange(len(v))]
        for j in xrange(i):
            p = BasisOrthogonalizer._projection(Q[j], v)
            for k in xrange(len(v)):
                w[k] += p[k]
        norm_sq = 0
        for k in xrange(len(v)):
                v1[k] = v[k] - w[k]
                norm_sq += v1[k]*v1[k]
        return Vector._new(v1, norm_sq)
    
    def reduce_slow(self, basis):
        # Slow Python implementation of LLL algorithm. Essentially the same
        # strategy was ported to C++ and packed in a standalone Python-callable
        # module (which is in fact the one use when calling reduce, below).
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
                        Q[i] = self._sum_proj(B[i], i, Q)
            a = Q[k].norm_sq
            b = (self.DELTA - self._mu(B[k], Q[k-1])**2) * Q[k-1].norm_sq
            if a >= b:
                k += 1
            else:
                B[k], B[k-1] = B[k-1], B[k]
                for i in xrange(k-1, len(Q)):
                    Q[i] = self._sum_proj(B[i], i, Q)                
                k = max(k-1, 1)
        return B
    
    def reduce(self, basis):
        # Faster C++ implementation of LLL. This method just converts the input
        # to a Boost.Python friendly list and then the output to a
        # Python-friendly format.
        B = cxx_linalg.basis_reduction(_to_cxx_format(basis))
        return  _from_cxx_format(B)
    
    
class BasisOrthogonalizer(object):
    
    # Computation of orthogonal basis using Gram-Schmidt.

    @classmethod
    def _projection(cls, u, v):
        if u == 0:
            return Vector.null(len(u))
        return Fraction(v*u, u.norm_sq) * u

    def orthogonalize_slow(self, basis):      
        Q = list()
        for i, v in enumerate(basis):
            w = v - sum([self._projection(u, v) for u in Q[:i]])
            Q.append(w)
        return Q

    def orthogonalize(self, basis):
        # Same as before, through C++.
        Q = cxx_linalg.orthogonalize(_to_cxx_format(basis))
        return  _from_cxx_format(Q)
    
    
def _to_cxx_format(basis):
    new_basis = list()
    for v in basis:
        new_v = list()
        for x in v:
            frac_x = Fraction(x)
            num_str = str(frac_x.numerator)
            den_str = str(frac_x.denominator)
            new_v.append((num_str, den_str))
        new_basis.append(new_v)
    return new_basis


def _from_cxx_format(basis):
    new_basis = list()
    for v in basis:
        new_v = Vector(len(v))
        for i, (num,den) in enumerate(v):
            x = Fraction(int(num), int(den))
            new_v[i] = x
        new_basis.append(new_v)
    return new_basis    

    
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