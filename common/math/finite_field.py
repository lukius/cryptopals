from common.math.gcd import ExtendedGCD
from common.math.linalg.bit import BitMatrix
from common.math.poly.poly import GF2Poly
from common.math.poly.ring import GF2PolyRing
from common.math.structures import AbstractGroup


class GF2k(GF2PolyRing, AbstractGroup):
    
    @classmethod
    def elem_class(cls):
        return GF2kElement    
    
    def __init__(self, k, modulus):
        GF2PolyRing.__init__(self)
        AbstractGroup.__init__(self)
        self.k = k
        mod, mod_deg = self._parse_poly(modulus)
        self.mod = GF2kElement(self, mod, mod_deg)
        
    def to_bit_matrix(self, f):
        x = self.x()
        z = self.identity()
        M = BitMatrix(self.k, self.k)
        for j in xrange(self.k):
            v = f(z).to_bit_vector()
            M.set_column(self.k - j - 1, v)
            z *= x
        return M

    def element(self, obj):
        p = GF2PolyRing.element(self, obj)
        return self.rem(p, self.mod)
    
    def order(self):
        return 2**self.k
    
    def square_root(self, x):
        return x**(2**(-1 % self.k))

    # Abstract group interface (modular multiplication).    
    def add(self, a, b):
        p_n = 0
        a_n = a.n
        b_n = b.n
        b_deg = b.deg

        while a_n > 0:
            if a_n & 1:
                p_n ^= b_n

            a_n >>= 1
            b_n <<= 1
            b_deg += 1

            if b_deg == self.mod.deg:
                b_n ^= self.mod.n
                b_deg = self._get_deg(b_n)

        return GF2kElement(self, p_n)
    
    # Abstract group interface.
    def invert(self, a):
        p, _, gcd = ExtendedGCD().value(a, self.mod)
        if gcd != 1:
            raise Exception('%r not invertible in %r --use irreducible modulus!'%\
                            (a, self))
        return p
    
    def __eq__(self, obj):
        if type(obj) != type(self):
            return False
        return self.k == obj.k and self.mod == obj.mod
    
    def __hash__(self):
        return hash(self.k) ^ hash(self.mod)
    
    def __repr__(self):
        return 'GF(2^%d) (with modulus %r)' % (self.k, self.mod)


class GF2kElement(GF2Poly):
    
    def __init__(self, field, n, deg=None):
        GF2Poly.__init__(self, field, n, deg)
        self.field = field