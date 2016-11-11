from common.challenge import MatasanoChallenge
from common.ciphers.pubkey.rsa import FixedERSA
from common.math.crt import ChineseRemainderTheorem
from common.math.root import NthRoot
from common.tools.converters import IntToBytes


class RSABroadcastAttack(object):
    
    def __init__(self, public_keys):
        self.moduli = map(lambda pubkey: pubkey[1], public_keys)
        self.n = len(self.moduli)
        
    def decrypt(self, ciphertexts):
        crt_result = ChineseRemainderTheorem().solve(ciphertexts, self.moduli)
        nth_root = NthRoot(self.n).value(crt_result)
        return IntToBytes(nth_root).value()


class Set5Challenge40(MatasanoChallenge):
    
    PLAINTEXT = 'Vos tambien la tenes adentro.'
    E = 3
    
    def expected_value(self):
        return self.PLAINTEXT
    
    def value(self):
        rsa_instances = [FixedERSA(e=self.E) for _ in range(self.E)]
        ciphertexts = map(lambda rsa: rsa.int_encrypt(self.PLAINTEXT),
                          rsa_instances)
        public_keys = map(lambda rsa: rsa.get_public_key(), rsa_instances)
        attack = RSABroadcastAttack(public_keys)
        return attack.decrypt(ciphertexts)