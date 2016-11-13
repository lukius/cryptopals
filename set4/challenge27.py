from common.attacks.bitflipping import UserProfileGenerator,\
                                       UserProfileParser,\
                                       InvalidProfileException
from common.challenge import CryptoChallenge
from common.ciphers.block.modes import CBC
from common.tools.misc import RandomByteGenerator
from common.tools.xor import ByteXOR


class CBCKeyRecoveryAttack(object):

    def __init__(self, profile_generator, profile_parser):
        self.profile_generator = profile_generator
        self.profile_parser = profile_parser
    
    def _build_ciphertext_from(self, encrypted_profile):
        null_block = '\0'*encrypted_profile.block_size()
        first_block = encrypted_profile.get_block(0)
        last_block = encrypted_profile.get_block(-1)
        penultimate_block = encrypted_profile.get_block(-2)
        # First three blocks are specially crafted to reveal the key.
        # Last two blocks are needed so as to bypass padding validations.
        return '%s%s%s%s%s' % (first_block, null_block, first_block,
                               penultimate_block, last_block)
    
    def _recover_key_from(self, ciphertext):
        # During decryption, the first three blocks will be decrypted like so:
        #   * D(first_block) XOR IV = key
        #   * D(null_block) XOR first_block
        #   * D(first_block) XOR null_block = D(first_block)
        # Thus, when XORing the first and third blocks of the result,
        #   * [D(first_block) XOR key] XOR [D(first_block)] = key
        try:
            self.profile_parser.parse(ciphertext)
        except InvalidProfileException, exception:
            fake_profile = exception.get_profile()
        return ByteXOR(fake_profile.get_block(0),
                       fake_profile.get_block(2)).value()
    
    def value(self):
        encrypted_profile = self.profile_generator.profile_for(str())
        ciphertext = self._build_ciphertext_from(encrypted_profile)
        return self._recover_key_from(ciphertext)
    
    
class CustomUserProfileParser(UserProfileParser):
    
    def _profile_contains_invalid_chars(self, profile):
        char_is_invalid = lambda char: ord(char) > 127
        return any(map(char_is_invalid, profile.bytes()))
    
    def parse(self, encrypted_profile):
        profile = self.cipher.decrypt(encrypted_profile, mode=self.mode)
        if self._profile_contains_invalid_chars(profile):
            raise InvalidProfileException(profile)
        return profile
    

class Set4Challenge27(CryptoChallenge):

    BLOCK_SIZE = 16

    def validate(self):
        secret_key = RandomByteGenerator().value(self.BLOCK_SIZE)
        mode = CBC(iv=secret_key)
        profile_generator = UserProfileGenerator(secret_key, mode)
        profile_parser = CustomUserProfileParser(secret_key, mode)
        recovered_key = CBCKeyRecoveryAttack(profile_generator,
                                             profile_parser).value()
        return recovered_key == secret_key