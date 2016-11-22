from common.attacks.rsa.oracle import RSAOracleAttack, RSAOracle
from common.challenge import CryptoChallenge
from common.ciphers.pubkey.rsa import RSA
from common.tools.base64 import Base64Decoder


class RSAParityOracleDecrypter(RSAOracleAttack):
    
    def _decrypt(self, int_ciphertext):
        # Invariant: the plaintext is in the interval
        # [lower_limit, upper_limit]
        lower_limit = 0
        upper_limit = self.n-1
        # two_i equals 2**i for i = 1,...,ceil(log_2 int_ciphertext)
        two_i = 2
        
        while lower_limit < upper_limit:
            mid = (lower_limit+upper_limit)/2
            mid_ciphertext = self._build_ciphertext_from_plaintexts(mid,
                                                                    two_i) 
            target_ciphertext = self._build_ciphertext_from(int_ciphertext,
                                                            two_i)
            if self.oracle.is_plaintext_even(target_ciphertext):
                upper_limit = mid
                # Adjust new upper limit if it violates the invariant.
                if not self.oracle.is_plaintext_even(mid_ciphertext):
                    upper_limit -= 1
            else:
                lower_limit = mid
                # Same as before.
                if self.oracle.is_plaintext_even(mid_ciphertext):
                    lower_limit += 1
            two_i *= 2
            
        return lower_limit


class RSAParityOracle(RSAOracle):
    
    def is_plaintext_even(self, ciphertext):
        int_plaintext = self.rsa.int_decrypt(ciphertext)
        return int_plaintext % 2 == 0


class Set6Challenge46(CryptoChallenge):
    
    STRING = 'VGhhdCdzIHdoeSBJIGZvdW5kIHlvdSBkb24ndCBwbGF5IGFyb3VuZCB3aXRo'+\
             'IHRoZSBGdW5reSBDb2xkIE1lZGluYQ=='

    def __init__(self):
        CryptoChallenge.__init__(self)
        self.plaintext = Base64Decoder().decode(self.STRING)

    def expected_value(self):
        return self.plaintext

    def value(self):
        rsa = RSA(bits=1024)
        oracle = RSAParityOracle(rsa)
        ciphertext = rsa.encrypt(self.plaintext)
        return RSAParityOracleDecrypter(oracle).decrypt(ciphertext)