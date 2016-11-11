import socket
import threading

from common.ciphers.block.aes import AES
from common.ciphers.block.modes import CBC
from common.hash.sha1 import SHA1
from common.key_exchange.diffie_hellman import DiffieHellman
from common.tools.converters import BytesToInt, IntToBytes
from common.tools.misc import Concatenation, RandomByteGenerator


class KeyExchangeProtocol(object):
    
    MAX_INT = 2**64 - 1
    LENGTH_FIELD_SIZE = 4
    BLOCK_SIZE = 16
    
    STATUS_RUNNING = 0
    STATUS_OK = 1
    STATUS_ERROR = 2
    
    P = 'ffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020'+\
        'bbea63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe135'+\
        '6d6d51c245e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5'+\
        'a899fa5ae9f24117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361c55'+\
        'd39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb9ed529077096966'+\
        'd670c354e4abc9804f1746c08ca237327ffffffffffffffff'
    G = 2    
    
    def __init__(self):
        self.socket = socket.socket()
        self.thread = threading.Thread(target=self._run)
        self.p = int(self.P, 16)
        self.status = self.STATUS_RUNNING
        
    def _init_diffie_hellman_from(self, p, g):
        self.diffie_hellman = DiffieHellman(p, g)        
        
    def _receive(self, socket=None):
        socket = socket if socket is not None else self.socket
        size_bytes = socket.recv(self.LENGTH_FIELD_SIZE)
        size = BytesToInt(size_bytes).value()
        return socket.recv(size)
    
    def _receive_int(self, socket=None):
        integer = self._receive(socket)
        return int(integer)    
    
    def _send(self, *values, **kwargs):
        message = Concatenation(map(str, values)).value()
        size_bytes = IntToBytes(len(message)).value(self.LENGTH_FIELD_SIZE)
        socket = kwargs['socket']\
                 if 'socket' in kwargs and kwargs['socket'] is not None\
                 else self.socket
        socket.send(size_bytes + message)
        
    def get_status(self):
        return self.status
        
    def start(self):
        self.thread.start()
        
    def stop(self):
        self.thread.join()


class KeyExchangeProtocolServer(KeyExchangeProtocol):
    
    ADDRESS = '127.0.0.1'
    PORT = 20100
    
    def __init__(self):
        KeyExchangeProtocol.__init__(self)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ADDRESS, self.PORT))
        self.socket.listen(1)
        self._init_diffie_hellman_from(self.p, self.G)
        
    def _accept_connection(self):
        self.socket, _ = self.socket.accept()
        

class KeyExchangeProtocolClient(KeyExchangeProtocol):

    def __init__(self):
        KeyExchangeProtocol.__init__(self)
        self.server_address = KeyExchangeProtocolServer.ADDRESS
        self.server_port = KeyExchangeProtocolServer.PORT
    
    def _connect(self):
        self.socket.connect((self.server_address, self.server_port))