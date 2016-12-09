import copy

from common.math.linalg.bit import BitVector


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
    
    def pow_mod(self, a, n):
        return self.ring.pow_mod(self, a, n)
    
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
        from common.math.finite_field import GF2kElement
        if isinstance(elem, (int,long)):
            elem %= 2
        if isinstance(elem, (int,long,GF2kElement)):
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
        from common.math.finite_field import GF2kElement
        if isinstance(p, GF2kElement) and p.field == self.ring.GF2k:
            if self.coeffs and self.coeffs[-1][1] == 0:
                coeffs = self.coeffs[:-1] + [(p+self.coeffs[-1][0], 0)]
            else:
                coeffs = self.coeffs[::] + [(p,0)]
            return GF2kPoly(self.ring, coeffs)
        elif isinstance(p, GF2kElement) and p.field != self.ring.GF2k:
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
        from common.math.finite_field import GF2kElement
        if isinstance(p, (int,long)) or\
           isinstance(p, GF2kElement) and p.field == self.ring.GF2k:
            coeffs = map(lambda (k,d): (k*p, d), self.coeffs)
            return GF2kPoly(self.ring, coeffs)
        elif isinstance(p, GF2kElement) and p.field != self.ring.GF2k:
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