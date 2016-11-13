from common.attacks.hash.nostradamus import NostradamusAttack
from common.challenge import CryptoChallenge
from common.hash.md import MDHashFunction
from common.hash.tools.build import BasicHashFunctionFactory
from common.tools.misc import RandomByteGenerator


class Set7Challenge54(CryptoChallenge):
    
    LENGTH = 50
    BLOCK_SIZE = MDHashFunction.block_size()
    PREFIX = RandomByteGenerator().value(LENGTH*BLOCK_SIZE)
    PREDICTION_LENGTH = 150*BLOCK_SIZE
    
    def validate(self):
        hash_function = BasicHashFunctionFactory.build(16)
        attack = NostradamusAttack(hash_function, self.PREDICTION_LENGTH, k=5)
        prediction = attack.prediction()
        message = attack.for_prefix(self.PREFIX)
        return message.startswith(self.PREFIX) and\
               hash_function().hash(message) == prediction