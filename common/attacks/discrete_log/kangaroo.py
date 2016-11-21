from common.math.group import Z_n
from common.math.modexp import ModularExp


class PollardKangarooAttack(object):
    
    DEFAULT_K = 22
    
    def __init__(self, group, g, p, k=None):
        self.p = p
        self.g = g
        self.k = k or self.DEFAULT_K
        self.group = group
        self.modexp = ModularExp(self.p)
        
    def _compute_N(self):
        # N (i.e., the number of the tame kangaroo jumps) is computed as 
        # 4m, with
        #   m = ([(p-1)/k] * sum_j 2^j mod p) / (p-1), 0 <= j < k
        # i.e., the mean value of the outputs of f. It is scaled with a 
        # factor of 4 following Pollard's analysis: if N = \Theta * m with
        # \Theta = 4, the probability of missing the wild kangaroo is about
        # 0.02.
        s = (self.modexp.value(2,self.k) - 1) % self.p
        w = (self.p-1)//self.k
        s *= w
        s //= self.p-1
        return 4*s 
    
    def _iterate(self, x, y):
        f_y = self.f(y)
        x += f_y
        g_f_y = self.group.pow(self.g, f_y)
        y = self.group.add(y, g_f_y)
        return x, y
    
    def _advance_tame_kangaroo(self, N, a, b):
        x_N = 0
        y_N = self.group.pow(self.g, b)
        for _ in xrange(N):
            x_N, y_N = self._iterate(x_N, y_N)            
        return x_N, y_N
    
    def _advance_wild_kangaroo(self, x_N, y_N, y, a, b):
        x_M = 0
        y_M = y
        while x_M < b - a + x_N:
            x_M, y_M = self._iterate(x_M, y_M)
            if y_M == y_N:
                return b + x_N - x_M
        
    def get_index(self, y, a, b): 
        # Computes i such that g**i = y mod p (a <= i <= b)
        N = self._compute_N()
        x_N, y_N = self._advance_tame_kangaroo(N,a,b)
        return self._advance_wild_kangaroo(x_N, y_N, y, a, b)
    
    
class IntegerKangarooAttack(PollardKangarooAttack):
    
    def __init__(self, g, p):
        Z_p = Z_n(p)
        PollardKangarooAttack.__init__(self, Z_p, g, p)
    
    def f(self, x):
        return self.modexp.value(2, x%self.k)


class EllipticCurveKangarooAttack(PollardKangarooAttack):

    def __init__(self, g, p):
        PollardKangarooAttack.__init__(self, g.curve, g, p)
    
    def f(self, P):
        return self.modexp.value(2, (P.x*P.y)%self.k)