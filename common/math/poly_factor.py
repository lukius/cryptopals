import math

from collections import defaultdict

from common.math.gcd import GCD


class SquarefreeFactorization(object):
    
    def factor(self, f):
        if f == 0:
            return [(f,1)]
        i = 1
        R = 1
        f = f.clone()
        g = f.derivative()
        if g != 0:
            c = GCD().value(f, g)
            w = f / c
            while not w.is_unit():
                y = GCD().value(w, c)
                z = w / y
                R *= z**i
                i += 1
                w = y
                c = c / y
            factors = [(R,1)]
            if not c.is_unit():
                c = c.x2_to_x()
                factors += map(lambda (p,k): (p,2*k), self.factor(c))
        else:
            f = f.x2_to_x()
            factors = map(lambda (p,k): (p,2*k), self.factor(f))

        return factors
        
        
class DistinctDegreeFactorization(object):
    
    def factor(self, f):
        f1 = f.clone()
        i = 1
        factors = list()
        x = f.ring.x()
        x_q = f.ring.pow_mod(x, f.ring.field_order(), f1)
        while f1.degree() >= 2*i:
            g = GCD().value(f1, x_q + x)
            if not g.is_unit():
                factors.append((g,i))
                f1 /= g
            i += 1
            x_q = x_q**2 % f1
        if f1 != 1:
            factors.append((f1, f1.degree()))
            
        if not factors:
            factors = [(f,1)]
            
        return factors
    
    
class EqualDegreeFactorization(object):
    
    def factor(self, f, d):
        if f.degree() == d:
            return [f]
        k = int(math.log(f.ring.field_order(), 2))
        while True:
            T = f.ring.rand_element(2*d - 1)
            if T.degree() < 1:
                continue
            W = T
            for _ in xrange(k*d-1):
                T = T**2 % f
                W += T
            g = GCD().value(f, W)
            if not g.is_unit() and g.degree() < f.degree():
                f1 = g
                f2 = f / g
                return self.factor(f1, d) + self.factor(f2, d)
            
            
class GF2kPolyFactorization(object):
    
    def factor(self, f):
        f = f.to_monic()
        factors = defaultdict(lambda: 0)
        sqf_factors = SquarefreeFactorization().factor(f)
        for g,k in sqf_factors:
            if g in factors:
                factors[g] += k
                continue
            dd_factors = DistinctDegreeFactorization().factor(g)
            for h,d in dd_factors:
                if h in factors:
                    factors[h] += k
                    continue
                ed_factors = EqualDegreeFactorization().factor(h,d)
                for p in ed_factors:
                    factors[p] += k
        return map(lambda (p,k): (p.to_monic(), k), factors.items())