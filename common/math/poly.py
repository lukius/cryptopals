import copy
import random

from common.math.group import AbstractGroup
from common.math.gcd import ExtendedGCD
from common.math.linalg.bit import BitVector, BitMatrix


class GF2PolyRing(object):
    
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
        
    def pow(self, a, n):
        # TODO: refactor. Cannot inherit form abstact group.
        result = self.element(1)
        while n > 0:
            if n % 2 == 1:
                result = self.add(result, a)
            n >>= 1
            a = self.add(a, a)
        return result

    def pow_mod(self, a, n, b):
        # TODO: refactor. Cannot inherit form abstact group.
        result = self.element(1)
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
            
        return GF2Poly(self, n, deg)

    def rand_element(self, max_deg=None):
        max_deg = 2**max_deg if max_deg is not None else 1<<128
        n = random.randint(1, max_deg)
        return self.element(n)
    
    def add(self, a, b):
        # Is actually 'mul', but the GF2k subclass implements the abstract
        # group interface.
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

        return GF2Poly(self, p_n)    
    
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

        q = GF2Poly(self, q_n)
        r = GF2Poly(self, r_n, r_deg)
        
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


class GF2k(GF2PolyRing, AbstractGroup):
    
    def __init__(self, k, modulus):
        GF2PolyRing.__init__(self)
        AbstractGroup.__init__(self)
        self.k = k
        mod, mod_deg = self._parse_poly(modulus)
        self.mod = GF2Poly(self, mod, mod_deg)
        
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

    # Modular multiplication    
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

        return GF2Poly(self, p_n)
    
    def invert(self, a):
        p, _, gcd = ExtendedGCD().value(a, self.mod)
        if gcd != 1:
            raise Exception('%r not invertible in %r --use irreducible modulus!'%\
                            (a, self))
        return p
    
    def identity(self):
        return self.element(1)
    
    def __eq__(self, obj):
        if type(obj) != type(self):
            return False
        return self.k == obj.k and self.mod == obj.mod
    
    def __hash__(self):
        return hash(self.k) ^ hash(self.mod)
    
    def __repr__(self):
        return 'GF(2^%d) (with modulus %r)' % (self.k, self.mod)
    
    
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
            if d != 0:
                coeffs.append((k, d/2))
            else:
                coeffs.append((k, 0))
        return GF2kPoly(self, coeffs)
    
    def x(self):
        return self.element([(self.GF2k.identity(),
                              1)])
    
    def __repr__(self):
        return 'GF(2^%d)[X]' % self.GF2k.k


class Char2FieldPoly(object):

    def __init__(self, ring):
        self.ring = ring

    def degree(self):
        return self.deg
    
    def coefficient(self):
        return self.coeff

    def derivative(self):
        return self.ring.derivative(self)
    
    def is_unit(self):
        return self.deg == 0

    def x2_to_x(self):
        return self.ring.x2_to_x(self)
    
    def __add__(self, elem):
        elem = self._to_elem(elem)
        return self._add(elem)
    
    def __sub__(self, elem):
        return self.__add__(elem)
    
    def __rsub__(self, elem):
        return self.__add__(elem)
    
    def __radd__(self, elem):
        return self.__add__(elem)
    
    def __mul__(self, elem):
        elem = self._to_elem(elem)
        return self._mul(elem)
    
    def _mul(self, p):
        return self.ring.add(self, p)    
    
    def __rmul__(self, elem):
        return self.__mul__(elem)
    
    def __div__(self, elem):
        elem = self._to_elem(elem)
        return self.ring.div(self, elem)
    
    def __divmod__(self, elem):
        elem = self._to_elem(elem)
        return self.ring.divmod(self, elem)
    
    def __mod__(self, elem):
        elem = self._to_elem(elem)
        return self.ring.rem(self, elem)
    
    def __pow__(self, k):
        return self.ring.pow(self, k)
    
    def __ne__(self, elem):
        return not self.__eq__(elem)


