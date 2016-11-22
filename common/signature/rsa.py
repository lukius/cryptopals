from common.ciphers.pubkey.rsa import RSA
from common.signature import DigitalSignatureScheme
from common.tools.misc import ByteSize
from common.tools.converters import BytesToInt, IntToBytes
from common.tools.padders import LeftPadder


class RSADigitalSignature(DigitalSignatureScheme):

    # Base class for RSA-based digital signatures schemes.
    
    def __init__(self):
        DigitalSignatureScheme.__init__(self)
        self.rsa = self._RSA()
        self.public_key = self.rsa.get_public_key()
        self.e, self.n = self.public_key
        self.n_size = ByteSize(self.n).value()
        
    def _RSA(self):
        # Can be overriden to instanciate RSA object with custom parameters.
        return RSA()
        
    def _decrypt(self, signature):
        decrypted_block = self.rsa.encrypt(signature)
        return LeftPadder(decrypted_block).value(self.n_size, char='\0')
    
    def sign(self, message):
        encoded_message = self.__encode(message)
        # Decrypt in order to use the private key.
        return self.rsa.decrypt(encoded_message)
    
    def verify(self, message, signature):
        encoded_message = self.__encode(message)
        block = self._decrypt(signature)
        return encoded_message == block
    
    def __encode(self, message):
        m = self._encode(message)
        m_n = BytesToInt(m).value() % self.rsa.n
        return self._encode(IntToBytes(m_n).value())
    
    def _encode(self, message):
        # Can be overriden for custom behavior.
        return LeftPadder(message).value(self.n_size, char='\0') 