import random

from common.attacks.bitflipping import BitFlippingAttack,\
                                       UserProfileGenerator, UserProfileParser
from common.challenge import CryptoChallenge
from common.ciphers.block.modes import CTR
from common.tools.misc import RandomByteGenerator


class CTRBitFlippingAttack(BitFlippingAttack):
    
    def get_string(self):
        # As before, first 10 bytes complete the block before the one we are
        # targeting.
        return 'X'*10 + 'X'*self.block_size


class Set4Challenge26(CryptoChallenge):

    BLOCK_SIZE = 16
    NONCE_SIZE = 8

    def validate(self):
        secret_key = RandomByteGenerator().value(self.BLOCK_SIZE)
        secret_nonce = random.randint(0, 2**64 - 1)
        mode = CTR(nonce=secret_nonce)
        profile_generator = UserProfileGenerator(secret_key, mode)
        attack = CTRBitFlippingAttack(profile_generator, self.BLOCK_SIZE)
        encrypted_profile = attack.value()
        profile = UserProfileParser(secret_key, mode).parse(encrypted_profile)
        return ';admin=true' in profile