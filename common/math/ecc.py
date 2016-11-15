import random

from common.math.group import AbstractGroup
from common.math.invmod import ModularInverse
from common.math.root import ModularSquareRoot
    

class EllipticCurve(AbstractGroup):
    
    def __init__(self, a, b, p):
        self.a = a
        self.b = b
        self.p = p
        self.O = EllipticCurveIdentity(self)
        
    def point(self, *args):
        x, y = self._point_read(*args)
        return self._point(x, y)
    
    def point_safe(self, *args):
        x, y = self._point_read(*args)
        return self._point_safe(x, y)    
        
    def _point_read(self, *args):
        if len(args) == 1 and isinstance(args[0], EllipticCurvePointBase):
            x, y = args[0].x, args[0].y
        elif len(args) == 1 and isinstance(args[0], tuple):
            x, y = args[0]
        elif len(args) > 1:
            x, y = args[0], args[1]
        return x, y
            
    def _point(self, x, y):
        return EllipticCurvePoint(self, x % self.p, y % self.p)
    
    def _point_safe(self, x, y):
        if (y*y) % self.p != (x*x*x + self.a*x  + self.b) % self.p:
            raise Exception('point (%g,%g) not in curve!' % (x,y))
        return self._point(x,y)
    
    def identity(self):
        return self.O
    
    def add(self, P, Q):
        if P == self.O:
            return Q
        if Q == self.O:
            return P
        if P == self.invert(Q):
            return self.O
        
        if P == Q:
            s = ModularInverse(self.p).value(2*P.y)
            m = ((3*P.x**2 + self.a) * s) % self.p
        else:
            s = ModularInverse(self.p).value(Q.x - P.x)
            m = ((Q.y - P.y) * s) % self.p

        x = m*m - P.x - Q.x
        y = m*(P.x - x) - P.y

        return self.point(x, y)        
    
    def invert(self, P):
        if P == self.O:
            return P
        return self.point(P.x, self.p - P.y)
    
    def rand_point(self):
        while True:
            x = random.randint(0, self.p-1)
            y_sq = (x*x*x + self.a*x  + self.b) % self.p
            y = ModularSquareRoot(self.p).value(y_sq)
            if y is not None:
                break
        return self.point(x,y)
    
    def __repr__(self):
        return 'E(GF(%d)) : y^2 = x^3 + %d * x + %d' % (self.p, self.a, self.b)
    
    
class EllipticCurvePointBase(object):
    
    def __init__(self, curve):
        self.curve = curve
    
    def __add__(self, P):
        return self.curve.add(self, P)
    
    def __mul__(self, n):
        return self.curve.pow(self, n)
    
    def __rmul__(self, n):
        return self.__mul__(n)
    
    def invert(self):
        return self.curve.invert(self)
    
    def __eq__(self, P):
        raise NotImplementedError
    
    def __ne__(self, P):
        return not self.__eq__(P)


class EllipticCurvePoint(EllipticCurvePointBase):
    
    def __init__(self, curve, x, y):
        EllipticCurvePointBase.__init__(self, curve)
        self.x = x
        self.y = y
        
    def __eq__(self, P):
        return P._eq_point(self)
    
    def _eq_point(self, P):
        return self.x == P.x and self.y == P.y
    
    def _eq_id(self, O):
        return False
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __repr__(self):
        return '(%d, %d)' % (self.x, self.y)


class EllipticCurveIdentity(EllipticCurvePointBase):
    
    def __eq__(self, P):
        return P._eq_id(self)
    
    def _eq_point(self, P):
        return False
    
    def _eq_id(self, O):
        return True    
    
    def __repr__(self):
        return 'O'