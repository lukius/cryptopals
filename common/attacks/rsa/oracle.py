from common.math.modexp import ModularExp
from common.tools.converters import BytesToInt, IntToBytes


class RSAOracleAttack(object):
    
    def __init__(self, oracle):
        self.oracle = oracle
        self.e, self.n = oracle.get_public_key()
        
    def _encrypt(self, m):
        return ModularExp(self.n).value(m, self.e)
    
    def _multiply(self, a, b):
        return (a*b) % self.n
    
    def _build_ciphertext_from_plaintexts(self, m1, m2):
        c1 = self._encrypt(m1)
        c2 = self._encrypt(m2)
        return self._multiply(c1, c2)
        
    def _build_ciphertext_from(self, c, m):
        m_encrypted = self._encrypt(m)
        return self._multiply(c, m_encrypted)
        
    def decrypt(self, ciphertext):
        int_ciphertext = BytesToInt(ciphertext).value()
        int_plaintext = self._decrypt(int_ciphertext)
        return IntToBytes(int_plaintext).value()
    
    def _decrypt(self, int_ciphertext):
        raise NotImplementedError
    
    
class RSAOracle(object):
    
    def __init__(self, rsa):
        self.rsa = rsa
        
    def get_public_key(self):
        return self.rsa.get_public_key()    