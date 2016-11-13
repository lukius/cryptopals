from common.challenge import CryptoChallenge
from common.key_exchange.protocols.ssrp import SimplifiedSRPClient,\
                                               SimplifiedSRPServer
from common.mac.hmac import HMAC
from common.hash.sha256 import SHA256


class SSRPPasswordCracker(SimplifiedSRPServer):
    
    def __init__(self, password_list):
        SimplifiedSRPServer.__init__(self, str(), str())
        self.password_list = password_list
        
    def _init_state(self):
        SimplifiedSRPServer._init_state(self)
        self.b = 1
        self.u = 1
        
    def _hmac_from_password_validates(self, password):
        hashed_password = self.sha256.hash(self.salt + password)
        x = self._to_int(hashed_password)
        v = self.modexp.value(self.G, x)
        # Since u = b = 1, modular exponentiation vanishes:
        # S = (A * v ** u)**b % n = (A * v) % n
        S = (self.A*v) % self.p
        S_bytes = self._from_int(S)
        K = self.sha256.hash(S_bytes)
        hmac = HMAC(K, SHA256).value(self.salt)
        return hmac == self.received_hmac
        
    def crack(self):
        for password in self.password_list:
            if self._hmac_from_password_validates(password):
                return password


class Set5Challenge38(CryptoChallenge):
    
    EMAIL = 'foo@bar.baz'
    PASSWORD = 'admin1234'
    
    def _get_password_list(self):
        # This is a very short password list, but it is pointless to
        # provide additional passwords. It will just make the challenge
        # run slower.
        words = ['password', 'root', 'admin', 'user', 'guest']
        nums = ['1', '12', '123', '1234', '4321', '321', '21']
        return [word+num for word in words for num in nums]
    
    def validate(self):
        password_list = self._get_password_list()
        client = SimplifiedSRPClient(self.EMAIL, self.PASSWORD)
        password_cracker = SSRPPasswordCracker(password_list)
        
        password_cracker.start()
        client.start()
        client.stop()
        password_cracker.stop()
        
        cracked_password = password_cracker.crack()

        return cracked_password == self.PASSWORD