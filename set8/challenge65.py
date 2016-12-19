from common.attacks.gcm.truncated_mac import ExtendedTruncatedMACGCMAttack
from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import GCM
from common.tools.misc import RandomByteGenerator


class Challenge65GCM(GCM):
    
    # As before, this is a custom GCM tailored for this challenge, for
    # efficiency purposes only. Since the extension of the ciphertexts just
    # prepends null blocks, we can safely skip them when computing the GHASH.
    
    def __init__(self, block_length, iv, tag_length=None):
        GCM.__init__(self, iv, tag_length=tag_length)
        # We save the original ciphertext's block length (i.e., before being
        # extended).
        self.block_length = block_length
        
    def _is_power_of_2(self, i):
        return i & (i-1) == 0        
        
    def _ghash(self, cipher, auth_data, ciphertext):
        n = ciphertext.block_count()
        
        if n == self.block_length:
            # When dealing with the original ciphertext, just compute it the
            # regular way.
            ghash = GCM._ghash(self, cipher, auth_data, ciphertext)
        else:
            ghash = 0
            j = 2
            h = self._to_field_elem(self.H)
            
            # Otherwise, iterate first over the blocks that are multiplied by
            # h^(2^i) for some i (we can safely skip the others as we assume
            # they are zero due to the extension). 
            while j <= n:
                block = ciphertext.get_block(n - j + 1)
                z = self._to_field_elem(block)
                ghash += z * h**j
                j <<= 1
                
            # Then, traverse the blocks at indices corresponding to the
            # original ciphertext which are multiplied by h^k with k not being
            # a power of 2.       
            k = self.block_length + 1
            for i in xrange(self.block_length):
                block = ciphertext.get_block(n - self.block_length + i)
                if not self._is_power_of_2(k):
                    z = self._to_field_elem(block)
                    ghash += z * h**k
                k -= 1
                
            # Finally, include the length block.
            len_C = len(ciphertext)*8
            ghash += self.field.element(len_C)*h
            
        return ghash


class Set8Challenge65(CryptoChallenge):
    
    MESSAGE_BLOCK_LENGTH = 3
    
    def _test_key_recovery(self):
        byte_generator = RandomByteGenerator()
        gcm_iv = byte_generator.value(12)
        aes_key = byte_generator.value(16)
        message = byte_generator.value(16 * self.MESSAGE_BLOCK_LENGTH)

        aes = AES(aes_key)
        gcm = Challenge65GCM(self.MESSAGE_BLOCK_LENGTH, gcm_iv, tag_length=16)
        c, t = aes.encrypt(message, mode=gcm)
        
        attack = ExtendedTruncatedMACGCMAttack(aes, gcm, c, t)
        key = attack.recover_key()
        
        self._assert_equals(gcm.H, key)
    
    def _validate(self):
        self._test_key_recovery()