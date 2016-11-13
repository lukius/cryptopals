from common.challenge import CryptoChallenge
from common.ciphers.pubkey.rsa import RSA


class Set5Challenge39(CryptoChallenge):
    
    PLAINTEXT = 'Vos tambien la tenes adentro.'
    
    def expected_value(self):
        return self.PLAINTEXT
    
    def value(self):
        rsa = RSA()
        ciphertext = rsa.encrypt(self.PLAINTEXT)
        return rsa.decrypt(ciphertext)