import string

from common.challenge import CryptoChallenge
from common.ciphers.stream.rc4 import RC4
from common.tools.base64 import Base64Decoder
from common.tools.misc import RandomByteGenerator, Concatenation


class RC4SingleByteBiasAttack(object):
    
    # Based on "On the Security of RC4 in TLS and WPA" by Bernstein et al.
    
    BIASED_BYTE_1 = (15, 240)
    BIASED_BYTE_2 = (31, 224)
    EXPERIMENTS = 2**23
    
    def __init__(self, oracle):
        self.oracle = oracle
        self.length = self._get_suffix_length()
        
    def _get_suffix_length(self):
        return len(self.oracle.encrypt(''))
    
    def _build_bias_maps_using(self, prefix_length):
        i = self.BIASED_BYTE_1[0]
        j = self.BIASED_BYTE_2[0]
        biases_i = [0 for _ in range(256)]
        biases_j = [0 for _ in range(256)]
        prefix = 'X'* prefix_length
        for _ in xrange(self.EXPERIMENTS):
            ciphertext = self.oracle.encrypt(prefix)
            ciphered_byte_i = ciphertext[i]
            ciphered_byte_j = ciphertext[j] if j < len(ciphertext) else '\0'
            biases_i[ord(ciphered_byte_i)] += 1
            biases_j[ord(ciphered_byte_j)] += 1
        return biases_i, biases_j
    
    def _sort_descending(self, bias_map):
        return sorted(enumerate(bias_map),
                      key=lambda item: item[1],
                      reverse=True)
        
    def _find_printable_bytes(self, biases_i, biases_j):
        biased_byte_i = self.BIASED_BYTE_1[1]
        biased_byte_j = self.BIASED_BYTE_2[1]
        for c_i, _ in biases_i:
            p_i = chr(biased_byte_i ^ c_i)
            if p_i in string.printable:
                break
        for c_j, _ in biases_j:
            p_j = chr(biased_byte_j ^ c_j)
            if p_j in string.printable:
                break
        return p_i, p_j
        
    def _decrypt_bytes(self, prefix_length):
        biases_i, biases_j = self._build_bias_maps_using(prefix_length)
        biases_i = self._sort_descending(biases_i)
        biases_j = self._sort_descending(biases_j)
        # This is to find the first printable bytes following the bias maps
        # order. Since we know that the plaintext is English, this might
        # help and reduce the number of experiments to be performed.
        return self._find_printable_bytes(biases_i, biases_j)
        
    def value(self):
        suffix = [str() for _ in range(self.length)]
        biased_byte_position = self.BIASED_BYTE_1[0]
        for i in range(1 + self.length/2):
            # Generate a prefix long enough to place the ith byte of the
            # ciphertext in position 15 and the jth byte in position 31.
            j = i + biased_byte_position + 1
            prefix_length = self.length - j + 1
            byte_i, byte_j = self._decrypt_bytes(prefix_length)
            suffix[i] = byte_i
            if j < self.length:
                suffix[j] = byte_j
        return Concatenation(suffix).value()
        

class RC4EncryptionOracle(object):
    
    RC4_KEY_SIZE = 16
    
    def __init__(self, suffix):
        self.suffix = suffix
        
    def encrypt(self, message):
        key = RandomByteGenerator().value(self.RC4_KEY_SIZE)
        return RC4(key).encrypt(message + self.suffix)
        

class Set7Challenge56(CryptoChallenge):
    
    PLAINTEXT = 'QkUgU1VSRSBUTyBEUklOSyBZT1VSIE9WQUxUSU5F'
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.plaintext = Base64Decoder().decode(self.PLAINTEXT)
    
    def expected_value(self):
        return self.plaintext
    
    def value(self):
        oracle = RC4EncryptionOracle(self.plaintext)
        return RC4SingleByteBiasAttack(oracle).value()