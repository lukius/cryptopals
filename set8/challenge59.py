from common.challenge import CryptoChallenge
from common.math.ecc import EllipticCurve


class Set8Challenge59(CryptoChallenge):

    # Elliptic curve y^2 = x^3 + ax + b
    #  * Over Z_p
    #  * #E(Z_p) = o.
    #  * Also, point G on E(Z_p) has order d. 
    a = -95051
    b = 11279326    
    p = 233970423115425145524320034830162017933
    G = (182, 85518893674295321206118380980485522083)
    d = 29246302889428143187362802287225875743
    o = 233970423115425145498902418297807005944
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        
    def _validate(self):
        # 1. Check elliptic curve implementation.
        curve = EllipticCurve(self.a, self.b, self.p)
        G = curve.point(*self.G)
        self._assert_equals(curve.identity(), self.d * G)
    
    