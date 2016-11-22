from common.ciphers.pubkey.rsa import RSA
from common.math.crt import ChineseRemainderTheorem
from common.math.factor import SieveBasedSmoothNumberGenerator
from common.math.invmod import ModularInverse
from common.math.modexp import ModularExp
from common.tools.converters import BytesToInt
from common.tools.misc import ByteSize


class FixedRSA(RSA):
    
    def __init__(self, e, n, d):
        self.e = e
        self.n = n
        self.d = d
        RSA.__init__(self)
        
    def _init_parameters(self, bits):
        self.modexp = ModularExp(self.n)
        self.public_key = (self.e, self.n) 


class RSAKeyDuplicationAttack(object):
    
    SMOOTHNESS_FACTOR = 2**16
    
    def __init__(self, rsa):
        self.rsa = rsa
        self.e, self.n = rsa.get_public_key()
        self.n_size = ByteSize(self.n).value()
        # Generator of prime numbers with the desired properties.
        self.generator = SieveBasedSmoothNumberGenerator(self.SMOOTHNESS_FACTOR)
        
    def _pad(self, message):
        return message

    def _is_primitive_root(self, x, p, factors):
        modexp = ModularExp(p)
        for q in factors:
            if modexp.value(x, (p-1)/q) == 1:
                return False
        return True
    
    def _generate_primes(self, m, s, bitsize):
        while True:
            while True:
                p_1, p_factors = self.generator.value(bitsize)
                p = p_1 + 1
                if self._is_primitive_root(m, p, p_factors) and\
                   self._is_primitive_root(s, p, p_factors):
                    break
            while True:    
                q_1, q_factors = self.generator.value(bitsize,
                                                      banned_primes=p_factors[1:])
                q = q_1 + 1
                if self._is_primitive_root(m, q, q_factors) and\
                   self._is_primitive_root(s, q, q_factors):
                    break
            if ByteSize(p*q).value() == self.n_size and\
               p*q > self.n:
                break
        return p, p_factors, q, q_factors
    
    def _discrete_log(self, m, s, p, factors):
        # Find e such that s^e = m mod p using the Pohlig-Hellman algorithm.
        rems = list()
        mods = list()
        modexp = ModularExp(p)
        for q in factors:
            u = (p-1)/q
            s_u = modexp.value(s, u)
            for k in xrange(q):
                if modexp.value(s_u,k) == modexp.value(m, u):
                    rems.append(k)
                    mods.append(q)
        return rems, mods
        
    def generate_key(self, plaintext, ciphertext):
        pad_m = self._pad(plaintext)
        m = BytesToInt(pad_m).value()
        s = BytesToInt(ciphertext).value()
        # Target bitsize of p and q.
        bitsize = self.n_size*4
        while True:
            # Find primes p and q such that p-1 and q-1 are k-smooth numbers with
            # a "small" k (given by self.SMOOTHNESS_FACTOR). Also, p-1 and q-1
            # should not share prime factors other than 2. And m and s should be
            # primitive roots modulo p and modulo q.
            p, p_factors, q, q_factors = self._generate_primes(m, s, bitsize)
            rems_p, mods_p = self._discrete_log(m, s, p, p_factors)
            rems_q, mods_q = self._discrete_log(m, s, q, q_factors)

            # Fail if remainder modulo 2 is not the same.
            if rems_p[0] != rems_q[0]:
                continue
            
            # All checks passed. Now use CRT to assemble the whole thing.
            rems = rems_p + rems_q[1:]
            mods = mods_p + mods_q[1:]
            new_e, _ = ChineseRemainderTheorem().solve(rems, mods)
            new_N = p*q
            new_d = ModularInverse((p-1)*(q-1)).value(new_e)

            return new_e, new_N, new_d
        
    def duplicate(self, plaintext, ciphertext):
        e, N, d = self.generate_key(plaintext, ciphertext)
        return FixedRSA(d, N, e)
    
    
class RSASignatureKeySelectionAttack(RSAKeyDuplicationAttack):
        
    def _pad(self, message):
        # self.rsa is actually an RSA-based digital signature object.
        return self.rsa._encode(message)