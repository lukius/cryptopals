from common.attacks.rsa.pkcs1_5 import PKCS1_5PaddingOracleAttack,\
                                   PKCS1_5PaddingOracle
from common.challenge import CryptoChallenge
from common.ciphers.pubkey.rsa import RSA
from common.tools.misc import ByteSize
from common.tools.padders import PKCS1_5Padder


class Set6Challenge48(CryptoChallenge):
    
    STRING = 'Pochoclin!'
    RSA_BITS = 768
    
    def expected_value(self):
        return self.STRING
    
    def _decrypt(self, ciphertext, oracle):
        # See comment on Set6Challenge7. 
        try:
            plaintext = PKCS1_5PaddingOracleAttack(oracle).decrypt(ciphertext)
        except Exception:
            plaintext = None
        return plaintext    

    def value(self):
        rsa = RSA(bits=self.RSA_BITS)
        oracle = PKCS1_5PaddingOracle(rsa)
        byte_size = ByteSize(rsa.n).value()
        padded_string = PKCS1_5Padder(self.STRING).value(size=byte_size)
        ciphertext = rsa.encrypt(padded_string)
        return self._decrypt(ciphertext, oracle)
