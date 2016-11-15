import random

from common.math.modexp import ModularExp


class AbstractDiffieHellman(object):
    
    def __init__(self, g, g_order):
        self.g = g
        self.exp = self._choose_secret_exponent(g_order)
        self.public_key = self._compute_public_key()
        
    def _choose_secret_exponent(self, g_order):
        return random.randint(1, g_order-1)
        
    def get_public_key(self):
        return self.public_key

    def _compute_public_key(self):
        raise NotImplementedError
    
    def get_secret_from(self, key):
        raise NotImplementedError


class DiffieHellman(AbstractDiffieHellman):
    
    def __init__(self, p, g, g_order=None):
        self.p = p
        self.modexp = ModularExp(self.p)
        AbstractDiffieHellman.__init__(self, g, g_order=g_order or p)
        
    def _compute_public_key(self):
        return self.modexp.value(self.g, self.exp)

    def get_secret_from(self, key):
        return self.modexp.value(key, self.exp)


class EllipticCurveDiffieHellman(AbstractDiffieHellman):
    
    def __init__(self, curve, g, g_order):
        self.curve = curve
        g = self._new_point(g)
        AbstractDiffieHellman.__init__(self, g, g_order)
        
    def _new_point(self, P):
        return self.curve.point_safe(P)
        
    def _compute_public_key(self):
        return self.exp * self.g

    def get_secret_from(self, key):
        return self.exp * self._new_point(key)
    
    
class UnsafeEllipticCurveDiffieHellman(EllipticCurveDiffieHellman):
    
    # Unsafe variant of ECDH that does not check whether the point
    # submitted as the peer public key is a valid curve point.
    
    def _new_point(self, P):
        return self.curve.point(P)  