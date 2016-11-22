from Crypto.Util.asn1 import DerOctetString, DerSequence, DerNull

from common.hash.sha1 import SHA1
from common.signature.rsa import RSADigitalSignature


class PKCS1_15DigitalSignature(RSADigitalSignature):
    
    def __init__(self, hash_function=SHA1):
        RSADigitalSignature.__init__(self)
        self.hash_function = hash_function()
        
    def _encode(self, message):
        hash_oid = self.hash_function.get_OID()
        digest = self.hash_function.hash(message)
        der_digest = DerOctetString(digest).encode()
        der_null = DerNull().encode()
        der_sequence = DerSequence([hash_oid, der_null]).encode()
        hash_info = DerSequence([der_sequence, der_digest]).encode()
        hash_size = len(hash_info)
        padding = '\xff'*(self.n_size - hash_size - 3)
        return '\x00\x01' + padding + '\0' + hash_info