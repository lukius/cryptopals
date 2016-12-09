from common.math.finite_field import GF2k
from common.tools.blockstring import BlockString
from common.tools.converters import IntToBytes, BytesToInt
from common.tools.padders import PKCS7Padder, PKCS7Unpadder,\
                                 RightPadder
from common.tools.xor import ByteXOR


class BlockCipherMode(object):
    
    DEFAULT_BLOCK_SIZE = 16

    @classmethod                  
    def name(cls):
        return cls.__name__

    def __init__(self, block_size=None):
        self.block_size = self.DEFAULT_BLOCK_SIZE if block_size is None\
                          else block_size 
    
    def _pad(self, string):
        return PKCS7Padder(string).value(self.block_size)

    def _unpad_if_needed(self, index, block):
        if self.block_string.is_last_block_index(index):
            block = PKCS7Unpadder(block).value()
        return block    
    
    def _iterate_blocks_with(self, block_string, cipher, callback):
        self.cipher = cipher
        self.block_string = block_string
        result = BlockString(block_size=self.block_size)
        return reduce(lambda _result, block: _result + callback(*block),
                      enumerate(self.block_string), result)

    def _block_encryption_callback(self, index, block):
        raise NotImplementedError
    
    def _block_decryption_callback(self, index, block):
        raise NotImplementedError

    def encrypt_with_cipher(self, plaintext, cipher):
        if type(plaintext) != BlockString:
            plaintext = BlockString(plaintext, self.block_size)
        plaintext = self._pad(plaintext)
        return self._iterate_blocks_with(plaintext, cipher,
                                         self._block_encryption_callback)
    
    def decrypt_with_cipher(self, ciphertext, cipher):
        if type(ciphertext) != BlockString:
            ciphertext = BlockString(ciphertext, self.block_size)
        return self._iterate_blocks_with(ciphertext, cipher,
                                         self._block_decryption_callback)


class ECB(BlockCipherMode):
    
    def _block_encryption_callback(self, index, block):
        return self.cipher.encrypt_block(block)
    
    def _block_decryption_callback(self, index, block):
        plaintext_block = self.cipher.decrypt_block(block)
        plaintext_block = self._unpad_if_needed(index, plaintext_block)
        return plaintext_block    
    

class CBC(BlockCipherMode):
    
    def __init__(self, iv, block_size=None):
        BlockCipherMode.__init__(self, block_size)
        self.iv = iv

    def _xor(self, string1, string2):
        return ByteXOR(string1, string2).value()

    def _block_encryption_callback(self, index, block):
        if index == 0:
            self.last_ciphertext_block = self.iv 
        xor_block = self._xor(block, self.last_ciphertext_block)
        ciphertext_block = self.cipher.encrypt_block(xor_block)        
        self.last_ciphertext_block = ciphertext_block
        return ciphertext_block
    
    def _block_decryption_callback(self, index, block):
        if index == 0:
            self.last_ciphertext_block = self.iv
        decrypted_block = self.cipher.decrypt_block(block)
        plaintext_block = self._xor(decrypted_block,
                                    self.last_ciphertext_block)
        plaintext_block = self._unpad_if_needed(index, plaintext_block)
        self.last_ciphertext_block = block
        return plaintext_block
        
        
class CTR(BlockCipherMode):
    
    def __init__(self, counter=None, nonce=None, block_size=None):
        from counter import DefaultCounter, NonceBasedCounter
        BlockCipherMode.__init__(self, block_size)
        if nonce is not None:
            counter = NonceBasedCounter(nonce, block_size)
        self.counter = counter if counter is not None\
                       else DefaultCounter(block_size)
                       
    def _pad(self, plaintext):
        # CTR mode does not need padding.
        return plaintext
                       
    def _xor(self, key, block):
        block_length = len(block)
        return ByteXOR(block, key[:block_length]).value()
    
    def _block_callback(self, index, block):
        key_argument = self.counter.count(index)
        key = self.cipher.encrypt_block(key_argument)
        return self._xor(key, block)
                       
    def _block_encryption_callback(self, index, block):
        return self._block_callback(index, block)
    
    def _block_decryption_callback(self, index, block):
        return self._block_callback(index, block)
    
    
