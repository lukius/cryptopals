from common.challenge import CryptoChallenge
from common.tools.blockstring import BlockString
from common.mac.cbc import CBC_MAC
from common.tools.misc import RandomByteGenerator
from common.tools.padders import PKCS7Padder
from common.tools.xor import ByteXOR


class CBC_MACMessageForger(object):
    
    ACCOUNT_ID = 6
    TARGET_AMOUNT = 1000000
    
    def __init__(self, mac_generator):
        self.mac_generator = mac_generator
        self.block_size = self.mac_generator.block_size()
        
    def _build_fake_message_and_mac(self):
        transaction_dict = {self.ACCOUNT_ID : [0, self.TARGET_AMOUNT]}
        fake_message, fake_mac = self.mac_generator.\
                                 get_message_and_mac_for(self.ACCOUNT_ID,
                                                         transaction_dict)
        return fake_message, fake_mac
        
    def forge_from(self, message, mac):
        fake_message, fake_mac = self._build_fake_message_and_mac()
        fake_message = BlockString(fake_message, self.block_size)
        # Our new first block should be XORed with the original MAC. This, when
        # CBC-encrypted, will be like XORing the actual first block with a zero
        # IV.
        first_block = ByteXOR(fake_message.get_block(0), mac).value()
        # Remove first block; leave the rest untouched. 
        fake_message.remove_block(0)
        # PKCS7-pad original message (since CBC encryption does so).
        padded_message = PKCS7Padder(message).value(self.block_size)
        crafted_message = padded_message + first_block + fake_message.bytes()
        return crafted_message, fake_mac


class CBC_MACGenerator(object):
    
    MESSAGE_TEMPLATE = 'from=%d&tx_list=%s'
    
    def __init__(self, key):
        self.mac = CBC_MAC(key)
        
    def block_size(self):
        return self.mac.get_block_size()
        
    def get_message_and_mac_for(self, from_id, transaction_dict):
        transaction_list = ['%d:%d' % (item[0], amount)\
                            for item in transaction_dict.items()
                            for amount in item[1]]
        transactions = ';'.join(transaction_list)
        message = self.MESSAGE_TEMPLATE % (from_id, transactions)
        return message, self.mac.value(message)


class Set7Challenge49(CryptoChallenge):
    
    BLOCK_SIZE = 16
    VICTIM_ID = 1
    
    def validate(self):
        key = RandomByteGenerator().value(self.BLOCK_SIZE)
        mac_generator = CBC_MACGenerator(key)
        mac_validator = CBC_MAC(key)
        message, mac = mac_generator.get_message_and_mac_for(self.VICTIM_ID,
                                                             {2:[100]})
        # The MAC generator is only meant to be used to generate MACs for
        # "attacker-controlled" accounts.
        crafted_message, forged_mac = CBC_MACMessageForger(mac_generator).\
                                      forge_from(message, mac)
                                      
        from_victim = 'from=%d' % self.VICTIM_ID
        to_attacker = '%d:1000000' % CBC_MACMessageForger.ACCOUNT_ID
        return from_victim in crafted_message and\
               to_attacker in crafted_message and\
               mac_validator.validate(crafted_message, forged_mac)