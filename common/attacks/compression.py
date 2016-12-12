import random
import string

from common.ciphers.block.modes import BlockCipherMode


class CompressionRatioAttack(object):
    
    PREFIX = 'sessionid='
    SUFFIX = 'Content'
    ALPHABET = string.letters + string.digits + '/-+=\n'
    
    def __init__(self, oracle):
        self.oracle = oracle
        # A symbol is a concatenation of two valid characters that might appear
        # in the message we want to crack. Using two bytes per symbol possibly
        # reduces the chances of errors such as false positives.
        self.symbols = [x+y for x in self.ALPHABET for y in self.ALPHABET]

    def _get_compressed_probe_length(self, message):
        probe = '%s%s' % (self.PREFIX, message)
        return self.oracle.get_compressed_length(probe)
        
    def _get_suffix_index(self, message):
        return message.find(self.SUFFIX)
        
    def _message_not_cracked(self, message):
        return self._get_suffix_index(message) == -1
        
    def _remove_suffix_from(self, message):
        index = self._get_suffix_index(message)
        return message[:index-1]
        
    def value(self):
        message = str()
        while self._message_not_cracked(message):
            # Crack the message iteratively. Every call to crack_bytes will
            # return a new valid prefix of the message.
            message = self._crack_bytes(message)
        return self._remove_suffix_from(message)
    
    def _crack_bytes(self, cookie):
        raise NotImplementedError
    
    
class CTRCompressionRatioAttack(CompressionRatioAttack):
    
    def _crack_bytes(self, message):
        # Find which symbol gives the shortest byte length after compressing.
        min_length = candidate = None
        for symbol in self.symbols:
            length = self._get_compressed_probe_length(message+symbol)
            if min_length is None or length < min_length:
                min_length = length
                candidate = symbol
        return message + candidate


class CBCCompressionRatioAttack(CompressionRatioAttack):
    
    BLOCK_SIZE = BlockCipherMode.DEFAULT_BLOCK_SIZE
    
    def __init__(self, oracle):
        CompressionRatioAttack.__init__(self, oracle)
        self.padding_chars = [char for char in string.printable
                              if char not in self.ALPHABET
                              if char not in ' :.']
    
    def _get_block_length(self, message):
        byte_length = self._get_compressed_probe_length(message)
        return byte_length / self.BLOCK_SIZE
    
    def _get_offset(self, message):
        initial_block_length = self._get_block_length(message)
        pad_size = 1
        while True:
            padding_chars = [random.choice(self.padding_chars)
                             for _ in range(pad_size)]
            padding = ''.join(padding_chars)
            block_length = self._get_block_length(message+padding)
            if block_length == initial_block_length+1:
                return pad_size
            pad_size += 1
    
    def _crack_bytes(self, cookie):
        # For every possible symbol, find out which one has the longest
        # offset. The offset is the minimum amount of bytes that need to be
        # added as suffix of the request in order to cross the block boundary.
        # The correct symbol will compress better, and thus it will have a
        # larger offset than any other symbol.
        max_offset = candidate = None
        initial_cookie_offset = self._get_offset(cookie)
        for symbol in self.symbols:
            offset = self._get_offset(cookie+symbol)
            # A wrong symbol will compress worse, and thus the final byte
            # length will increase. This will make the offset shorter than the
            # initial one, which is correct since it belongs to an already
            # cracked prefix of the cookie.
            if offset >= initial_cookie_offset and\
               (max_offset is None or offset > max_offset):
                max_offset = offset
                candidate = symbol
        return cookie + candidate[0]