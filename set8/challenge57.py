import random

from common.challenge import MatasanoChallenge
from common.hash.sha256 import SHA256
from common.key_exchange.diffie_hellman import DiffieHellman
from common.mac.hmac import HMAC
from common.tools.converters import IntToBytes
from common.math.prime import Primes
from common.math.modexp import ModularExp
from common.math.crt import ChineseRemainderTheorem


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
    
    
class PohligHellmannAttack(object):
    
    def __init__(self, target):
        self.target = target
        self.modexp = ModularExp(self.target.p)
        self.mac = CustomMAC()
        
    def _get_remainder_for(self, r):
        # Get an h such that h^r = 1 mod p (due to Euler's Theorem).
        while True:
            h = random.randint(1, self.target.p-1)
            h = self.modexp.value(h, (self.target.p-1)/r)
            if h != 1:
                break
            
        # Send h to the target and receive the authenticated message.    
        msg, target_mac = self.target.get_authenticated_message(h)
        
        # Finally, guess the remainder by brute-forcing its possible values.
        for k in xrange(r):
            trial_key = self.modexp.value(h, k)
            trial_mac = self.mac.value(trial_key)
            if trial_mac.value(msg) == target_mac:
                return k
        
    def _get_remainders(self):
        moduli = list()
        remainders = list()
        j = (self.target.p - 1) / self.target.q
        m = 1
        # Find factors of j = (p-1)/q
        for p in Primes():
            if j % p == 0 and j % (p*p) != 0:
                # For each factor p, compute the remainder
                #   b = x mod p (where x is the target's key)
                b = self._get_remainder_for(p)
                moduli.append(p)
                remainders.append(b)
                m *= p
                if m >= self.target.q:
                    break
        return remainders, moduli
        
    def _get_key(self, remainders, moduli):
        # Last step: use CRT to solve 
        #  x = remainders_i mod moduli_i
        crt = ChineseRemainderTheorem()
        x = crt.solve(remainders, moduli)
        return x % self.target.q
        
    def recover_key(self):
        remainders, moduli = self._get_remainders()
        return self._get_key(remainders, moduli)


class Set8Challenge57(MatasanoChallenge):
    
    def __init__(self):
        MatasanoChallenge.__init__(self)
        self.bob = DHMessageAuthenticator()
    
    def expected_value(self):
        return self.bob._get_secret_key()
    
    def value(self):
        attack = PohligHellmannAttack(self.bob)
        return attack.recover_key()