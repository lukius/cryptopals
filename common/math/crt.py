from common.math.invmod import ModularInverse
from common.tools.misc import Product


class ChineseRemainderTheorem(object):
    
    # Chinese Remainder Theorem custom implementation.
    # Solves systems of linear congruences
    #   x = r_i mod n_i
    # where n_1,...,n_k are coprime.
    # Solution is given modulo n_1 * ... * n_k.
    
    def solve(self, remainders, moduli):
        if len(remainders) != len(moduli):
            raise Exception
        
        N = Product(moduli).value()
        x = 0
        
        for i in xrange(len(moduli)):
            r_i = remainders[i]
            n_i = moduli[i]
            N_i = N/n_i
            M_i = ModularInverse(n_i).value(N_i)
            x += r_i * M_i * N_i
            
        return x % N, N