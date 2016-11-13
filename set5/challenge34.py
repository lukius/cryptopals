from common.attacks.key_exchange import KeyExchangeProtocolMITMAttack
from common.challenge import CryptoChallenge
from common.key_exchange.protocols import KeyExchangeProtocol
from common.key_exchange.protocols.toy import KeyExchangeToyProtocolServer,\
                                              KeyExchangeToyProtocolClient


class Set5Challenge34(CryptoChallenge):
    
    def validate(self):
        client = KeyExchangeToyProtocolClient()
        attack = KeyExchangeProtocolMITMAttack()
        server = KeyExchangeToyProtocolServer()
        
        server.start()
        client.start()
        client.stop()
        server.stop()
        attack.stop()
        
        message = attack.get_message()
        
        return message == KeyExchangeToyProtocolServer.MESSAGE and\
               client.get_status() == KeyExchangeProtocol.STATUS_OK and\
               server.get_status() == KeyExchangeProtocol.STATUS_OK 