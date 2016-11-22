from common.attacks.rsa.oracle import RSAOracle, RSAOracleAttack
from common.tools.padders import LeftPadder, PKCS1_5Unpadder
from common.tools.misc import ByteSize


class PKCS1_5PaddingOracle(RSAOracle):
    
    def __init__(self, rsa):
        RSAOracle.__init__(self, rsa)
        n = self.rsa.get_public_key()[1]
        self.n_size = ByteSize(n).value()
    
    def has_valid_padding(self, ciphertext):
        plaintext = self.rsa.decrypt(ciphertext)
        plaintext = LeftPadder(plaintext).value(self.n_size, char='\0')
        return plaintext[0] == '\x00' and plaintext[1] == '\x02'


class PKCS1_5PaddingOracleAttack(RSAOracleAttack):

    # Implementation of Bleinchenbacher's adaptive chosen-ciphertext
    # attack against PKCS1.5-padded RSA (a.k.a. "million message" attack).
    
    def __init__(self, oracle):
        RSAOracleAttack.__init__(self, oracle)
        self.k = ByteSize(self.n).value()
        self.B = 2**(8*(self.k-2))
    
    def _init_M(self):
        interval = PaddingOracleInterval(2*self.B, 3*self.B-1)
        M = PaddingOracleIntervalSet()
        M.add(interval)
        return M
    
    def _plaintext_was_found(self, M):
        return len(M) == 1 and M[0].low() == M[0].high()
    
    def _s_works(self, c, s):
        c_prime = self._build_ciphertext_from(c, s)
        return self.oracle.has_valid_padding(c_prime)
    
    def _search_s_from(self, lower_bound, c):
        s = lower_bound
        while not self._s_works(c, s):
            s += 1
        return s
    
    def _search_s_for_r(self, c, r, a, b):
        # Every lim unsuccessful iterations, increase current s value by a
        # constant factor. Backing off exponentially, as it is done for r
        # values below, might make s too high, which in turn stops the loop
        # too soon.
        i = 1        
        lim = 1000
        low_s = self._divide_and_round_up(2*self.B + r*self.n, b)
        high_s = self._divide_and_round_up(3*self.B + r*self.n, a)
        new_s = low_s
        while new_s < high_s:
            if self._s_works(c, new_s):
                return new_s
            if i % lim == 0:
                new_s += 100000
            new_s += 1
            i += 1
        return None
            
    def _search_s_with_one_interval(self, c, s, a, b):
        # Every lim unsuccessful iterations, back off r. A small value proved
        # to be satisfactory. Larger values will usually make the algorithm
        # run for very long periods of time.
        i = 1 
        lim = 100
        r = (2*(b*s - 2*self.B)) / self.n
        while True:
            new_s = self._search_s_for_r(c, r, a, b)
            if new_s is not None:
                return new_s
            if i % lim == 0:
                r *= 2
            r += 1
            i += 1
            
    def _find_next_s(self, M, c, s):
        if len(M) > 1:
            s = self._search_s_from(s+1, c)
        else:
            a, b = M[0].low(), M[0].high()
            s = self._search_s_with_one_interval(c, s, a, b)
        return s
    
    def _interval_is_well_defined(self, low, high):
        return low <= high and low >= 2*self.B and high < 3*self.B
    
    def _divide_and_round_up(self, dividend, divisor):
        q = dividend / divisor
        result = q
        if q*divisor < dividend:
            result += 1
        return result
            
    def _narrow_intervals(self, M, s):
        new_M = PaddingOracleIntervalSet()
        for interval in M:
            a, b = interval.low(), interval.high()
            low_r = (a*s - 3*self.B + 1) / self.n
            high_r = (b*s - 2*self.B) / self.n
            r = low_r
            while r <= high_r:
                low = self._divide_and_round_up(2*self.B + r*self.n, s)
                interval_low = max(a, low)
                high = (3*self.B - 1 + r*self.n) / s
                interval_high = min(b, high)
                if self._interval_is_well_defined(interval_low, interval_high):
                    interval = PaddingOracleInterval(interval_low,
                                                     interval_high)
                    new_M.add(interval)
                r += 1
        return new_M
        
    def _decrypt(self, c):
        # Called from decrypt template method (superclass)
        M = self._init_M()
        s = self._search_s_from(self.n/(3*self.B), c)
        while True:
            M = self._narrow_intervals(M, s)
            if self._plaintext_was_found(M):
                break
            s = self._find_next_s(M, c, s)
        return M[0].low()
    
    def decrypt(self, ciphertext):
        plaintext = RSAOracleAttack.decrypt(self, ciphertext)
        return PKCS1_5Unpadder(self.k).value(plaintext)


class PaddingOracleIntervalSet(object):
    
    def __init__(self):
        self.M = list()
        
    def add(self, interval):
        M = [interval]
        for _interval in self.M:
            if interval.includes(_interval):
                return
            if not _interval.includes(interval):
                M.append(_interval)
        self.M = M
    
    def __len__(self):
        return len(self.M)
    
    def __getitem__(self, i):
        if i >= len(self):
            raise IndexError('index out of range')
        return self.M[i]
    
    def __iter__(self):
        return iter(self.M)
    
    def next(self):
        return self.M.next()
    

class PaddingOracleInterval(object):
    
    def __init__(self, a, b):
        self.a = a
        self.b = b
        
    def low(self):
        return self.a
    
    def high(self):
        return self.b
    
    def includes(self, interval):
        return self.a <= interval.low() and interval.high() <= self.b
    
    def __eq__(self, interval):
        if not isinstance(interval, self.__class__):
            return False
        return self.a == interval.low() and self.b == interval.high()
        
    def __hash__(self):
        return hash((self.a, self.b))
