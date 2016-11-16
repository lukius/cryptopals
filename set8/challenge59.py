from common.challenge import CryptoChallenge
from common.math.ecc import WeierstrassEllipticCurve
from common.key_exchange.diffie_hellman import EllipticCurveDiffieHellman,\
                                               UnsafeEllipticCurveDiffieHellman
from common.attacks.ecc import InvalidCurveAttack


class CustomInvalidCurveAttack(InvalidCurveAttack):

    def __init__(self, curve, target, order):
        InvalidCurveAttack.__init__(self, curve, order)
        self.target = target

    def _key_is_valid(self, trial_key, P):    
        return trial_key == self.target.get_secret_from(P)


class Set8Challenge59(CryptoChallenge):

    # Elliptic curve y^2 = x^3 + ax + b
    #  * Over Z_p
    #  * #E(Z_p) = o.
    #  * Also, point g on E(Z_p) has order d. 
    a = -95051
    b = 11279326    
    p = 233970423115425145524320034830162017933
    g = (182, 85518893674295321206118380980485522083)
    d = 29246302889428143187362802287225875743
    o = 233970423115425145498902418297807005944
    
    # Invalid curves and their orders.
    E1 = WeierstrassEllipticCurve(-95051, 210, p)
    o1 = 233970423115425145550826547352470124412
    
    E2 = WeierstrassEllipticCurve(-95051, 504, p)
    o2 = 233970423115425145544350131142039591210
    
    E3 = WeierstrassEllipticCurve(-95051, 727, p)
    o3 = 233970423115425145545378039958152057148
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.curve = WeierstrassEllipticCurve(self.a, self.b, self.p)
        self.G = self.curve.point(self.g)
        self.alice = EllipticCurveDiffieHellman(self.curve, g=self.G,
                                                g_order=self.d)
        self.bob = UnsafeEllipticCurveDiffieHellman(self.curve, g=self.G,
                                                    g_order=self.d)
        
    def _test_ec_diffie_hellman(self):
        alice_pub = self.alice.get_public_key()
        bob_pub = self.bob.get_public_key()
        
        alice_secret = self.alice.get_secret_from(bob_pub)
        bob_secret = self.bob.get_secret_from(alice_pub)

        self._assert_equals(alice_secret, bob_secret)
        
    def _validate(self):
        # 1. Check elliptic curve implementation.
        self._assert_equals(self.curve.identity(), self.d * self.G)
        P = self.curve.rand_point()
        self._assert_equals((P.y*P.y) % self.p,
                            (P.x**3 + self.a * P.x + self.b) % self.p)
        
        # 2. Check elliptic curve Diffie-Hellman.
        self._test_ec_diffie_hellman()
        
        # 3. Recover Bob's key with the invalid curve attack.
        attack = CustomInvalidCurveAttack(self.curve, self.bob, self.d)
        key_recovered = attack.recover_key([(self.E1, self.o1),
                                            (self.E2, self.o2), 
                                            (self.E3, self.o3)])[0]
        self._assert_equals(self.bob.exp, key_recovered)