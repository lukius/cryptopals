from common.attacks.gcm.truncated_mac import ExtendedTruncatedMACGCMAttack
from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import GCM
from common.tools.misc import RandomByteGenerator


class Set8Challenge65(CryptoChallenge):
    
    def _test_key_recovery(self):
        byte_generator = RandomByteGenerator()
        gcm_iv = byte_generator.value(12)
        aes_key = byte_generator.value(16)
        message = byte_generator.value(16 * 3)

        aes = AES(aes_key)
        gcm = GCM(gcm_iv, tag_length=16)
        c, t = aes.encrypt(message, mode=gcm)
        
        attack = ExtendedTruncatedMACGCMAttack(aes, gcm, c, t)
        key = attack.recover_key()
        
        self._assert_equals(gcm.H, key)        
    
    def _validate(self):
        self._test_key_recovery()