import random

from common.math.group import AbstractGroup


class GF2(AbstractGroup):
    
    def __init__(self, k, mod_str):
        AbstractGroup.__init__(self)
        self.k = k
        self.mod, self.mod_deg = self._parse_poly(mod_str)
        
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
        
    def rand_element(self):
        n = random.randint(0, 2**self.k - 1)
        return GF2kElement(self, n)

    def element(self, obj):
        if isinstance(obj, (int,long)):
            n = obj
            deg = None
            if n < 0 or n >= 2**self.k:
                raise Exception('bad GF(2^%d) element format.' % self.k)
            
        elif isinstance(obj, basestring):
            n, deg = self._parse_poly(obj)
            
        return GF2kElement(self, n, deg)
    
    def add(self, a, b):
        # Is actually 'mul', but this implements the abstract group interface.
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

            if b_deg == self.mod_deg:
                b_n ^= self.mod
                b_deg = self._get_deg(b_n)

        return GF2kElement(self, p_n)
    
    def div_rem(self, a, b):
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

        q = GF2kElement(self, q_n)
        r = GF2kElement(self, r_n, r_deg)
        
        return q, r
    
    def div(self, a, b):
        return self.div_rem(a, b)[0]        
    
    def invert(self, a):
        return self.pow(a, 2**self.k - 2)
    
    def identity(self):
        return self.element(1)
    
    def __repr__(self):
        return 'GF(2^%d)' % self.k
    

class GF2kElement(object):
    
    def __init__(self, field, n, deg=None):
        self.field = field
        self.n = n
        self.deg = deg or self.field._get_deg(n)
        
    def degree(self):
        return self.deg
        
    def __add__(self, elem):
        if isinstance(elem, int) and elem in [0,1]:
            elem = self.field.element(elem)
        return self.field.element(self.n ^ elem.n)

    def __sub__(self, elem):
        return self.__add__(elem)
    
    def __rsub__(self, elem):
        return self.__add__(elem)
    
    def __radd__(self, elem):
        return self.__add__(elem)
    
    def __mul__(self, elem):
        if isinstance(elem, int) and elem in [0,1]:
            elem = self.field.element(elem)
        return self.field.add(self, elem)
    
    def __rmul__(self, elem):
        return self.__mul__(elem)
    
    def __div__(self, elem):
        return self.field.div(self, elem)
    
    def __pow__(self, k):
        return self.field.pow(self, k)
    
    def invert(self):
        return self.field.invert(self)
    
    def __eq__(self, elem):
        if elem == 0:
            return self.n == 0
        if elem == 1:
            return self.n == 1
        return self.n == elem.n
    
    def __ne__(self, elem):
        return not self.__eq__(elem)
    
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