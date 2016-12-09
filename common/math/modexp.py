from common.math.structures import Z_n


class ModularExp(object):
    
    def __init__(self, modulus):
        self.Z_n = Z_n(modulus)
        
    def value(self, base, exponent):
        return self.Z_n.pow(base, exponent)