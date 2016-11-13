from common.attacks.discrete_log import SubgroupConfinementAttack
from common.challenge import CryptoChallenge

from set8.misc import CustomMAC, DHMessageAuthenticator
    
    
class CustomSubgroupConfinementAttack(SubgroupConfinementAttack):    

    def __init__(self, target):
        SubgroupConfinementAttack.__init__(self, target.p, target.q)
        self.target = target
        self.mac = CustomMAC()
        
    def _key_is_valid(self, trial_key, h):
        # Send h to the target and receive the authenticated message.    
        msg, target_mac = self.target.get_authenticated_message(h)
        trial_mac = self.mac.value(trial_key)
        return trial_mac.value(msg) == target_mac


class Set8Challenge57(CryptoChallenge):
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.bob = DHMessageAuthenticator()
    
    def expected_value(self):
        return self.bob._get_secret_key()
    
    def value(self):
        attack = CustomSubgroupConfinementAttack(self.bob)
        return attack.recover_key()[0]