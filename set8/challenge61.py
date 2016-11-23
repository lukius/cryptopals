from common.attacks.rsa.key_duplication import RSASignatureKeySelectionAttack,\
                                               RSAKeyDuplicationAttack
from common.attacks.signature.ecdsa import ECDSAKeySelectionAttack
from common.challenge import CryptoChallenge
from common.signature.dsa import ECDSA
from common.ciphers.pubkey.rsa import RSA
from common.math.modexp import ModularExp
from common.signature.rsa import RSADigitalSignature

from misc import Set8EllipticCurve


class ECDSAValidator(ECDSA):
    
    def verify_using(self, message, signature, new_key, new_g):
        real_key, self.y = self.y, new_key
        real_g, self.g = self.g, new_g
         
        outcome = self.verify(message, signature)
        
        self.y = real_key
        self.g = real_g
        
        return outcome
    

class RSASignatureValidator(RSADigitalSignature):
    
    def _RSA(self):
        # Can be increased, but Pohlig-Hellman might take a while to crack the
        # discrete logs (fortunately the prime generation phase is quick).
        return RSA(bits=200)
    
    def verify_using(self, message, signature, new_key):
        real_rsa = self.rsa
        
        e, N = new_key     
        rsa = RSA()
        rsa.modexp = ModularExp(N)
        rsa.e = e
        rsa.n = N
        rsa.public_key = (e, N)   
        self.rsa = rsa
         
        outcome = self.verify(message, signature)
        
        self.rsa = real_rsa         
        
        return outcome
    
    
class Set8Challenge61(CryptoChallenge):
    
    message = 'estamos en la B.'
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.ecdsa = ECDSAValidator(parameters=Set8EllipticCurve.ECDSA_params())
        self.rsa = RSASignatureValidator()
        
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
        
    def _test_rsa_signature_key_selection_attack(self):
        signature = self.rsa.sign(self.message)
        attack = RSASignatureKeySelectionAttack(self.rsa)
        
        e, N, _ = attack.generate_key(self.message, signature)
        fake_key = (e, N)

        self._assert_not_equals(fake_key, self.rsa.get_public_key())
        self._assert_true(self.rsa.verify_using(self.message, signature,
                                                fake_key))
        
    def _test_rsa_decryption_to_chosen_plaintext(self):
        rsa = RSA(bits=200)
        
        attack = RSAKeyDuplicationAttack(rsa)

        ciphertext = rsa.encrypt(self.message)
        chosen_plaintext = 'Pobre RiBer.'
        new_rsa = attack.duplicate(chosen_plaintext, ciphertext)
        
        self._assert_equals(chosen_plaintext, new_rsa.decrypt(ciphertext))
        
    def _validate(self):
        # 1. Validate basic ECDSA signing and verification.
        self._test_ecdsa()
        
        # 2. Perform ECDSA key selection attack.
        self._test_ecdsa_key_selection_attack()
        
        # 3. Perform RSA signature key selection attack.
        self._test_rsa_signature_key_selection_attack()
        
        # 4. Choose RSA key to decrypt a ciphertext to a given message.
        self._test_rsa_decryption_to_chosen_plaintext()