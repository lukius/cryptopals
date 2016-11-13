from common.challenge import CryptoChallenge
from common.hash.sha1 import SHA1
from common.mac.hash import HashBasedMAC
from common.tools.misc import RandomByteGenerator


class Set4Challenge28(CryptoChallenge):

    MESSAGE = 'foo bar baz'

    def _check_valid_mac(self, sha1mac):
        mac = sha1mac.value(self.MESSAGE)
        return sha1mac.validate(self.MESSAGE, mac)
    
    def _check_invalid_mac(self, sha1mac):
        mac = sha1mac.value(self.MESSAGE)
        return not sha1mac.validate(self.MESSAGE + ' qux', mac)    

    def validate(self):
        key = RandomByteGenerator().value()
        sha1mac = HashBasedMAC(key, SHA1)
        valid_mac_ok = self._check_valid_mac(sha1mac)
        invalid_mac_ok = self._check_invalid_mac(sha1mac)
        return valid_mac_ok and invalid_mac_ok
        