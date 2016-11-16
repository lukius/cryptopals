from common.challenge import CryptoChallenge
from common.math.ecc import MontgomeryEllipticCurve


def montgomery_coords(P):
    # Hardcoded for the curve used in this challenge!
    return (P.x - 178, P.y)
    

class Set8Challenge60(CryptoChallenge):
    
    # Montgomery elliptic curve By^2 = x^3 + Ax^2 + x
    #  * Over Z_p
    #  * #E(Z_p) = o.
    #  * Point g on E(Z_p) has order d. 
    A = 534
    B = 1    
    p = 233970423115425145524320034830162017933
    g = (4, 85518893674295321206118380980485522083)
    d = 29246302889428143187362802287225875743    
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.m_curve = MontgomeryEllipticCurve(self.A, self.B, self.p)
        self.curve = self.m_curve.to_weierstrass()
        self.m_G = self.m_curve.point(self.g)
        
    def _test_montgomery_curve(self):
        P = self.curve.rand_point()
        Q = self.curve.rand_point()
        R = P + Q

        m_P = self.m_curve.point(montgomery_coords(P))
        m_Q = self.m_curve.point(montgomery_coords(Q))
        m_R = self.m_curve.point(montgomery_coords(R))
        
        self._assert_equals(m_R, m_P + m_Q)
        
        m_P = self.m_curve.rand_point()
        m_Q = self.m_curve.rand_point()
        m_R = m_P + m_Q
        
        P = self.curve.point(self.m_curve.weierstrass_coords(m_P))
        Q = self.curve.point(self.m_curve.weierstrass_coords(m_Q))
        R = self.curve.point(self.m_curve.weierstrass_coords(m_R))
        
        self._assert_equals(R, P + Q)
        
        inv_m_P = self.m_curve.invert(m_P)
        inv_P = self.curve.invert(P)
        m_inv_P = self.m_curve.point(montgomery_coords(inv_P))

        self._assert_equals(inv_m_P, m_inv_P)
        
    def _test_ladder(self):
        # Base point G should return 0 when multiplied by its order.
        self._assert_equals(0, self.d * self.m_G)
    
        P = self.curve.rand_point()
        m_P = self.m_curve.point(montgomery_coords(P))
        P10 = P * 10
        m_P10 = self.m_curve.point(montgomery_coords(P10))

        self._assert_equals(m_P10.x, m_P * 10)
    
    def _validate(self):
        # 1. Check Montgomery EC implementation.
        self._test_montgomery_curve()
        
        # 2. Check single-coordinate ladder.
        self._test_ladder()
        
        # 3. Recover key through the quadratic twist of the curve.
        # TBD