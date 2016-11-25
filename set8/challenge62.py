from fractions import Fraction

from common.attacks.signature.ecdsa import BiasedNonceECDSAKeyRecoveryAttack
from common.challenge   import CryptoChallenge
from common.math.linalg import Vector, BasisOrthogonalizer,\
                               LatticeBasisReduction
from common.signature.dsa import ECDSA

from misc import Set8EllipticCurve


class BiasedNonceECDSA(ECDSA):
    
    N_SHIFT = 8
    
    def _get_nonce(self):
        k = ECDSA._get_nonce(self)
        return (k >> self.N_SHIFT) << self.N_SHIFT


class Set8Challenge62(CryptoChallenge):
    
    BASIS         = [Vector([-2,             0,  2,              0]),
                     Vector([Fraction(1,2),  -1,  0,             0]),
                     Vector([-1,              0, -2, Fraction(1,2)]),
                     Vector([-1,              1,  1,             2])]
    
    REDUCED_BASIS = [Vector([Fraction(1,2),  -1,  0,             0]),
                     Vector([-1,              0, -2, Fraction(1,2)]),
                     Vector([Fraction(-1,2),  0,  1,             2]),
                     Vector([Fraction(-3,2), -1,  2,             0])] 
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.ecdsa = BiasedNonceECDSA(parameters=Set8EllipticCurve.ECDSA_params())
    
    def _test_orthogonalization(self):
        Q = BasisOrthogonalizer().orthogonalize(self.BASIS)
        for i,v in enumerate(Q):
            for u in Q[i+1:]:
                # Dot product should be zero.
                self._assert_equals(0, u*v)
    
    def _test_LLL(self):
        reduced_basis = LatticeBasisReduction().reduce(self.BASIS)
        self._assert_equals(self.REDUCED_BASIS, reduced_basis)
        
    def _test_key_recovery(self):
        attack = BiasedNonceECDSAKeyRecoveryAttack(self.ecdsa,
                                                   BiasedNonceECDSA.N_SHIFT)
        key = self.ecdsa.x
        key_recovered = attack.recover_key()
        self._assert_equals(key, key_recovered)
    
    def _validate(self):
        # 1. Test basis orthogonalization.
        self._test_orthogonalization()
        
        # 2. Test LLL algorithm.
        self._test_LLL()
        
        # 3. Recover ECDSA private key on biased nonces.
        self._test_key_recovery()