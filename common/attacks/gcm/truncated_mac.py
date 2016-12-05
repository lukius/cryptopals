from common.attacks.gcm import GCMAuthSubkeyRecoveryAttack


class TruncatedMACGCMAttack(GCMAuthSubkeyRecoveryAttack):
    
    def recover_key(self, ciphertext, tag):
        pass