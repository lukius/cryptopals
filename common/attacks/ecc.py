from common.math.crt import ChineseRemainderTheorem
from common.math.prime import Primes


class InvalidCurveAttack(object):
    
    # TODO: refactor and share common structure with the subgroup confinement
    # attack.
    
    # If a factor exceeds this value, we stop the attack. We won't be able
    # to brute-force the key anymore.
    MAX_P = 2**16
    
    def __init__(self, curve, q):
        self.curve = curve
        self.q = q
        
    def _get_remainder_for(self, invalid_curve, order, p):
        # Get a point P such that p * P = O.
        while True:
            P = invalid_curve.rand_point()
            P = (order/p) * P
            if P != invalid_curve.identity():
                break
            
        # Guess the remainder by brute-forcing its possible values.
        for k in xrange(p):
            trial_key = k * P
            if self._key_is_valid(trial_key, P):
                return k
        
    def _get_remainders(self, invalid_curves):
        moduli = list()
        remainders = list()
        m = 1
        for (invalid_curve, order) in invalid_curves:
            for p in Primes():
                if p > self.MAX_P:
                    break
                if order % p == 0 and order % (p*p) != 0 and\
                   p not in moduli:
                    # For each factor p, compute the remainder
                    #   b = x mod p (where x is the target's key)
                    b = self._get_remainder_for(invalid_curve, order, p)
                    moduli.append(p)
                    remainders.append(b)
                    m *= p
                    if m >= self.q:
                        return remainders, moduli
        
    def _get_key(self, remainders, moduli):
        # Last step: use CRT to solve 
        #  x = remainders_i mod moduli_i
        x, N = ChineseRemainderTheorem().solve(remainders, moduli)
        if N > self.q:
            return x % self.q, self.q
        else:
            return x, N
        
    def recover_key(self, invalid_curves):
        # invalid_curves is a list of tuples (curve, order) to use during the
        # attack.
        remainders, moduli = self._get_remainders(invalid_curves)
        return self._get_key(remainders, moduli)
    
    def _key_is_valid(self, trial_key, P):
        raise NotImplementedError