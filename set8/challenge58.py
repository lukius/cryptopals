from common.attacks.discrete_log import PollardKangarooAttack,\
                                        EnhancedSubgroupConfinementAttack
from common.challenge import MatasanoChallenge
from common.math.modexp import ModularExp

from set8.misc import DHMessageAuthenticator, CustomMAC


class CustomSubgroupConfinementAttack(EnhancedSubgroupConfinementAttack):    

    def __init__(self, target):
        EnhancedSubgroupConfinementAttack.__init__(self,
                                                   target.p,
                                                   target.g,
                                                   target.q)
        self.target = target
        self.mac = CustomMAC()
        
    def _target_public_key(self):
        return self.target.get_public_key()
        
    def _key_is_valid(self, trial_key, h):
        # Send h to the target and receive the authenticated message.    
        msg, target_mac = self.target.get_authenticated_message(h)
        trial_mac = self.mac.value(trial_key)
        return trial_mac.value(msg) == target_mac
    

class Set8Challenge58(MatasanoChallenge):
    
    p = 11470374874925275658116663507232161402086650258453896274534991676898999262641581519101074740642369848233294239851519212341844337347119899874391456329785623
    q = 335062023296420808191071248367701059461
    g = 622952335333961296978159266084741085889881358738459939978290179936063635566740258555167783009058567397963466103140082647486611657350811560630587013183357
    
    y1 = 7760073848032689505395005705677365876654629189298052775754597607446617558600394076764814236081991643094239886772481052254010323780165093955236429914607119
    y2 = 9388897478013399550694114614498790691034187453089355259602614074132918843899833277397448144245883225611726912025846772975325932794909655215329941809013733
    
    def __init__(self):
        MatasanoChallenge.__init__(self)
        self.bob = DHMessageAuthenticator()
        
    def _validate(self):
        kangaroo_attack = PollardKangarooAttack(self.p, self.g)
        modexp = ModularExp(self.p)
        
        # First validation: index of y1.
        # y1_idx should be 705485.
        y1_idx = kangaroo_attack.get_index(self.y1, a=0, b=2**20)
        self._assert_equals(modexp.value(self.g, y1_idx), self.y1)
        
        # Second validation: index of y2.
        # y2_idx should be 359579674340.
        y2_idx = kangaroo_attack.get_index(self.y2, a=0, b=2**40)
        self._assert_equals(modexp.value(self.g, y2_idx), self.y2)        
        
        attack = CustomSubgroupConfinementAttack(self.bob)
        secret_key = self.bob._get_secret_key()
        key_recovered = attack.recover_key()
        self._assert_equals(secret_key, key_recovered)