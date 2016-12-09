import random

from common.math.linalg.bit import BitVector
from common.math.poly.poly import GF2Poly, GF2kPoly
from common.math.structures import AbstractMonoid


class GF2PolyRing(AbstractMonoid):
    
    @classmethod
    def elem_class(cls):
        return GF2Poly
    
    def _get_deg(self, n):
        if n <= 1:
            deg = n-1
        else:
            deg = 0
            i = 2
            while i <= n:
                i <<= 1
                deg += 1
        return deg

    def _parse_poly(self, mod_str):
        try:
            k_set = set()
            mod_str = mod_str.lower()
            summands = map(lambda s: s.strip(), mod_str.split('+'))
            
            for xk in summands:
                if xk == '0':
                    continue
                if xk == '1':
                    k = 0
                elif xk == 'x':
                    k = 1
                elif xk[0] == 'x':
                    _, k = xk.split('^')
                    k = int(k)
                else:
                    raise Exception
                
                if k in k_set:
                    k_set.remove(k)
                else:
                    k_set.add(k)
                    
            n = 0
            for k in k_set:
                n += 1 << k
                
            return n, max(k_set) if k_set else -1
        except:
            raise Exception('bad GF(2)[X] element format.')
        
    def field_order(self):
        return 2        
        
    def pow_mod(self, a, n, b):
        result = self.identity()
        while n > 0:
            if n % 2 == 1:
                result = self.add(result, a) % b
            n >>= 1
            a = self.add(a, a) % b
        return result
        
    def element(self, obj):
        if isinstance(obj, (int,long)):
            n = obj
            deg = None
            
        elif isinstance(obj, basestring):
            n, deg = self._parse_poly(obj)
        
        elif isinstance(obj, BitVector):
            n, deg = obj.k, obj.n
            
        return self.elem_class()(self, n, deg)

    def rand_element(self, max_deg=None):
        max_deg = 2**max_deg if max_deg is not None else 1<<128
        n = random.randint(1, max_deg)
        return self.element(n)
    
    # Abstract monoid interface.
    def identity(self):
        return self.element(1)    

    # Abstract monoid interface (polynomial multiplication).    
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

        return self.elem_class()(self, p_n)    
    
    def divmod(self, a, b):
        if b == 0:
            raise ZeroDivisionError
            
        q_n, r_n = 0, a.n
        b_n = b.n
        b_deg, r_deg = b.deg, a.deg
        
        while r_deg >= b_deg:
            d = r_deg - b_deg
            q_n ^= 1 << d
            r_n ^= b_n << d
            r_deg = self._get_deg(r_n)

        q = self.elem_class()(self, q_n)
        r = self.elem_class()(self, r_n, r_deg)
        
        return q, r
    
    def div(self, a, b):
        return self.divmod(a, b)[0]
    
    def rem(self, a, b): 
        return self.divmod(a, b)[1]
    
    def derivative(self, a):
        n = a.n
        i = 0
        m = 0
        k = 0
        while n > 0:
            if i % 2 == 1 and n & 1:
                m |= k
            n >>= 1
            i += 1
            k = k<<1 if k > 0 else 1
        return self.element(m)
    
    def x2_to_x(self, a):
        n = a.n
        i = 0
        m = 0
        while n > 0:
            if n & 1:
                if i == 0:
                    m |= 1
                else:
                    m |= 1 << (i/2)
            n >>= 1
            i += 1
        return self.element(m)
    
    def x(self):
        return self.element('X')
    
    def __repr__(self):
        return 'GF(2)[X]'
    
    
class GF2kPolyRing(GF2PolyRing):
    
    def __init__(self, GF2k):
        GF2PolyRing.__init__(self)
        self.GF2k = GF2k
        
    def field_order(self):
        return self.GF2k.order()
        
    def element(self, obj):
        if isinstance(obj, (int,GF2Poly)):
            if obj != 0:
                coeffs = [(obj,0)]
            else:
                coeffs = list()
        elif isinstance(obj, list):
            coeffs = obj
        return GF2kPoly(self, coeffs)
    
    def rand_element(self, max_deg=None):
        max_deg = max_deg or 1<<128
        degs = random.randint(1, 2**(max_deg+1))
        coeffs = list()
        d = 0
        while degs > 0:
            if degs & 1:
                k = self.GF2k.rand_element()
                coeffs.insert(0, (k,d))
            d += 1
            degs >>= 1
        return GF2kPoly(self, coeffs)

    # Abstract monoid interface (polynomial multiplication).
    def add(self, a, b):
        coeffs = dict()
        for k1,d1 in b.coeffs:
            for k2,d2 in a.coeffs:
                if d1+d2 in coeffs:
                    coeffs[d1+d2] += k1 * k2
                else:
                    coeffs[d1+d2] = k1 * k2
        coeffs = map(lambda (d,k): (k,d), coeffs.items())
        coeffs = sorted(coeffs, key=lambda x: x[1], reverse=True)
        return GF2kPoly(self, coeffs)
    
    def divmod(self, a, b):
        if b == 0:
            raise ZeroDivisionError
        
        q = 0
        a = a.clone()
        x = self.x()

        if b.degree() == 0:
            a *= b.coefficient().invert()
            return a, self.element(0)
        
        while a.degree() >= b.degree():
            b_k = b.coefficient().invert()
            k = a.coefficient() * b_k
            d = a.degree() - b.degree()
            p = k * x**d
            q += p
            a += p * b
            
        return q, a
    
    def derivative(self, a):
        coeffs = list()
        for k, d in a.coeffs:
            if d & 1:
                coeffs.append((k, d-1))
        return GF2kPoly(self, coeffs)
    
    def x2_to_x(self, a):
        coeffs = list()
        for k, d in a.coeffs:
            k = self.GF2k.square_root(k)
            coeffs.append((k, d/2))
        return GF2kPoly(self, coeffs)
    
    def x(self):
        return self.element([(self.GF2k.identity(),
                              1)])
    
    def __repr__(self):
        return 'GF(2^%d)[X]' % self.GF2k.k