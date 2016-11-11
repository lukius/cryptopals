import random

from common.math.modexp import ModularExp


class DiffieHellman(object):
    
    def __init__(self, p, g, g_order=None):
        self.p = p
        self.g = g
        self.modexp = ModularExp(self.p)
        self.exp = self._choose_secret_exponent(g_order or p)
        self.public_key = self._compute_public_key()
        
    def _choose_secret_exponent(self, g_order):
        return random.randint(1, g_order-1)
    
    def _compute_public_key(self):
        return self.modexp.value(self.g, self.exp)
        
    def get_public_key(self):
        return self.public_key
    
    def get_secret_from(self, key):
        return self.modexp.value(key, self.exp)
