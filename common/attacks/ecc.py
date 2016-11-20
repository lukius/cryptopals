import random
import threading

from common.attacks.discrete_log.kangaroo import StoppableECKangarooAttack
from common.math.crt import ChineseRemainderTheorem
from common.math.prime import Primes, is_prime
from common.math.modexp import ModularExp
from common.tools.converters import IntToBinary
from common.tools.padders import LeftPadder


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
    
    
class InsecureTwistAttack(object):
    
    MAX_P = 2**24
    
    def __init__(self, curve, order, G, G_order):
        self.curve = curve
        self.order = order
        self.G = G
        self.G_order = G_order
        
    def _get_twist_order(self):
        return 2*self.curve.p + 2 - self.order
    
    def _y_is_quadratic_residue(self, x):
        # Use the Legendre symbol, which should be 1.
        p = self.curve.p
        y = self.curve.y_sq_from_x(x)
        return ModularExp(p).value(y, (p-1)/2) == 1
    
    def _point_of_order(self, d, n):
        while True:
            x = random.randint(0, self.curve.p-1)
            if self._y_is_quadratic_residue(x):
                continue
            x = self.curve.ladder(x, n/d)
            if x != 0:
                return x
    
    def _get_remainder_for(self, p, n):
        # p is the small factor of n we are targeting now.
        # n is the quadratic twist curve order.
        x = self._point_of_order(p, n)
            
        # Guess the remainder by brute-forcing its possible values.
        for k in xrange(p):
            trial_key = self.curve.ladder(x, k)
            if self._key_is_valid(trial_key, x):
                return k, p-k
    
    def _get_remainders(self):
        moduli = list()
        remainders = list()
        # n is the order of the quadratic twist curve.
        n = self._get_twist_order()
        n1 = n
        m = 1
        for p in Primes():
            if p > self.MAX_P or\
               (n1 > self.MAX_P and is_prime(n1)):
                break
            if n1 % (p*p) == 0:
                while n1%p == 0:
                    n1 /= p
                continue
            if n1 % p == 0:
                # For each factor p, compute the remainder
                #   b = x mod p (where x is the target's key)
                b = self._get_remainder_for(p, n)
                moduli.append(p)
                remainders.append(b)
                m *= p
                n1 /= p
                if m >= self.G_order:
                    break
        return remainders, moduli
    
    def _get_key_mod_N_candidates(self, remainders, moduli):
        # Finds x1, x2 mod N in the remainders such that
        #   ladder(z, xi) = target.secret(z)
        # for a point z of order N (x is the target's key).
        crt = ChineseRemainderTheorem()
        k = len(moduli)
        n = 2**k
        candidates = list()

        # Actually done for two points.
        z1, z2 = None, None
        
        for i in xrange(n):
            # Select remainders given by binary representation of i.
            bin_i = LeftPadder(IntToBinary(i).value()).value(k, char='0')
            rems = map(lambda (j,r): r[int(bin_i[j])],
                       enumerate(remainders))
            
            x_N, N = crt.solve(rems, moduli)
            
            z1 = z1 or self._point_of_order(N, self._get_twist_order())
            z2 = z2 or self._point_of_order(N, self._get_twist_order())
            s1 = self.curve.ladder(z1, x_N)
            if s1 == self.target.get_secret_from(z1):
                s2 = self.curve.ladder(z2, x_N)
                if s2 == self.target.get_secret_from(z2):
                    candidates.append(x_N)
                    
        return candidates, N
    
    def recover_key(self):
        remainders, moduli = self._get_remainders()
        # Since we have a small number of factors for the challenge, we can do
        # this after processing the whole thing. Otherwise, we should be doing
        # this several times in the middle to avoid dealing with a large space
        # of possibilities (each factor doubles the size of the space).
        xs, N = self._get_key_mod_N_candidates(remainders, moduli)
        
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.key = None
        workers = list()
        
        for x in xs:
            worker = KangarooWorker(self)
            worker.start(x, N)
            workers.append(worker)
            
        finished = 0
        while self.key is None and finished < len(workers):
            self.event.wait()
            with self.lock:
                self.event.clear()
                finished += 1
            
        if self.key is not None:
            map(lambda worker: worker.stop(), workers)

        return self.key
            
                
class KangarooWorker(object):
    
    def __init__(self, owner):
        self.owner = owner
        self.index = None
        
    def start(self, x, N):
        self.thread = threading.Thread(target=self._start,
                                       args=(x,N))
        self.thread.daemon = True
        self.thread.start()
        
    def _start(self, x, N):
        key_x = self.owner._target_public_key()
        key_y = self.owner.curve.y_from_x(key_x)
        Y = self.owner.curve.point(key_x, key_y)
        G_x = x * self.owner.G
        Y_prime = Y + self.owner.curve.invert(G_x)
        G_prime = N * self.owner.G

        self.attack = StoppableECKangarooAttack(G_prime, self.owner.G_order)
        index = self.attack.get_index(Y_prime, a=0, b=self.owner.G_order/N)
        
        if index is not None:
            key = x + self.index * N
            if self.owner.curve.ladder(self.owner.G.x, key) == key_x:
                self.owner.key = key
        
        with self.owner.lock:        
            self.owner.event.set()
    
    def stop(self):
        self.attack.stop()