import copy
import cxx_linalg

from fractions import Fraction

from common.math.linalg.vector import Vector


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