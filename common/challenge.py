class ChallengeFailure(Exception):
    
    pass


class MatasanoChallenge(object):
    
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