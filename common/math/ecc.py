import math
import random

from common.math.structures import AbstractGroup
from common.math.invmod import ModularInverse
from common.math.root import ModularSquareRoot
from common.math.modexp import ModularExp
    

class EllipticCurve(AbstractGroup):
    
    def __init__(self, p):
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
        if not self._point_in_curve(x,y):
            raise Exception('point (%g,%g) not in curve!' % (x,y))
        return self._point(x,y)
    
    def identity(self):
        return self.O
    
    def invert(self, P):
        if P == self.O:
            return P
        return self.point(P.x, self.p - P.y)
    
    def rand_point(self):
        while True:
            x = random.randint(0, self.p-1)
            y = self.y_from_x(x)
            if y is not None:
                break
        return self.point(x,y)
    
    def y_from_x(self, x):
        y_sq = self.y_sq_from_x(x)
        return ModularSquareRoot(self.p).value(y_sq)
    
    def y_sq_from_x(self, x):
        raise NotImplementedError

    def add(self, P, Q):
        raise NotImplementedError
    
    def _point_in_curve(self, x, y):
        raise NotImplementedError
    
    
    def __repr__(self):
        raise NotImplementedError
    
    
class WeierstrassEllipticCurve(EllipticCurve):
    
    def __init__(self, a, b, p):
        EllipticCurve.__init__(self, p)
        self.a = a
        self.b = b
    
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

        return self._point(x, y)
    
    def y_sq_from_x(self, x):
        return (x*x*x + self.a*x  + self.b) % self.p

    def _point_in_curve(self, x, y):
        return (y*y) % self.p == (x*x*x + self.a*x  + self.b) % self.p
    
    def __repr__(self):
        return 'E(GF(%d)) : y^2 = x^3 + %d * x + %d' % (self.p, self.a, self.b)
    
    
class MontgomeryEllipticCurve(EllipticCurve):

    def __init__(self, A, B, p):
        EllipticCurve.__init__(self, p)
        self.A = A
        self.B = B
        self.modinv = ModularInverse(self.p)
        self.B_inv = self.modinv.value(self.B)
    
    def add(self, P, Q):
        if P == self.O:
            return Q
        if Q == self.O:
            return P
        if P == self.invert(Q):
            return self.O
              
        x1, y1 = P.x, P.y
        x2, y2 = Q.x, Q.y

        if P == Q:
            l_d = self.modinv.value((2*self.B*y1) % self.p)   
            l_n = (3*x1*x1 + 2*self.A*x1 + 1) % self.p
            l = (l_n * l_d) % self.p
            
            x3 = (self.B*l*l - self.A - 2*x1) % self.p
            y3 = ((3*x1 + self.A)*l - self.B*l*l*l - y1) % self.p
        else:
            r = (self.B * (x2*y1 - x1*y2)**2) % self.p
            s = self.modinv.value(x1*x2*(x2-x1)**2) 
    
            x3 = (r*s) % self.p
            
            u1 = ((2*x1 + x2 + self.A)*(y2 - y1)) % self.p
            v1 = self.modinv.value((x2 - x1) % self.p)
            
            u2 = self.B*(y2 - y1)**3
            v2 = self.modinv.value(((x2 - x1)**3) % self.p)
            
            y3 = ((u1*v1) - (u2*v2) - y1) % self.p
        
        return self._point(x3, y3) 
    
    def ladder(self, a, n):
        # Single-coordinate ladder to compute scalar multiplication.
        u2, w2 = (1, 0)
        u3, w3 = (a, 1)
        bitsize = int(math.ceil(math.log(self.p+1, 2)))
        for i in xrange(bitsize-1, -1, -1):
            b = 1 & (n >> i)
            
            u2, u3 = self._swap(u2, u3, b)
            w2, w3 = self._swap(w2, w3, b)
            
            v1 = ((u2*u3 - w2*w3)**2) % self.p
            v2 = (a * (u2*w3 - w2*u3)**2) % self.p
            u3, w3 = v1, v2
            
            v1 = ((u2*u2 - w2*w2)**2) % self.p
            v2 = (4*u2*w2 * (u2*u2 + self.A*u2*w2 + w2*w2)) % self.p
            u2, w2 = v1, v2
            
            u2, u3 = self._swap(u2, u3, b)
            w2, w3 = self._swap(w2, w3, b)
        return (u2 * ModularExp(self.p).value(w2, self.p-2)) % self.p
    
    def _swap(self, a, b, f):
        return f * (b,a) + (1-f) * (a,b)
    
    def to_weierstrass(self):
        # Compute the isomorphic curve in Weierstrass form.
        den_a = self.modinv.value((3*self.B*self.B) % self.p)
        a = ((3 - self.A*self.A) * den_a) % self.p
        
        den_b = self.modinv.value((27*self.B*self.B*self.B) % self.p)
        b = ((2*self.A*self.A*self.A - 9*self.A) * den_b) % self.p
        
        return WeierstrassEllipticCurve(a, b, self.p)
    
    def weierstrass_coords(self, *args):
        # Express a given point in this curve in Weierstrass coordinates.
        x, y = self._point_read(*args)
        t = self.modinv.value(3)
        x_w = (self.B_inv * (x + self.A * t)) % self.p
        y_w = (y * self.B_inv) % self.p
        return (x_w, y_w)
    
    def y_sq_from_x(self, x):
        B_y_sq = (x*x*x + self.A*x*x  + x) % self.p
        return (self.B_inv * B_y_sq) % self.p

    def _point_in_curve(self, x, y):
        return (self.B*y*y) % self.p ==\
               (x*x*x + self.A*x*x  + x) % self.p
    
    def __repr__(self):
        return 'E(GF(%d)) : %d * y^2 = x^3 + %d * x^2 + x' %\
               (self.p, self.B, self.A)
    
    
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