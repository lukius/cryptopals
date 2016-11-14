from common.math.invmod import ModularInverse


class AbstractGroup(object):
    
    def identity(self):
        raise NotImplementedError
    
    def add(self, a, b):
        raise NotImplementedError
    
    def pow(self, a, n):
        result = self.identity()
        while n > 0:
            if n % 2 == 1:
                result = self.add(result, a)
            n >>= 1
            a = self.add(a, a)
        return result
    
    def invert(self, a):
        raise NotImplementedError
    
    
class Z_n(AbstractGroup):
    
    def __init__(self, n):
        self.n = n
        
    def identity(self):
        return 1
    
    def add(self, a, b):
        return (a*b) % self.n
    
    def invert(self, a):
        # Assuming gcd(a,n) = 1.
        return ModularInverse(self.n).value(a)