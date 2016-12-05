from __future__ import absolute_import

import random

from math import log, floor, ceil


class Concatenation(object):
    
    def __init__(self, objs):
        self.objs = objs
        
    def value(self):
        if not self.objs:
            return list()
        initial_value = type(self.objs[0])()
        return reduce(lambda result, obj: result + obj,
                      self.objs, initial_value)
        
        
class FileLines(object):
    
    def __init__(self, filename):
        self.filename = filename
        
    def value(self):
        return open(self.filename, 'r').read().splitlines()
    
    
class ByteSize(object):
    
    def __init__(self, integer):
        self.integer = integer
        
    def value(self):
        bit_size = 1 + floor(log(self.integer, 2))
        return int(ceil(bit_size/8))


class Average(object):
    
    def __init__(self, values):
        self.values = values
        
    def value(self):
        length = len(self.values)
        return sum(self.values)/float(length)
    
    
class Product(object):
    
    def __init__(self, values):
        self.values = values
        
    def value(self, identity=1):
        return reduce(lambda a,b: a*b, self.values, identity)
    

class RandomByteGenerator(object):
    
    MAX_VALUE = 500
    
    def value(self, count=None):
        if count is None:
            count = random.randint(1, self.MAX_VALUE)
        random_bytes = str()
        chars = map(chr, range(255))
        i = 0
        while i < count:
            random_bytes += random.choice(chars)
            i += 1
        return random_bytes
    
    
class AllEqual(object):
    
    def __init__(self, objs):
        self.objs = objs
        
    def value(self, obj=None):
        if obj is None:
            value = len(set(self.objs)) == 1
        else:
            value = all(map(lambda _obj: _obj == obj, self.objs))
        return value
    

class HammingDistance(object):
    
    def __init__(self, string1, string2):
        if len(string1) != len(string2):
            raise RuntimeError('strings must have equal length') 
        self.string1 = string1
        self.string2 = string2
        
    def value(self):
        from common.tools.converters import BytesToBinary
        bin_string1 = BytesToBinary(self.string1).value()
        bin_string2 = BytesToBinary(self.string2).value()
        pairs = zip(bin_string1, bin_string2)
        differences = reduce(lambda count, (bit1,bit2): count + (bit1 != bit2),
                             pairs, 0)
        return differences