from common.attacks.bitflipping import BitFlippingAttack,\
                                       UserProfileGenerator, UserProfileParser
from common.challenge import CryptoChallenge
from common.ciphers.block.modes import CBC
from common.tools.misc import RandomByteGenerator


class CBCBitFlippingAttack(BitFlippingAttack):
    
    def get_string(self):
        # Generate profile using enough data to make two extra blocks.
        # First 10 bytes complete the previous block. We assume knowledge
        # of the prefix introduced by the profile generator.
        return 'X'*(10 + 2*self.block_size)


class Set2Challenge16(CryptoChallenge):

    BLOCK_SIZE = 16

    def validate(self):
        secret_key = RandomByteGenerator().value(self.BLOCK_SIZE)
        secret_iv = RandomByteGenerator().value(self.BLOCK_SIZE)
        mode = CBC(secret_iv)
        profile_generator = UserProfileGenerator(secret_key, mode)
        attack = CBCBitFlippingAttack(profile_generator, self.BLOCK_SIZE)
        encrypted_profile = attack.value()
        profile = UserProfileParser(secret_key, mode).parse(encrypted_profile)
        return ';admin=true' in profile