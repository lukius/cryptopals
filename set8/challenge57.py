from common.challenge import MatasanoChallenge
from common.attacks.discrete_log import PohligHellmannAttack
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
        
    def get_authenticated_message(self, public_key):
        key = self.dh.get_secret_from(public_key)
        mac = CustomMAC().value(key)
        return self.M, mac.value(self.M)
    
    
class CustomMAC(object):
    
    def value(self, key): 
        key_bytes = IntToBytes(key).value()
        return HMAC(key_bytes, hash_function=SHA256)
    
    
class DHSubgroupConfinementAttack(PohligHellmannAttack):    

    def __init__(self, target):
        PohligHellmannAttack.__init__(self, target.p, target.q)
        self.target = target
        self.mac = CustomMAC()
        
    def _key_is_valid(self, trial_key, h):
        # Send h to the target and receive the authenticated message.    
        msg, target_mac = self.target.get_authenticated_message(h)
        trial_mac = self.mac.value(trial_key)
        return trial_mac.value(msg) == target_mac


class Set8Challenge57(MatasanoChallenge):
    
    def __init__(self):
        MatasanoChallenge.__init__(self)
        self.bob = DHMessageAuthenticator()
    
    def expected_value(self):
        return self.bob._get_secret_key()
    
    def value(self):
        attack = DHSubgroupConfinementAttack(self.bob)
        return attack.recover_key()