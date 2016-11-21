import random

from common.hash.sha256 import SHA256
from common.math.group import Z_n
from common.math.invmod import ModularInverse
from common.math.modexp import ModularExp
from common.math.prime import RandPrime, is_prime
from common.signature import DigitalSignatureScheme


class AbstractDSA(DigitalSignatureScheme):
    
    # Based on Wikipedia pseudocode.
    
    def __init__(self, hash_function=SHA256, parameters=None):
        DigitalSignatureScheme.__init__(self)
        self.hash_function = hash_function()
        self._init_params_from(parameters)
        self._init_group()
        self._init_keys()
        
    def _init_params_from(self, parameters):
        if parameters is None:
            self.group_param, self.q, self.g = self._param_generator().generate()
        else:
            self.group_param, self.q, self.g = parameters
        
    def _init_keys(self):
        self.x = random.randint(1, self.q-1)
        self.y = self.group.pow(self.g, self.x)
        self.public_key = (self.group_param, self.q, self.g, self.y)
        
    def sign(self, message):
        h = self.hash_function.int_hash(message)
        while True:
            k = random.randint(1, self.q-1)
            r = self._to_int(self.group.pow(self.g, k)) % self.q
            if r == 0:
                continue
            k_inv = ModularInverse(self.q).value(k)
            s = k_inv*(h + self.x*r) % self.q
            if s != 0:
                break
        return r, s
    
    def verify(self, message, signature):
        r, s = signature
        if (r <= 0 or r >= self.q) or (s <= 0 or s >= self.q):
            return False
        h = self.hash_function.int_hash(message)
        w = ModularInverse(self.q).value(s)
        u1 = (h*w) % self.q
        u2 = (r*w) % self.q
        g_u1 = self.group.pow(self.g, u1)
        y_u2 = self.group.pow(self.y, u2)
        v_mod_p = self.group.add(g_u1, y_u2)
        v = self._to_int(v_mod_p) % self.q
        return r == v
    
    def _init_group(self):
        raise NotImplementedError
    
    def _param_generator(self):
        raise NotImplementedError
        
    def _to_int(self, z):
        raise NotImplementedError    

    
class DSA(AbstractDSA):
    
    def _init_group(self):
        self.group = Z_n(self.group_param)
        
    def _param_generator(self):
        return DSAParameterGenerator
        
    def _to_int(self, z):
        return z
    
    
class ECDSA(AbstractDSA):
    
    def _init_group(self):
        # group_param is just the elliptic curve.
        self.group = self.group_param
        
    def _param_generator(self):
        # TBD
        raise NotImplementedError        
        
    def _to_int(self, z):
        return z.x    
    
    
class DSAParameterGenerator(object):
    
    DEFAULT_L = 2048
    DEFAULT_N = 256
    DEFAULT_H = 2
    
    def __init__(self, L=None, N=None):
        self.prime_generator = RandPrime()
        self.L = self.DEFAULT_L if L is None else L
        self.N = self.DEFAULT_N if N is None else N
        
    def _choose_p_from(self, q):
        i = 2
        while True:
            p = i*q + 1
            # TODO: implement Miller-Rabin
            if is_prime(p):
                break
            i += 1
        return p
                
    def _choose_g_from(self, p, q):
        h = self.DEFAULT_H
        while True:
            g = ModularExp(p).value(h, (p-1)/q)
            if g != 1:
                break
        return g
    
    def generate(self):
        q = self.prime_generator.value(self.N)
        p = self._choose_p_from(q)
        g = self._choose_g_from(p, q)
        return p, q, g