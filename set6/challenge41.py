from common.challenge import CryptoChallenge
from common.ciphers.pubkey.rsa import RSA
from common.hash.sha1 import SHA1
from common.math.invmod import ModularInverse
from common.math.modexp import ModularExp
from common.tools.converters import BytesToInt, IntToBytes


class UnpaddedRSADecrypter(object):
    
    def __init__(self, one_time_rsa):
        self.one_time_rsa = one_time_rsa

    def decrypt(self, ciphertext):
        e, n = self.one_time_rsa.get_public_key()
        int_ciphertext = BytesToInt(ciphertext).value()
        # Choose any value s.t. it is coprime with n (since we need it to
        # be invertible mod n). Being n = pq, with p and q "big" primes,
        # choosing a small prime will do it.
        dummy_plaintext = 11
        modular_inverse = ModularInverse(n).value(dummy_plaintext)
        dummy_ciphertext = ModularExp(n).value(dummy_plaintext, e)
        new_ciphertext = (dummy_ciphertext*int_ciphertext) % n
        new_ciphertext = IntToBytes(new_ciphertext).value()
        obtained_plaintext = self.one_time_rsa.decrypt(new_ciphertext)
        integer = BytesToInt(obtained_plaintext).value()
        int_plaintext = (integer*modular_inverse) % n
        return IntToBytes(int_plaintext).value()
    

class OneTimeRSA(RSA):
    
    def __init__(self):
        RSA.__init__(self)
        self.hash_function = SHA1()
        self.hashes = set()
        
    def decrypt(self, ciphertext):
        ciphertext_hash = self.hash_function.hash(ciphertext)
        if ciphertext_hash in self.hashes:
            raise RuntimeError('ciphertext already decrypted')
        self.hashes.add(ciphertext_hash)
        return RSA.decrypt(self, ciphertext)


class Set6Challenge41(CryptoChallenge):

    PLAINTEXT = 'Vos tambien la tenes adentro.'
    
    def expected_value(self):
        return self.PLAINTEXT
    
    def value(self):
        one_time_rsa = OneTimeRSA()
        ciphertext = one_time_rsa.encrypt(self.PLAINTEXT)
        # Decrypt this ciphertext and ignore its output (so as to ensure that
        # we cannot cheat and decrypt it again after).
        one_time_rsa.decrypt(ciphertext)
        return UnpaddedRSADecrypter(one_time_rsa).decrypt(ciphertext)