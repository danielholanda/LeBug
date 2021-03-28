from copy import deepcopy as copy
import yaml

''' C-like struct '''
class struct:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    def __repr__(self):
        return str(self.__dict__)

''' Map list to int '''
def toInt(lst):
    return [list(map(int, l)) for l in lst]

''' Encode vector of floats to ints '''
def floatToEncodedInt(float_array,DATA_WIDTH):
    return [encode(x,DATA_WIDTH) for x in float_array]

''' Encode vector of floats to ints '''    
def encode(value,DATA_WIDTH):
    int_bits=int(DATA_WIDTH/2)
    frac_bits=int(DATA_WIDTH/2)
    is_negative = value<0
    max_value = (1<<(int_bits-1+frac_bits))-1
    x = round(value * (1<< frac_bits))
    x = int(max_value if x > max_value else -max_value if x< -max_value else x)
    if is_negative:
        x = (1<<DATA_WIDTH) + x
    return x

''' Decode vector of floats from encoded ints back to floats '''
def encodedIntTofloat(encoded_int,DATA_WIDTH):
    frac_bits=int(DATA_WIDTH/2)
    return [[decode(encoded_value,DATA_WIDTH) for encoded_value in l] for l in encoded_int] 

''' Decode vector of floats from encoded ints back to floats '''
def decode(value,DATA_WIDTH):
    int_bits=int(DATA_WIDTH/2)
    frac_bits=int(DATA_WIDTH/2)
    value=float(value)
    max_value = (1<<(int_bits-1+frac_bits))-1
    is_negative = value>max_value
    if is_negative:
        value = -((1<<DATA_WIDTH) - value)
    return value / (1 << frac_bits)