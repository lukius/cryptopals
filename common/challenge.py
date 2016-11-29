class ChallengeFailure(Exception):
    
    pass


class CryptoChallenge(object):
    
    def expected_value(self):
        raise NotImplementedError
    
    def value(self):
        raise NotImplementedError
    
    def _assert_raises(self, exception, method):
        try:
            method()
        except exception:
            pass
        else:
            raise ChallengeFailure
        
    def _assert_equals(self, a, b):
        if a != b:
            raise ChallengeFailure
        
    def _assert_not_equals(self, a, b):
        if a == b:
            raise ChallengeFailure        
        
    def _assert_true(self, a):
        if not a:
            raise ChallengeFailure
        
    def _assert_false(self, a):
        if a:
            raise ChallengeFailure
        
    def _assert_in(self, a, values):
        for value in values:
            if a == value:
                return
        raise ChallengeFailure    
    
    def _validate(self):
        value = self.value()
        expected_value = self.expected_value()
        return value == expected_value
    
    def validate(self):
        try:
            self._validate()
        except ChallengeFailure:
            return False
        else:
            return True