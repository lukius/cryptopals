from common.challenge import CryptoChallenge
from common.random.mt19937 import MersenneTwister


class MersenneTwisterClone(MersenneTwister):
    
    def __init__(self, state):
        self.state = state
        self.index = 0


class MersenneTwisterCloner(object):
    
    def _invert_fourth_transformation(self, integer):
        return integer ^ (integer >> 18)
    
    def _invert_third_transformation(self, integer):
        return integer ^ ((integer << 15) & 4022730752)
    
    def _invert_second_transformation(self, integer):
        # Bitmask i will project bits 7i,...,min(7i+6, 31).
        bitmasks = [0x0000007f, 0x00003f80, 0x001fc000, 0x0fe00000, 0xf0000000]
        result = 0
        for bitmask in bitmasks:
            anded = (result << 7) & 2636928640
            bits = (integer ^ anded) & bitmask
            result ^= bits
        return result
    
    def _invert_first_transformation(self, integer):
        return integer ^ (integer >> 11) ^ (integer >> 22)
    
    def _get_state_value_for(self, integer):
        integer = self._invert_fourth_transformation(integer)
        integer = self._invert_third_transformation(integer)
        integer = self._invert_second_transformation(integer)
        integer = self._invert_first_transformation(integer)
        return integer
    
    def clone(self, prng):
        state = list()
        for _ in range(MersenneTwister.STATE_SIZE):
            integer = prng.rand()
            state_value = self._get_state_value_for(integer)
            state.append(state_value)
        return MersenneTwisterClone(state)


class Set3Challenge23(CryptoChallenge):
    
    SEED = 100
    INTS = MersenneTwister.STATE_SIZE
    
    def __init__(self):
        CryptoChallenge.__init__(self)
        self.prng = MersenneTwister(seed=self.SEED)
    
    def _values_for(self, prng):
        return [prng.rand() for _ in range(self.INTS)]
    
    def expected_value(self):
        return self._values_for(self.prng)
    
    def value(self):
        cloned_prng = MersenneTwisterCloner().clone(self.prng)
        return self._values_for(cloned_prng)