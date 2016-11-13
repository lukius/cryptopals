from common.challenge import CryptoChallenge
from common.tools.padders import PKCS7Padder


class Set2Challenge09(CryptoChallenge):
    
    STRING = 'YELLOW SUBMARINE'
    
    def expected_value(self):
        return '%s%s' % (self.STRING, '\4'*4)

    def value(self):
        return PKCS7Padder(self.STRING).value(20)