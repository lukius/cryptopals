import zlib

from common.attacks.compression import CTRCompressionRatioAttack,\
                                       CBCCompressionRatioAttack
from common.challenge import CryptoChallenge
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import BlockCipherMode, CBC, CTR
from common.tools.misc import RandomByteGenerator
from common.tools.base64 import Base64Encoder


class HTTPCompressionOracle(object):
    
    REQUEST = 'POST / HTTP/1.1\n' +\
              'Host: www.lta.com.ar\n' +\
              'Cookie: sessionid=%s\n' +\
              'Content-Length: %d\n\n' +\
              '%s'
              
    def __init__(self, session_id):
        self.session_id = session_id
        
    def _encrypt(self, message):
        key = RandomByteGenerator().value(BlockCipherMode.DEFAULT_BLOCK_SIZE)
        cipher = AES(key)
        mode = self._get_encryption_mode()
        return cipher.encrypt(message, mode=mode)

    def get_compressed_length(self, content):
        request = self.REQUEST % (self.session_id, len(content), content)
        compressed_request = zlib.compress(request)
        encrypted_request = self._encrypt(compressed_request)
        return len(encrypted_request)
    
    def _get_encryption_mode(self):
        raise NotImplementedError
        
        
class CTRCompressionOracle(HTTPCompressionOracle):
    
    def _get_encryption_mode(self):
        return CTR()
    

class CBCCompressionOracle(HTTPCompressionOracle):
    
    def _get_encryption_mode(self):
        iv = RandomByteGenerator().value(CBC.DEFAULT_BLOCK_SIZE)
        return CBC(iv)


class Set7Challenge51Base(CryptoChallenge):
    
    # This length corresponds to the length of the cookie used in the challenge.
    # For greater lengths, the algorithm used here does not seem to work
    # properly. However, it might be fixed by using symbols of greater size
    # (e.g., combinations of three characters instead of two) and just keeping
    # the first character of each candidate symbol on each iteration. The
    # downside of this is that the running time increases exponentially.
    COOKIE_SIZE = 32
    COOKIE = RandomByteGenerator().value(COOKIE_SIZE)
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.cookie = Base64Encoder().encode(self.COOKIE)
    
    def expected_value(self):
        return self.cookie
    
    def value(self):
        return self._get_attack().value()
    
    def _get_attack(self):
        raise NotImplementedError
    
    
class Set7Challenge51UsingCTR(Set7Challenge51Base):

    def _get_attack(self):
        oracle = CTRCompressionOracle(self.cookie)
        return CTRCompressionRatioAttack(oracle)


class Set7Challenge51UsingCBC(Set7Challenge51Base):

    def _get_attack(self):
        oracle = CBCCompressionOracle(self.cookie)
        return CBCCompressionRatioAttack(oracle)