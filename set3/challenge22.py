import random
import time

from common.challenge import CryptoChallenge
from common.random.mt19937 import MersenneTwister


class Clock(object):
    
    _timestamp = int(time.time())
    
    @classmethod
    def advance(cls, seconds):
        cls._timestamp += seconds
    
    @classmethod
    def now(cls):
        return cls._timestamp
        

class MersenneTwisterSeedCracker(object):
    
    # Maximum number of seconds in the past where we expect to find the seed.
    MAX_SECONDS = 5000

    def _seed_generates_output(self, integer, seed):
        prng = MersenneTwister(seed)
        return integer == prng.rand()
    
    def value(self, integer):
        current_time = Clock.now()
        for i in range(self.MAX_SECONDS):
            seed = current_time - i
            if self._seed_generates_output(integer, seed):
                return seed


class Set3Challenge22(CryptoChallenge):
    
    MIN_SLEEP_SECONDS = 50
    MAX_SLEEP_SECONDS = 2000
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.seed = self._get_seed()
        self.output = self._get_output()
        self._advance_clock()
    
    def _get_seed(self):
        return Clock.now()
    
    def _get_output(self):
        return MersenneTwister(self.seed).rand()

    def _advance_clock(self):
        seconds = random.randint(self.MIN_SLEEP_SECONDS,
                                    self.MAX_SLEEP_SECONDS)
        Clock.advance(seconds)
    
    def expected_value(self):
        return self.seed
        
    def value(self):
        return MersenneTwisterSeedCracker().value(self.output)