class RandomAccessCTR(CTR):
    
    def __init__(self, *args, **kwargs):
        CTR.__init__(self, *args, **kwargs)
        self.keystream = str()
        
    def get_keystream(self):
        return self.keystream
        
    def _xor(self, key, block):
        self.keystream += key
        return CTR._xor(self, key, block)
    
    
class GCM(CTR):
    
    def __init__(self, iv, tag_length=None, block_size=None):
        CTR.__init__(self, block_size=block_size)
        self.iv = iv
        self.len_iv = len(iv) * 8
        self.tag_length = tag_length/8 if tag_length else self.block_size
        self.field = GF2k(128, modulus='x^128 + x^7 + x^2 + x + 1')
        
    def _unpack_encryption_data(self, data):
        if isinstance(data, (tuple,list)):
            return data
        else:
            return data, str()

    def _unpack_decryption_data(self, data):
        if len(data) == 2:
            return data[0], str(), data[1]
        else:
            return data
        
    def _to_field_elem(self, block):
        int_block = BytesToInt(block).value()
        return self.field.element(int_block)
    
    def _pad(self, block):
        return RightPadder(block).value(16, char='\x00')    
    
    def _from_field_elem(self, X):
        return IntToBytes(X.n).value(size=self.block_size)
        
    def _init_nonce(self, cipher):
        self.H = self._ghash_subkey(cipher)
        if self.len_iv == 96:
            self.y0 = self.iv + IntToBytes(1).value(4)
        else:
            Y = self._ghash(cipher, str(), self.iv)
            self.y0 = self._from_field_elem(Y)
            
    def _init_counter(self):
        from common.ciphers.block.counter import GCMCounter
        y0 = BytesToInt(self.y0).value()
        self.counter = GCMCounter(y0, block_size=self.block_size)
        
    def _ghash_subkey(self, cipher):
        return cipher.encrypt('\x00' * self.block_size, mode=CTR()).bytes()
        
    def _ghash(self, cipher, auth_data, ciphertext):
        H = self._to_field_elem(self.H)
        X = self.field.element(0)
        len_A = len_C = 0
        for block in BlockString(auth_data):
            padded_block = self._pad(block)
            A = self._to_field_elem(padded_block)
            X = (X + A) * H
            len_A += len(block)*8
        for block in ciphertext:
            padded_block = self._pad(block)
            A = self._to_field_elem(padded_block)
            X = (X + A) * H
            len_C += len(block)*8
        L = self.field.element((len_A << 64) + len_C)
        X = (X + L) * H
        return X
    
    def _tag(self, cipher, G):
        S = self._to_field_elem(cipher.encrypt(self.y0).bytes())
        tag = self._from_field_elem(G + S)
        return tag[:self.tag_length]
        
    def encrypt_with_cipher(self, data, cipher):
        self._init_nonce(cipher)
        self._init_counter()
        plaintext, auth_data = self._unpack_encryption_data(data)
        ciphertext = CTR.encrypt_with_cipher(self, plaintext, cipher)
        G = self._ghash(cipher, auth_data, ciphertext)
        tag = self._tag(cipher, G)
        return ciphertext, tag
    
    def decrypt_with_cipher(self, data, cipher):
        self._init_nonce(cipher)
        self._init_counter()
        ciphertext, auth_data, input_tag = self._unpack_decryption_data(data)
        G = self._ghash(cipher, auth_data, ciphertext)
        tag = self._tag(cipher, G)
        if tag == input_tag:
            plaintext = CTR.decrypt_with_cipher(self, ciphertext, cipher)
            result = (True, plaintext)
        else:
            result = (False, str())
        return result