from pyomslpwan.lib.coding import ConvolutionalCodec, Puncturer, CrcCodec, Scrambler, DifferentialCodec
from pyomslpwan.lib.fields import Field, FieldGroup
import numpy



class CommonFecEncodingSchemeParities():
    def __init__(self):
        self.systematic = Field()
        self.fec_parity_1 = Field()
        self.fec_parity_2 = Field()
        self.fec_parity_3 = Field()
        self.fec_tail_0 = Field()
        self.fec_tail_1 = Field()
        self.fec_tail_2 = Field()
        self.fec_tail_3 = Field()
        self.fec_parity_3a = Field()
        self.fec_parity_3b = Field()
        self.fec_parity_3c = Field()
    
        self.fec_group_0 = FieldGroup([
            self.systematic,
            self.fec_tail_0
        ])

        self.fec_group_1 = FieldGroup([
            self.fec_parity_1,
            self.fec_tail_1
        ])

        self.fec_group_2 = FieldGroup([
            self.fec_parity_2,
            self.fec_tail_2
        ])

        self.fec_group_3 = FieldGroup([
            self.fec_parity_3,
            self.fec_tail_3
        ])



class CommonFecEncodingScheme:

    CONSTRAINT_LENGTH = 7
    INITIAL_STATE = 0
    FINAL_STATE = 0
    POLYNOMIAL_G0 = 0x4D
    POLYNOMIAL_G1 = 0x73
    POLYNOMIAL_G2 = 0x67
    POLYNOMIAL_G3 = 0x5D

    PUNCTURING_PATTERN_SIZE = 7
    PUNCTURING_PATTERN_A = 0b1000000
    PUNCTURING_PATTERN_B = 0b0100000
    PUNCTURING_PATTERN_C = 0b0010000

    def __init__(self):
        self.codec = ConvolutionalCodec(CommonFecEncodingScheme.CONSTRAINT_LENGTH,
                                        [CommonFecEncodingScheme.POLYNOMIAL_G0,
                                         CommonFecEncodingScheme.POLYNOMIAL_G1,
                                         CommonFecEncodingScheme.POLYNOMIAL_G2,
                                         CommonFecEncodingScheme.POLYNOMIAL_G3],
                                        recursive_polynomial=CommonFecEncodingScheme.POLYNOMIAL_G0)

        self.puncturer_a = Puncturer(CommonFecEncodingScheme.PUNCTURING_PATTERN_SIZE,
                                     CommonFecEncodingScheme.PUNCTURING_PATTERN_A)
        self.puncturer_b = Puncturer(CommonFecEncodingScheme.PUNCTURING_PATTERN_SIZE,
                                     CommonFecEncodingScheme.PUNCTURING_PATTERN_B)
        self.puncturer_c = Puncturer(CommonFecEncodingScheme.PUNCTURING_PATTERN_SIZE,
                                     CommonFecEncodingScheme.PUNCTURING_PATTERN_C)
    
    def encode(self, data):
        c0, c1, c2, c3 = self.codec.encode(data,
                                           initial_state=CommonFecEncodingScheme.INITIAL_STATE,
                                           final_state=CommonFecEncodingScheme.FINAL_STATE)

        data_size = len(data)
        punctured_size = data_size // CommonFecEncodingScheme.PUNCTURING_PATTERN_SIZE
        tail_size = CommonFecEncodingScheme.CONSTRAINT_LENGTH - 1

        parities = CommonFecEncodingSchemeParities()
        parities.systematic.setSize(data_size)
        parities.fec_parity_1.setSize(data_size)
        parities.fec_parity_2.setSize(data_size)
        parities.fec_parity_3.setSize(data_size)
        parities.fec_tail_0.setSize(tail_size)
        parities.fec_tail_1.setSize(tail_size)
        parities.fec_tail_2.setSize(tail_size)
        parities.fec_tail_3.setSize(tail_size)
        parities.fec_parity_3a.setSize(punctured_size)
        parities.fec_parity_3b.setSize(punctured_size)
        parities.fec_parity_3c.setSize(punctured_size)

        parities.fec_group_0.setBitstream(c0)
        parities.fec_group_1.setBitstream(c1)
        parities.fec_group_2.setBitstream(c2)
        parities.fec_group_3.setBitstream(c3)
        fec_parity_3 = parities.fec_parity_3.getBitstream()
        parities.fec_parity_3a.setBitstream(self.puncturer_a.puncture(fec_parity_3, punctured_size))
        parities.fec_parity_3b.setBitstream(self.puncturer_b.puncture(fec_parity_3, punctured_size))
        parities.fec_parity_3c.setBitstream(self.puncturer_c.puncture(fec_parity_3, punctured_size))

        return parities

    def decode(self, parities: CommonFecEncodingSchemeParities, data_size):
        punctured_size = data_size // CommonFecEncodingScheme.PUNCTURING_PATTERN_SIZE
        tail_size = CommonFecEncodingScheme.CONSTRAINT_LENGTH - 1
        default = lambda x, d: x if len(x) > 0 else d
        
        zero_parity = numpy.zeros(data_size)
        zero_tail = numpy.zeros(tail_size)

        systematic = default(parities.systematic.getNrzStream(), zero_parity)
        fec_parity_1 = default(parities.fec_parity_1.getNrzStream(), zero_parity)
        fec_parity_2 = default(parities.fec_parity_2.getNrzStream(), zero_parity)
        fec_tail_0 = default(parities.fec_tail_0.getNrzStream(), zero_tail)
        fec_tail_1 = default(parities.fec_tail_1.getNrzStream(), zero_tail)
        fec_tail_2 = default(parities.fec_tail_2.getNrzStream(), zero_tail)
        fec_tail_3 = default(parities.fec_tail_3.getNrzStream(), zero_tail)

        fec_parity_3 = numpy.zeros(data_size)
        fec_parity_3_mask = numpy.zeros(data_size)

        if parities.fec_parity_3.getSize() > 0:
            fec_parity_3 += parities.fec_parity_3.getNrzStream()
            fec_parity_3_mask += 1
        if parities.fec_parity_3a.getSize() > 0:
            fec_parity_3 += self.puncturer_a.depuncture(parities.fec_parity_3a.getNrzStream(), data_size)
            fec_parity_3_mask += self.puncturer_a.depuncture(numpy.ones(punctured_size), data_size)
        if parities.fec_parity_3b.getSize() > 0:
            fec_parity_3 += self.puncturer_b.depuncture(parities.fec_parity_3b.getNrzStream(), data_size)
            fec_parity_3_mask += self.puncturer_b.depuncture(numpy.ones(punctured_size), data_size)
        if parities.fec_parity_3c.getSize() > 0:
            fec_parity_3 += self.puncturer_c.depuncture(parities.fec_parity_3c.getNrzStream(), data_size)
            fec_parity_3_mask += self.puncturer_c.depuncture(numpy.ones(punctured_size), data_size)

        numpy.divide(fec_parity_3, fec_parity_3_mask, where=fec_parity_3_mask != 0, out=fec_parity_3)

        fec_data_0 = numpy.concatenate([systematic, fec_tail_0])
        fec_data_1 = numpy.concatenate([fec_parity_1, fec_tail_1])
        fec_data_2 = numpy.concatenate([fec_parity_2, fec_tail_2])
        fec_data_3 = numpy.concatenate([fec_parity_3, fec_tail_3])

        emissions = [fec_data_0, fec_data_1, fec_data_2, fec_data_3]
        data = self.codec.decode(emissions,
                                 initial_state=CommonFecEncodingScheme.INITIAL_STATE,
                                 final_state=CommonFecEncodingScheme.FINAL_STATE,
                                 soft=True)

        return data



class CommonInterleavingScheme:

    MULTIPLIER = 188527

    def __init__(self):
        self.scrambler = Scrambler(CommonInterleavingScheme.MULTIPLIER)
    
    def interleave(self, data):
        return self.scrambler.scramble(data)
    
    def deinterleave(self, interleaved):
        return self.scrambler.unscramble(interleaved)



class Precoder(DifferentialCodec):
    
    SEED_BIT = 0

    def encode(self, data):
        return super().encode(data, seed_bit=Precoder.SEED_BIT)
    
    def decode(self, precoded):
        return super().decode(precoded, seed_bit=Precoder.SEED_BIT)



class CodedLengthCrc(CrcCodec):

    LENGTH = 15
    POLYNOMIAL = 0xC617

    def __init__(self):
        super().__init__(CodedLengthCrc.LENGTH, CodedLengthCrc.POLYNOMIAL)



class CodedHeaderCrc(CrcCodec):

    LENGTH = 8
    POLYNOMIAL = 0x107

    def __init__(self):
        super().__init__(CodedHeaderCrc.LENGTH, CodedHeaderCrc.POLYNOMIAL)