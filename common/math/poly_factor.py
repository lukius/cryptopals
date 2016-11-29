from common.math.gcd import GCD


class SquarefreeFactorization(object):
    
    def factor(self, f):
        # TODO: ensure f is monic when factoring over GF(2^k).
        if f == 0:
            return [(f,1)]
        i = 1
        R = 1
        f = f.clone()
        g = f.derivative()
        if g != 0:
            c = GCD().value(f, g)
            w = f / c
            while w != 1:
                y = GCD().value(w, c)
                z = w / y
                R *= z**i
                i += 1
                w = y
                c = c / y
            factors = [(R,1)]
            if c != 1:
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
        x_q = x**2
        while f1.degree() >= 2*i:
            g = GCD().value(f1, x_q + x)
            if g != 1:
                factors.append((g,i))
                f1 /= g
            i += 1
            x_q = x_q**2 % f1
        if f1 != 1:
            factors.append((f1, f1.degree()))
            
        if not factors:
            factors = [(f,1)]
            
        return factors