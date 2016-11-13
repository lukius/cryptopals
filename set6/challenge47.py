from common.attacks.pkcs1_5 import PKCS1_5PaddingOracleAttack,\
                                   PKCS1_5PaddingOracle
from common.challenge import CryptoChallenge
from common.ciphers.pubkey.rsa import RSA
from common.tools.misc import ByteSize
from common.tools.padders import PKCS1_5Padder


class Set6Challenge47(CryptoChallenge):
    
    STRING = 'Pochoclin!'
    RSA_BITS = 256
    
    def expected_value(self):
        return self.STRING
    
    def _decrypt(self, ciphertext, oracle):
        # The attack might fail occasionally. I think it is due to how RSA
        # chooses its underlying prime factors of the modulus n: if the prime
        # number generator yields a non-prime number (it is probabilistic,
        # after all), then the computed totient will be nonsense and thus all
        # the math gets screwed. 
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