class GF2kPoly(Char2FieldPoly):
    
    def __init__(self, ring, coeffs):
        Char2FieldPoly.__init__(self, ring)
        coeffs = filter(lambda (k,d): k != 0, coeffs)
        self.coeffs = coeffs
        self.coeff = coeffs[0][0] if coeffs else 0
        self.deg = coeffs[0][1] if coeffs else -1
        
    def _to_elem(self, elem):
        if isinstance(elem, (int,long)):
            elem %= 2
        if isinstance(elem, (int,long,GF2Poly)):
            elem = self.ring.element(elem)
        elif not isinstance(elem, GF2kPoly):
            raise Exception 
        return elem
        
    def clone(self):
        coeffs = copy.copy(self.coeffs)
        return GF2kPoly(self.ring, coeffs)
    
    def to_monic(self):
        if not self.coeffs or self.coeffs[0][0] == 1:
            return self.clone()
        k = self.coeffs[0][0]
        return self * k.invert()
    
    def _add(self, p):
        if isinstance(p, GF2Poly) and p.ring == self.ring.GF2k:
            if self.coeffs and self.coeffs[-1][1] == 0:
                coeffs = self.coeffs[:-1] + [(p+self.coeffs[-1][0], 0)]
            else:
                coeffs = self.coeffs[::] + [(p,0)]
            return GF2kPoly(self.ring, coeffs)
        elif isinstance(p, GF2Poly) and p.ring != self.ring.GF2k:
            raise Exception
        i = j = 0
        coeffs = list()
        while i < len(self.coeffs) and j < len(p.coeffs):
            if self.coeffs[i][1] == p.coeffs[j][1]:
                k = self.coeffs[i][0] + p.coeffs[j][0]
                d = self.coeffs[i][1]
                i += 1
                j += 1
            elif self.coeffs[i][1] > p.coeffs[j][1]:
                k = self.coeffs[i][0]
                d = self.coeffs[i][1]
                i += 1
            else:
                k = p.coeffs[j][0]
                d = p.coeffs[j][1]
                j += 1
            coeffs.append((k,d))
        while i < len(self.coeffs):
            coeffs.append(self.coeffs[i])
            i += 1
        while j < len(p.coeffs):
            coeffs.append(p.coeffs[j])
            j += 1 
        return GF2kPoly(self.ring, coeffs)
    
    def _mul(self, p):
        if isinstance(p, (int,long)) or\
           isinstance(p, GF2Poly) and p.ring == self.ring.GF2k:
            coeffs = map(lambda (k,d): (k*p, d), self.coeffs)
            return GF2kPoly(self.ring, coeffs)
        elif isinstance(p, GF2Poly) and p.ring != self.ring.GF2k:
            raise Exception
        else:
            return Char2FieldPoly._mul(self, p)
        
    def __call__(self, x):
        return reduce(lambda value, (k,d): value + k*x**d,
                      self.coeffs,
                      0)
    
    def __eq__(self, elem):
        if elem == 0:
            return len(self.coeffs) == 0
        if elem == 1:
            return len(self.coeffs) == 1 and\
                   self.coeffs[0][1] == 0 and\
                   self.coeffs[0][0] == 1
        return self.coeffs == elem.coeffs
    
    def __hash__(self):
        return hash(tuple(self.coeffs)) ^ id(self)
    
    def __repr__(self):
        if self == 0:
            return '0'
        str_list = list()
        for k,d in self.coeffs:
            str_k = '[%s]' % str(k).replace('X','Z') if k != 1 else str()
            if d > 1:
                str_elem = '%sX^%d' % (str_k, d)
            elif d == 1:
                str_elem = '%sX' % str_k
            else:
                str_elem = str_k if k != 1 else '[1]'
            str_list.append(str_elem)
        return ' + '.join(str_list)


class GF2Poly(Char2FieldPoly):
    
    def __init__(self, ring, n, deg=None):
        Char2FieldPoly.__init__(self, ring)
        self.n = n
        self.deg = deg or self.ring._get_deg(n)
        self.coeff = 1 if self.deg >= 0 else 0
        
    def _to_elem(self, elem):
        if isinstance(elem, (int,long)):
            elem %= 2
        if isinstance(elem, (int,long)):
            elem = self.ring.element(elem)
        return elem        
        
    def clone(self):
        return GF2Poly(self.ring, self.n, self.deg)
    
    def to_monic(self):
        return self.clone()
    
    def to_bit_vector(self):
        return BitVector._new(self.ring.k, self.n)
    
    def invert(self):
        return self.ring.invert(self)    
        
    def _add(self, p):
        return self.ring.element(self.n ^ p.n)
    
    def _mul(self, p):
        if isinstance(p, GF2kPoly):
            return p.__mul__(self)
        return Char2FieldPoly._mul(self, p)
    
    def __call__(self, x):
        n = self.n >> 1
        result = 1 if (self.n & 1) else 0
        while n > 0:
            if n & 1:
                result ^= x
            n >>= 1
        return result    
    
    def __eq__(self, elem):
        if elem == 0:
            return self.n == 0
        if elem == 1:
            return self.n == 1
        return self.n == elem.n
    
    def __hash__(self):
        return hash(self.n) ^ id(self)
    
    def __repr__(self):
        if self.n == 0:
            return '0'
        xs = list()
        n = self.n
        i = 0
        while n > 0:
            if n & 1:
                if i == 0:
                    x = '1'
                elif i == 1:
                    x = 'X'
                else:
                    x = 'X^%d' % i
                xs.append(x)
            i += 1
            n >>= 1
        return ' + '.join(xs[::-1])