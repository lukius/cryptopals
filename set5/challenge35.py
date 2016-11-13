from common.attacks.key_exchange import KeyExchangeProtocolMITMAttack
from common.challenge import CryptoChallenge
from common.key_exchange.protocols import KeyExchangeProtocol
from common.key_exchange.protocols.toy import KeyExchangeToyProtocolServer,\
                                              KeyExchangeToyProtocolClient


class KeyExchangeMITMAttackWithCustomG(KeyExchangeProtocolMITMAttack):
    
    def _inject_parameters_to_client(self):
        g = self._get_custom_g()
        self._send(g, socket=self.server_socket)
        self._send(self.p, socket=self.server_socket)
        # We send A = 1 in order to set client secret to 1.
        self._send(1, socket=self.server_socket)
        
    def _inject_client_public_key_to_server(self):
        self._send(self.B, socket=self.client_socket)
        
    def _build_message_from(self, message, secret):
        self._init_cipher_from(secret, self.iv)
        encrypted_message = self.cipher.encrypt(message,
                                                mode=self.cipher_mode)
        return encrypted_message.bytes()   
    
    def _get_server_message_from(self, iv_and_message):
        possible_server_secrets = self._get_possible_server_secrets()
        # Only one of these will succeed. The others will probably raise
        # invalid padding exceptions.
        for possible_secret in possible_server_secrets:
            try:     
                message = KeyExchangeProtocolMITMAttack.\
                          _decrypt_message(self,iv_and_message,
                                           possible_secret)
                self.server_secret = possible_secret
            except Exception:
                continue
            else:
                return message
        
    def _send_message_to_client(self, iv_and_message):
        self.iv = iv_and_message[:self.BLOCK_SIZE]
        self.message = self._get_server_message_from(iv_and_message)
        # Build encrypted message again, this time using the secret derived by
        # the client (which will be 1; see above).
        message = self._build_message_from(self.message, 1)
        self._send(self.iv+message, socket=self.server_socket)

    def _send_message_to_server(self, iv_and_message):
        # Encrypt expected message by server using its secret (already
        # found above).
        message = self._build_message_from(self.message[::-1],
                                           self.server_secret)
        self._send(message, socket=self.client_socket)
        
    def _decrypt_message(self, iv_and_message, secret):
        # Nothing to do since we already have the secret message.
        return self.message

    def _get_custom_g(self):
        raise NotImplementedError

    def _get_possible_server_secrets(self):
        raise NotImplementedError


class KeyExchangeMITMAttackWithGEquals1(KeyExchangeMITMAttackWithCustomG):
    
    def _get_custom_g(self):
        return 1
    
    def _get_possible_server_secrets(self):
        return [1]
    

class KeyExchangeMITMAttackWithGEqualsP(KeyExchangeMITMAttackWithCustomG):
    
    def _get_custom_g(self):
        return self.p

    def _get_possible_server_secrets(self):
        return [0]


class KeyExchangeMITMAttackWithGEqualsPMinus1(KeyExchangeMITMAttackWithCustomG):
    
    def _get_custom_g(self):
        return self.p - 1

    def _get_possible_server_secrets(self):
        return [1, self.p - 1]


class Set5Challenge35(CryptoChallenge):
    
    def _validate_attack(self, attack_class):
        client = KeyExchangeToyProtocolClient()
        attack = attack_class()
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

    def validate(self):
        attack_classes = [KeyExchangeMITMAttackWithGEquals1,\
                          KeyExchangeMITMAttackWithGEqualsP,\
                          KeyExchangeMITMAttackWithGEqualsPMinus1]
        
        return all(map(lambda attack_class: self._validate_attack(attack_class),
                       attack_classes))