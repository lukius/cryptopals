from common.challenge import CryptoChallenge
from common.tools.blockstring import BlockString
from common.hash import HashFunction
from common.mac.cbc import CBC_MAC
from common.tools.xor import ByteXOR
from common.tools.padders import PKCS7Padder


class CBC_MACHash(HashFunction):

    def __init__(self, key, iv):
        HashFunction.__init__(self)
        self.mac_generator = CBC_MAC(key, iv=iv)
    
    def hash(self, message):
        return self.mac_generator.value(message)


class Set7Challenge50(CryptoChallenge):
    
    BLOCK_SIZE = 16
    KEY = 'YELLOW SUBMARINE'
    IV = '\0'*BLOCK_SIZE
    SNIPPET = "alert('MZA who was that?');"
    TARGET_SNIPPET = "alert('Ayo, the Wu is back!');"
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.hash_function = CBC_MACHash(self.KEY, self.IV)
    
    def expected_value(self):
        return self.hash_function.hash(self.SNIPPET)
    
    def value(self):
        # This was found "by hand", using the idea explored in the previous
        # challenge: concatenate our target snippet with the original one, 
        # and use the latter MAC code as the final MAC code of the whole 
        # message. Thus, the crafted code snippet will look like:
        #
        # alert('Ayo, the Wu is back!');        var x = ('<GARBAGE>as that?');
        #
        # where <GARBAGE> stands for the the concatenation of 16-byte PKCS7
        # padding and the XOR between the first block of the original snippet
        # and the MAC code of the first part of that message.
        # This script was tested on Chrome and worked OK (luckily, no "'"
        # appeared inside <GARBAGE>).
        
        # 2 spaces complete the second block, and 6 of them are just used
        # to complete block 3 and leave room for the 'var x' declaration.
        spaces = ' '*8
        var_x = 'var x = (\''
        prefix = '%s%s%s' % (self.TARGET_SNIPPET, spaces, var_x)
        padded_prefix = PKCS7Padder(prefix).value(self.BLOCK_SIZE)
        
        snippet = BlockString(self.SNIPPET, self.BLOCK_SIZE)
        prefix_hash = self.hash_function.hash(prefix)
        garbage = ByteXOR(snippet.get_block(0), prefix_hash).value()
        # last block is just "as that?');"
        last_block = snippet.get_block(-1)
        
        crafted_snippet = '%s%s%s' % (padded_prefix, garbage, last_block)
        return self.hash_function.hash(crafted_snippet)