from common.attacks.mac import TimeLeakBasedHMACCracker
from common.challenge import CryptoChallenge
from common.hash.sha1 import SHA1
from common.mac.hmac import HMAC
from common.tools.misc import RandomByteGenerator, Average
from common.attacks.tools.timeleak import TimeLeakingWebServer


class HMACCrackerForReducedTimeLeak(TimeLeakBasedHMACCracker):
    
    REQUEST_ATTEMPTS = 50
    
    def _compute_score_for(self, hmac):
        times = [self._measure_request_time_for(hmac)\
                 for _ in range(self.REQUEST_ATTEMPTS)]
        return Average(times).value()
    

class Set4Challenge32(CryptoChallenge):
    
    STRING = 'foo bar baz'
    KEY = RandomByteGenerator().value(50)
    TIMING_LEAK = 0.003
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.hmac = HMAC(self.KEY, SHA1).value(self.STRING)
    
    def expected_value(self):
        return self.hmac
    
    def value(self):
        with TimeLeakingWebServer(self.STRING, self.hmac, self.TIMING_LEAK)\
             as server:
            return HMACCrackerForReducedTimeLeak(server).crack()