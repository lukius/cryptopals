from common.challenge import CryptoChallenge
from common.key_exchange.diffie_hellman import DiffieHellman


class Set5Challenge33(CryptoChallenge):
    
    P = 'ffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020'+\
        'bbea63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe135'+\
        '6d6d51c245e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5'+\
        'a899fa5ae9f24117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361c55'+\
        'd39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb9ed529077096966'+\
        'd670c354e4abc9804f1746c08ca237327ffffffffffffffff'
    G = 2
        
    def validate(self):
        p = int(self.P, 16)
        diffie_hellman1 = DiffieHellman(p, self.G)
        diffie_hellman2 = DiffieHellman(p, self.G)
        public_key1 = diffie_hellman1.get_public_key()
        public_key2 = diffie_hellman2.get_public_key()
        secret1 = diffie_hellman1.get_secret_from(public_key2)
        secret2 = diffie_hellman2.get_secret_from(public_key1)
        return secret1 == secret2