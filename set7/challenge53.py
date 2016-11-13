from common.attacks.hash.preimage import SecondPreimageAttack
from common.challenge import CryptoChallenge
from common.hash.tools.build import BasicHashFunctionFactory


class Set7Challenge53(CryptoChallenge):
    
    K = 5
    BLOCK = 'LTA!'*16
    MESSAGE = BLOCK*(K + 1 + 2**K)
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        # Use a rather artificial hash function in order to make the
        # challenge run faster. In theory, any MD hash function could
        # be targeted.
        self.hash_function = BasicHashFunctionFactory.build(24)
    
    def expected_value(self):
        return self.hash_function().hash(self.MESSAGE)
    
    def value(self):
        preimage = SecondPreimageAttack(self.hash_function).value(self.MESSAGE,
                                                                  self.K)
        if preimage == self.MESSAGE:
            # Won't happen, but fail if the preimage found is the same message.
            return None
        return self.hash_function().hash(preimage)