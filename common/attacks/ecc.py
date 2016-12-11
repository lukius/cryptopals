import random

from common.attacks.discrete_log.kangaroo import EllipticCurveKangarooAttack
from common.math.crt import ChineseRemainderTheorem
from common.math.prime import Primes, is_prime
from common.math.modexp import ModularExp
from common.tools.concurrency import ConcurrentTask, ConcurrentTaskManager
from common.tools.converters import IntToBinary
from common.tools.padders import LeftPadder


class InvalidCurveAttack(object):
    
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
    
    def _point_of_order(self, d, i, n):
        while True:
            x = random.randint(0, self.curve.p-1)
            if self._y_is_quadratic_residue(x):
                continue
            x = self.curve.ladder(x, n/(d**i))
            if x != 0:
                return x
    
    def _get_remainders_for(self, p, i, n):
        # p is the small factor of n we are targeting now.
        # n is the quadratic twist curve order.
        # i is the highest integer j such that p^j | n.
        x = self._point_of_order(p, i, n)
            
        # Guess the remainder by brute-forcing its possible values.
        for k in xrange(p):
            trial_key = self.curve.ladder(x, k)
            if self._key_is_valid(trial_key, x):
                return k, (p-k)%p
    
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
            if n1 % p == 0:
                i = 0
                while n1%p == 0:
                    n1 /= p
                    i += 1
                # For each factor p, compute the remainders
                #   b1 =  x mod p
                #   b2 = -x mod p
                # where x is the target's key (we need to track both because of
                # the single-coordinate ladder).
                b = self._get_remainders_for(p, i, n)
                moduli.append(p)
                remainders.append(b)
                m *= p
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
            
            z1 = z1 or self._point_of_order(N, 1, self._get_twist_order())
            z2 = z2 or self._point_of_order(N, 1, self._get_twist_order())
            s1 = self.curve.ladder(z1, x_N)
            if s1 == self.target.get_secret_from(z1):
                s2 = self.curve.ladder(z2, x_N)
                if s2 == self.target.get_secret_from(z2):
                    candidates.append(x_N)
                    
        return set(candidates), N
    
    def _get_base_points(self):
        key_x = self._target_public_key()
        y1 = self.curve.y_from_x(key_x)
        G1 = self.curve.point(key_x, y1)
        G2 = G1.invert()
        return G1, G2
    
    def _run_tasks(self, tasks):
        if len(tasks) > ConcurrentTaskManager.DEFAULT_WORKERS:
            # Not enough cores for launching them in parallel.
            for task in tasks:
                task.run()
                result = task.result()
                if result is not None:
                    return result
        else:
            with ConcurrentTaskManager() as task_manager:
                winner_task = task_manager.compete(tasks)
    
            return winner_task.result()
    
    def recover_key(self):
        remainders, moduli = self._get_remainders()
        # Since we have a small number of factors for the challenge, we can do
        # this after processing the whole thing. Otherwise, we should be doing
        # this several times in the middle to avoid dealing with a large space
        # of possibilities (each factor doubles the size of the space).
        xs, N = self._get_key_mod_N_candidates(remainders, moduli)
        
        # The ladder only works with the x coordinate of the points. As the
        # kangaroo algorithm uses the elliptic curve addition, we also need
        # the y coordinate. But we have two candidate base points G.
        Gs = self._get_base_points()
        
        # We should have two candidates of the key mod N. We now launch four
        # instances of the kangaroo algorithm combining each G and each x.
        tasks = [KangarooAttackTask(self, G, x, N) for x in xs
                                                   for G in Gs]
        
        return self._run_tasks(tasks)
            

class KangarooAttackTask(ConcurrentTask):
    
    def __init__(self, parent, point, x, N):
        ConcurrentTask.__init__(self)
        self.parent = parent
        self.x = x
        self.N = N
        self.point = point
        
    def result(self):
        return self.queue.get()
        
    def run(self):
        Y = self.point
        G_x = self.x * self.parent.G
        Y_prime = Y + self.parent.curve.invert(G_x)
        G_prime = self.N * self.parent.G

        attack = EllipticCurveKangarooAttack(G_prime, self.parent.G_order)
        index = attack.get_index(Y_prime, a=0, b=self.parent.G_order/self.N)
        
        result = None
        if index is not None:
            key = self.x + index * self.N
            if self.parent.curve.ladder(self.parent.G.x, key) == self.point.x:
                result = key
        
        self.queue.put(result)