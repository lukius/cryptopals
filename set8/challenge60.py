from common.attacks.ecc import InsecureTwistAttack
from common.challenge import CryptoChallenge
from common.key_exchange.diffie_hellman import MontgomeryCurveDiffieHellman
from common.math.ecc import MontgomeryEllipticCurve


def montgomery_coords(P):
    # Hardcoded for the curve used in this challenge!
    return (P.x - 178, P.y)
    
    
class CustomInsecureTwistAttack(InsecureTwistAttack):

    def __init__(self, target, curve, order, G, G_order):
        InsecureTwistAttack.__init__(self, curve, order, G, G_order)
        self.target = target
        
    def _target_public_key(self):
        return self.target.get_public_key()

    def _key_is_valid(self, trial_key, x):    
        return trial_key == self.target.get_secret_from(x)    
    

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
    o = 233970423115425145498902418297807005944
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.m_curve = MontgomeryEllipticCurve(self.A, self.B, self.p)
        self.curve = self.m_curve.to_weierstrass()
        self.m_G = self.m_curve.point(self.g)
        self.bob = MontgomeryCurveDiffieHellman(curve=self.m_curve,
                                                g=self.m_G,
                                                g_order=self.d)
        
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
        m_G_x = self.m_G.x
        self._assert_equals(0, self.m_curve.ladder(m_G_x, self.d))
    
        # Convert random point back and forth from Weierstrass curve.
        P = self.curve.rand_point()
        m_P = self.m_curve.point(montgomery_coords(P))
        P10 = P * 10
        m_P10 = self.m_curve.point(montgomery_coords(P10))

        self._assert_equals(m_P10.x, self.m_curve.ladder(m_P.x, 10))
        
        # Check that ladder's output equals x coordinate of standard power.
        m_Q = 25 * m_P
        x = self.m_curve.ladder(m_P.x, 25)
        
        self._assert_equals(m_Q.x, x)
    
    def _validate(self):
        # 1. Check Montgomery EC implementation.
        self._test_montgomery_curve()
        
        # 2. Check single-coordinate ladder.
        self._test_ladder()
        
        # 3. Recover key through the quadratic twist of the curve.
        attack = CustomInsecureTwistAttack(target=self.bob, curve=self.m_curve,
                                           order=self.o, G=self.m_G, G_order=self.d)
        key_recovered = attack.recover_key()
        self._assert_equals(self.bob.exp, key_recovered)        