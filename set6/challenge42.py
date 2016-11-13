from common.challenge import CryptoChallenge
from common.ciphers.pubkey.rsa import FixedERSA
from common.hash.sha1 import SHA1
from common.math.root import NthRoot
from common.signature.pkcs1_15 import PKCS1_15DigitalSignature
from common.tools.converters import BytesToInt, IntToBytes
from common.tools.misc import ByteSize
from common.tools.padders import RightPadder, LeftPadder


class EEquals3RSASignatureForger(object):
    
    # This will just work for SHA1-based signatures.
    ASN1_BYTES = '0!0\t\x06\x05+\x0e\x03\x02\x1a\x05\x00\x04\x14'
    PREFIX = '\x00\x01'
    PADDING_BYTE = '\xff'
    INITIAL_PAD_SIZE = 10
    
    def __init__(self, public_key):
        self.e, self.n = public_key
        self.n_size = ByteSize(self.n).value()
        
    def _get_signature_block(self, pad_size, string):
        digest = SHA1().hash(string)
        prefix = '%s%s\x00%s%s' % (self.PREFIX, self.PADDING_BYTE*pad_size,
                                   self.ASN1_BYTES, digest)
        return RightPadder(prefix).value(self.n_size, char='\x00')

    def _prefix_bytes_match(self, candidate_block, block, pad_size):
        end_index = len(self.PREFIX) + pad_size + 1 + len(self.ASN1_BYTES) + 20
        return candidate_block[:end_index] == block[:end_index]
    
    def _to_bytes(self, integer):
        return IntToBytes(integer).value()
    
    def _get_candidate_block_from(self, block):
        integer = BytesToInt(block).value()
        root = NthRoot(self.e).value(integer)
        next_power = (root+1)**self.e
        candidate_block = self._to_bytes(next_power)
        return root+1, LeftPadder(candidate_block).value(self.n_size,
                                                         char='\x00')
    
    def forge(self, string):
        pad_size = self.INITIAL_PAD_SIZE
        # Iterate pad sizes until we find a valid signature.
        while True:
            # Get the zero-padded block for this pad size:
            # 0x00 0x01 0xff ... 0xff 0x00 ASN.1_INFO HASH_DIGEST 
            block = self._get_signature_block(pad_size, string)
            if len(block) > self.n_size:
                raise RuntimeError('failed to find a valid signature')
            # Get a candidate block and then check if it is suitable.
            # A candidate block is built taking the eth root r of the current
            # block and getting the bytes out of (r+1)**e. If its prefix
            # matches with the original block, then we have found a valid
            # signature.
            eth_root, candidate_block = self._get_candidate_block_from(block)
            if self._prefix_bytes_match(candidate_block, block, pad_size):
                signature = self._to_bytes(eth_root)
                break
            pad_size += 1
        return signature


class InsecurePKCS1_15DigitalSignature(PKCS1_15DigitalSignature):
    
    def _RSA(self):
        return FixedERSA(e=3)
    
    def _get_hash_from(self, block):
        # Skip first two bytes
        start_index = 2
        # Skip padding
        while block[start_index] == '\xff':
            start_index += 1
        # Skip zero byte
        start_index += 1
        # Skip ASN.1/SHA1 info
        start_index += 15
        return block[start_index:start_index+20]
    
    def verify(self, message, signature):
        message_hash = self.hash_function.hash(message)
        block = self._decrypt(signature)
        hash_from_signature = self._get_hash_from(block)
        return message_hash == hash_from_signature


class Set6Challenge42(CryptoChallenge):

    STRING = 'hi mom'
    
    def validate(self):
        singature_verifier = InsecurePKCS1_15DigitalSignature()
        public_key = singature_verifier.get_public_key()
        signature = EEquals3RSASignatureForger(public_key).forge(self.STRING)
        return singature_verifier.verify(self.STRING, signature)