from collections import defaultdict

from common.attacks.hash.multicollisions import MulticollisionGenerator
from common.challenge import CryptoChallenge
from common.hash.tools.build import BasicHashFunctionFactory,\
                                    ComposedHashFunction
from common.tools.misc import AllEqual


class ComposedHashFunctionCollisionGenerator(object):
    
    def __init__(self, composed_hash):
        self.composed_hash = composed_hash
        self.weak_hash = composed_hash.functions[0]
        self.stronger_hash = composed_hash.functions[1]
        
    def _filter_collisions(self, collisions):
        hashes = defaultdict(lambda: list())
        for collision in collisions:
            collision_hash = self.composed_hash.hash(collision)
            collisions_for_hash = hashes[collision_hash]
            collisions_for_hash.append(collision)
            if len(collisions_for_hash) > 1:
                return collisions_for_hash
        return list()        
    
    def value(self):
        collision_generator = MulticollisionGenerator(self.weak_hash)
        state = None
        collisions = None
        # Generate 2**(target_bitsize/2) collisions; keep duplicating
        # if no collisions are found.
        n = self.stronger_hash.bits()/2
        while True:
            # On each step, duplicate the number of collisions. This is 
            # achieved by supplying previous collisions and state to the
            # multicollision generator.
            collisions, state = collision_generator.value(n, collisions, state)
            composed_hash_collisions = self._filter_collisions(collisions)
            if composed_hash_collisions:
                break
            n = 1
        return composed_hash_collisions


class Set7Challenge52(CryptoChallenge):
    
    def validate(self):
        weak_hash = BasicHashFunctionFactory.build(16)
        stronger_hash = BasicHashFunctionFactory.build(32)
        composed_hash = ComposedHashFunction(weak_hash, stronger_hash)
        
        collisions = ComposedHashFunctionCollisionGenerator(composed_hash).value()
        hashes = map(lambda message: composed_hash.hash(message), collisions)
        
        return AllEqual(hashes).value()