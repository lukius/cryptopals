from common.attacks.hash.md4 import MD4CollisionGenerator
from common.challenge import CryptoChallenge
from common.hash.md4 import MD4


class Set7Challenge55(CryptoChallenge):
    
    def validate(self):
        md4 = MD4()
        collisions = MD4CollisionGenerator().value()
        return md4.hash(collisions[0]) == md4.hash(collisions[1])