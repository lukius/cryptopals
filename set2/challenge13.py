import random

from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import ECB
from common.tools.padders import PKCS7Padder
from common.tools.misc import RandomByteGenerator


class UserProfileParser(object):

    FIELDS = ['email', 'uid', 'role']

    def __init__(self, key):
        self.cipher = AES(key)

    def _parse(self, profile):
        tuples = profile.split('&')
        return dict(map(lambda item: item.split('='), tuples))
    
    def _profile_has_valid_fields(self, profile):
        return set(profile.keys()) == set(self.FIELDS)
    
    def _validate(self, profile):
        if not self._profile_has_valid_fields(profile):
            raise RuntimeError('invalid profile!')

    def parse(self, encrypted_profile):
        profile_string = self.cipher.decrypt(encrypted_profile, mode=ECB())
        profile = self._parse(profile_string.bytes())
        self._validate(profile)
        return profile


class UserProfileGenerator(object):

    def __init__(self, key):
        self.cipher = AES(key)
        self.profile_template = 'email=%s&uid=%d&role=user'

    def _rand_uid(self):
        return random.randint(10,99)

    def profile_for(self, email):
        if '&' in email or '=' in email:
            raise RuntimeError('email address has invalid characters!')
        uid = self._rand_uid()
        profile = self.profile_template % (email, uid)
        return self.cipher.encrypt(profile, mode=ECB())


class AdminUserProfileGenerator(object):

    BLOCK_SIZE = 16

    def __init__(self, profile_generator):
        self.profile_generator = profile_generator
        
    def value(self):
        # 1. Use as input any email that makes the second block end just
        # before the role:
        # email=xxxxxx@xx.
        # com&uid=xx&role=
        # user
        email = 'xxxxxx@xx.com'
        ciphertext1 = self.profile_generator.profile_for(email)
        
        # 2. Use as input an email containing 'admin' appropriately padded:
        # email=xxxxxx@xx.
        # admin$$$$$$$$$$$
        # &uid=xx&role=use
        # r
        admin_padded = PKCS7Padder('admin').value(self.BLOCK_SIZE) 
        email = 'xxxxxx@xx.%s' % admin_padded
        ciphertext2 = self.profile_generator.profile_for(email)
        
        # 3. Keep first two blocks from ciphertext1 and second block from
        # ciphertext2.
        ciphertext1.replace_block(2, ciphertext2.get_block(1))
        return ciphertext1


class Set2Challenge13(CryptoChallenge):

    BLOCK_SIZE = AdminUserProfileGenerator.BLOCK_SIZE

    def expected_value(self):
        return 'admin'

    def value(self):
        secret_key = RandomByteGenerator().value(self.BLOCK_SIZE)
        profile_generator = UserProfileGenerator(secret_key)
        # The secret key is not known by the admin profile generator.
        encrypted_profile = AdminUserProfileGenerator(profile_generator).\
                            value()
        profile = UserProfileParser(secret_key).parse(encrypted_profile)
        return profile['role']