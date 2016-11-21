from common.challenge import CryptoChallenge
from common.math.ecc import WeierstrassEllipticCurve
from common.signature.dsa import ECDSA
from common.attacks.signature.ecdsa import ECDSAKeySelectionAttack


class ECDSAValidator(ECDSA):
    
    def verify_using(self, message, signature, new_key, new_g):
        real_key, self.y = self.y, new_key
        real_g, self.g = self.g, new_g
         
        outcome = self.verify(message, signature)
        
        self.y = real_key
        self.g = real_g
        
        return outcome
    
    
class Set8Challenge61(CryptoChallenge):
    
    p = 233970423115425145524320034830162017933
    curve = WeierstrassEllipticCurve(-95051, 210, p)
    G = curve.point(182, 85518893674295321206118380980485522083)
    d = 29246302889428143187362802287225875743
    
    message = 'estamos en la B.'
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.ecdsa = ECDSAValidator(parameters=(self.curve, self.d, self.G))
        
    def _test_ecdsa(self):
        signature = self.ecdsa.sign(self.message)
        self._assert_true(self.ecdsa.verify(self.message, signature))
        self._assert_false(self.ecdsa.verify(self.message + 'x', signature))
        signature = (signature[0]+1, signature[1])
        self._assert_false(self.ecdsa.verify(self.message, signature))
        
    def _test_ecdsa_key_selection_attack(self):
        signature = self.ecdsa.sign(self.message)
        attack = ECDSAKeySelectionAttack(self.ecdsa)

        fake_key, fake_G = attack.generate_key(self.message, signature)

        self._assert_not_equals(fake_key, self.ecdsa.get_public_key()[-1])
        self._assert_not_equals(fake_G, self.ecdsa.g)
        self._assert_true(self.ecdsa.verify_using(self.message, signature,
                                                  fake_key, fake_G))
        
    def _validate(self):
        # 1. Validate basic ECDSA signing and verification.
        self._test_ecdsa()
        
        # 2. Perform ECDSA key selection attack.
        self._test_ecdsa_key_selection_attack()
        
        # 3. Perform RSA signature key selection attack.
        # TBD