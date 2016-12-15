import string
import sys

from argparse import ArgumentParser
from collections import defaultdict

from common.challenge import CryptoChallenge
from common.tools.misc import Concatenation


class CommandLineParser(object):
    
    DESCRIPTION = 'Matasano crypto challenges'
    HELP_SETS = 'Comma-separated numbers of challenge sets.\
                 If missing, all sets will be run.'
    HELP_CHALLENGES = 'Comma-separated numbers of challenges. If missing,\
                       all challenges inside the given sets will be run.'

    def get_sets(self):
        return self.sets

    def get_challenges(self):
        return self.challenges
                          
    def _parse_cmdline(self):
        parser = ArgumentParser(description=self.DESCRIPTION)
        
        parser.add_argument("-s", "--sets", action='store',
                               dest='sets', help=self.HELP_SETS)
        parser.add_argument("-c", "--challenges", action='store',
                               dest='challenges', help=self.HELP_CHALLENGES)
        
        self.options = parser.parse_args()
        
    def _all_digits(self, argument):
        return all(map(lambda char: char in string.digits, argument))
        
    def _process_argument(self, argument):
        arg_list = list()
        if argument is not None:
            arg_list = argument.split(',')
            arg_list = filter(lambda arg: arg and self._all_digits(arg),
                              arg_list)
        return arg_list
        
    def _process_arguments(self):
        self.sets = self._process_argument(self.options.sets)
        self.challenges = self._process_argument(self.options.challenges)
    
    def run(self):
        self._parse_cmdline()
        self._process_arguments()


class Runner(object):
    
    SET_PLACEHOLDER = 'set%s'
    CHALLENGE_PLACEHOLDER = 'challenge%s'
    MAX_SETS = 8
    ALL_SETS = list(range(MAX_SETS+1))
    CHALLENGES_PER_SET = defaultdict(lambda: 8, {8: 9})
    REQUIREMENTS = ['Crypto']
    
    def __init__(self):
        self.command_line_parser = CommandLineParser()
        self.out_stream = sys.stdout
        self.challenges_ran = 0
        self.challenges_failed = 0
        
    def _show_message(self, message):
        self.out_stream.write(message)
        self.out_stream.flush()
        
    def _get_sets(self):
        set_nums = self.command_line_parser.get_sets()
        if not set_nums:
            set_nums = self.ALL_SETS
        return set_nums
    
    def _get_challenges(self):
        return self.command_line_parser.get_challenges()
    
    def _check_requirements(self):
        message = 'WARNING: required module %s not found. ' +\
                  'Some challenges might be skipped.\n'
        for requirement in self.REQUIREMENTS:
            try:
                __import__(requirement)
            except:
                self._show_message(message % requirement)
    
    def _import_challenge(self, set_num, challenge_num):
        n = sum([self.CHALLENGES_PER_SET[s] for s in xrange(1, set_num)])
        start_num = n + 1
        end_num = n + self.CHALLENGES_PER_SET[set_num]
        challenge_num = int(challenge_num)
        if start_num <= challenge_num <= end_num:
            real_challenge_num = challenge_num
        else:
            real_challenge_num = n + challenge_num
        set_directory = self.SET_PLACEHOLDER % set_num
        challenge_name = self.CHALLENGE_PLACEHOLDER % str(real_challenge_num)
        challenge_path = '%s.%s' % (set_directory, challenge_name)
        try:
            __import__(challenge_path)
        except:
            pass
    
    def _import_challenges(self):
        set_nums = self._get_sets()
        challenge_nums = self._get_challenges()
        
        for set_num in set_nums:
            if not challenge_nums:
                n = self.CHALLENGES_PER_SET[set_num]
                challenge_nums = range(1, n+1)
                
            for challenge_num in challenge_nums:
                self._import_challenge(int(set_num), int(challenge_num))
                
    def _run_challenge(self, challenge):
        self._show_message('Running %s ... ' % challenge.__class__.__name__)
        self.challenges_ran += 1
        if challenge.validate():
            self._show_message('OK\n')
        else:
            self._show_message('FAILED\n')
            self.challenges_failed += 1
                
    def _get_challenge_classes(self):
        challenge_classes = CryptoChallenge.__subclasses__()
        challenge_classes = map(self._get_proper_classes, challenge_classes)
        return Concatenation(challenge_classes).value()
                
    def _get_proper_classes(self, challenge_class):
        subclasses = challenge_class.__subclasses__()
        return subclasses if subclasses else [challenge_class]
                
    def _run_challenges(self):
        challenge_classes = self._get_challenge_classes()
        map(lambda challenge_class: self._run_challenge(challenge_class()),
            challenge_classes)
    
    def _show_result(self):
        if self.challenges_ran == 0:
            self._show_message('No challenges found.\n')
        else:
            if self.challenges_failed == 0:
                self._show_message('\nAll challenges OK.\n')
            else:
                suffix = '' if self.challenges_failed == 1 else 's'
                self._show_message('\n%d challenge%s failed.\n' %
                                   (self.challenges_failed, suffix))
    
    def run(self):
        self._check_requirements()
        self.command_line_parser.run()
        self._import_challenges()
        self._run_challenges()
        self._show_result()


if __name__ == '__main__':
    Runner().run()