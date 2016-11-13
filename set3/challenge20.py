from common.attacks.xor import RepeatingKeyXORDecrypter
from common.tools.base64 import Base64Decoder
from common.ciphers.block.aes import AES
from common.ciphers.block.modes import CTR
from common.challenge import CryptoChallenge
from common.tools.misc import Concatenation, FileLines, RandomByteGenerator


class FixedNonceCTRDecrypter(object):
        
    def decrypt(self, ciphertexts):
        ciphertext = ConcatenationAfterTruncation(ciphertexts).value()
        return RepeatingKeyXORDecrypter().decrypt(ciphertext)


class ConcatenationAfterTruncation(object):

    def __init__(self, strings):
        self.strings = strings

    def value(self):
        min_length = min(map(len, self.strings))
        strings = [string[:min_length] for string in self.strings]
        return Concatenation(strings).value()


class Set3Challenge20(CryptoChallenge):
    
    FILE = 'set3/data/20.txt'
    ANSWER_FILE = 'set3/data/20ans.txt'
    BLOCK_SIZE = 16
    
    def expected_value(self):
        strings = FileLines(self.ANSWER_FILE).value()
        return ConcatenationAfterTruncation(strings).value()
    
    def _encrypt(self, plaintexts):
        key = RandomByteGenerator().value(self.BLOCK_SIZE)
        aes = AES(key)
        return map(lambda text: aes.encrypt(text, mode=CTR(nonce=0)).bytes(),
                   plaintexts)
    
    def value(self):
        plaintexts = Base64Decoder().decode_file_lines(self.FILE)
        ciphertexts = self._encrypt(plaintexts)
        return FixedNonceCTRDecrypter().decrypt(ciphertexts)