import bitstring
import numpy
import numpy.typing

from pyomslpwan.lib.convolution import convolve, deconvolve, softViterbiDecode, generateEmissionTable



def toBinaryArray(data):
    return numpy.array(data, dtype=int)

def toNrzArray(data):
    return binaryToNrz(toBinaryArray(data))

def toBits(data):
    return bitstring.Bits(data)

def binaryToNrz(data):
    return data * 2.0 - 1

def nrzToBinary(data):
    return data > 0



class ConvolutionalCodec:

    def __init__(self, constraint_length, polynomials, recursive_polynomial=None, use_lookup_table=True):
        
        self.constraint_length = constraint_length
        self.polynomials = numpy.array(polynomials, dtype=numpy.uint32)
        self.recursive_polynomial = recursive_polynomial

        if use_lookup_table:
            self.emission_table = generateEmissionTable(self.constraint_length, self.polynomials)
        else:
            self.emission_table = None

    def encode(self, data, initial_state=0, final_state=0):
        data = data.astype(numpy.bool_)

        if self.recursive_polynomial is not None:
            data = deconvolve(data, self.constraint_length, self.recursive_polynomial, 0)

        emissions = [convolve(data, self.constraint_length, poly, initial_state, final_state) for poly in self.polynomials]

        return emissions
    
    def decode(self, observed_emissions, initial_state=0, final_state=0, soft=False):
        observed_emissions = numpy.stack(observed_emissions, axis=0).astype(numpy.float32)
        
        if not soft:
            observed_emissions = binaryToNrz(observed_emissions)
        
        if self.emission_table is None:
            data = softViterbiDecode(observed_emissions, self.constraint_length, initial_state, final_state, polynomials=self.polynomials)
        else:
            data = softViterbiDecode(observed_emissions, self.constraint_length, initial_state, final_state, emission_table=self.emission_table)

        if self.recursive_polynomial is not None:
            data = convolve(data, self.constraint_length, self.recursive_polynomial, 0, 0)[:-self.constraint_length + 1]

        return data



class CrcCodec:

    def __init__(self, crc_length, polynomial, use_lookup_table=True):
        self.crc_length = crc_length
        self.codec = ConvolutionalCodec(crc_length + 1, [polynomial], recursive_polynomial=polynomial, use_lookup_table=use_lookup_table)
    
    def encode(self, data):
        encoded = self.codec.encode(data)[0]
        return encoded
    
    def parity(self, data):
        encoded = self.encode(data)
        parity = encoded[-self.crc_length:]
        return parity
    
    def decode(self, encoded, soft=False):
        data = self.codec.decode([encoded], soft=soft)
        return data
    
    def check(self, encoded):
        parity = self.parity(encoded)
        return (parity == 0).all()



class Puncturer:

    def __init__(self, mask_size, bitmask):
        self.bitmask = numpy.array(bitstring.Bits(uint=bitmask, length=mask_size), dtype=bool)

    def puncture(self, data, punctured_length):
        pattern = numpy.resize(self.bitmask, len(data))
        punctured = data[pattern][:punctured_length]
        return punctured

    def depuncture(self, data, depunctured_length, placeholder_value=0):
        depunctured = numpy.full(depunctured_length, placeholder_value, dtype=data.dtype)
        puncture_mask = numpy.resize(self.bitmask, depunctured_length)
        depunctured[puncture_mask] = data
        return depunctured



class Scrambler:

    def __init__(self, index_multiplier):
        self.index_multiplier = index_multiplier
    
    def scramble(self, data):
        data_index = numpy.arange(len(data), dtype=numpy.uint32)
        interleaved_index = (self.index_multiplier * data_index) % len(data)
        interleaved = numpy.empty_like(data)
        interleaved[interleaved_index] = data
        return interleaved
    
    def unscramble(self, interleaved):
        data_index = numpy.arange(len(interleaved), dtype=numpy.uint32)
        interleaved_index = (self.index_multiplier * data_index) % len(interleaved)
        data = interleaved[interleaved_index]
        return data



class DifferentialCodec:

    def __init__(self):
        pass

    def encode(self, data, seed_bit=0):
        padded_data = numpy.insert(data, 0, seed_bit)
        differential = numpy.abs(numpy.diff(padded_data))
        return differential
    
    def decode(self, differential, seed_bit=0):
        data = numpy.cumsum(differential) % 2
        return data
