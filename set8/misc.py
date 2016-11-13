from common.hash.sha256 import SHA256
from common.key_exchange.diffie_hellman import DiffieHellman
from common.mac.hmac import HMAC
from common.tools.converters import IntToBytes


class DHMessageAuthenticator(object):
    
    p = 7199773997391911030609999317773941274322764333428698921736339643928346453700085358802973900485592910475480089726140708102474957429903531369589969318716771
    g = 4565356397095740655436854503483826832136106141639563487732438195343690437606117828318042418238184896212352329118608100083187535033402010599512641674644143
    q = 236234353446506858198510045061214171961
    
    M = 'crazy flamboyant for the rap enjoyment'
    
    def __init__(self):
        self.dh = DiffieHellman(self.p, self.g, g_order=self.q)
        
    def _get_secret_key(self):
        # Not part of the public interface (i.e., not known to the attacker).
        return self.dh.exp
    
    def get_public_key(self):
        return self.dh.get_public_key()
        
    def get_authenticated_message(self, public_key):
        key = self.dh.get_secret_from(public_key)
        mac = CustomMAC().value(key)
        return self.M, mac.value(self.M)
    
    
class CustomMAC(object):
    
    def value(self, key): 
        key_bytes = IntToBytes(key).value()
        return HMAC(key_bytes, hash_function=SHA256)