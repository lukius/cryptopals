from common.attacks.mac import MDHashBasedMACMessageForger
from common.challenge import CryptoChallenge
from common.hash.md4 import MD4
from common.mac.hash import HashBasedMAC
from common.tools.misc import RandomByteGenerator


class MD4BasedMACMessageForger(MDHashBasedMACMessageForger):
    
    def _hash_function(self):
        return MD4


class Set4Challenge30(CryptoChallenge):
    
    STRING = 'comment1=cooking%20MCs;userdata=foo;'+\
             'comment2=%20like%20a%20pound%20of%20bacon'
    TARGET_STRING = ';admin=true'

    def validate(self):
        key = RandomByteGenerator().value(20)
        md4mac = HashBasedMAC(key, MD4)
        string_mac = md4mac.value(self.STRING)
        message, mac = MD4BasedMACMessageForger(md4mac).\
                       forge(self.STRING, string_mac, self.TARGET_STRING)
                       
        return message.startswith(self.STRING) and\
               message.endswith(self.TARGET_STRING) and\
               md4mac.validate(message, mac)