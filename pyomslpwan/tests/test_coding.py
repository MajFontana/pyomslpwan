import unittest
from bitstring import Bits

from pyomslpwan.tests.vectors import *
from pyomslpwan.lib.coding import toBinaryArray, toNrzArray
from pyomslpwan.src.coding import *



class FecTest(unittest.TestCase):

    def setUp(self):
        self.vector = FecTestVector()
        self.codec = CommonFecEncodingScheme()  

    def test_encoder(self):
        fec_input = toBinaryArray(self.vector.input_data)
        fec_parities = self.codec.encode(fec_input)
        self.assertEqual(fec_parities.systematic.getBits(), self.vector.systematic_output)
        self.assertEqual(fec_parities.fec_parity_1.getBits(), self.vector.fec_parity_1)
        self.assertEqual(fec_parities.fec_parity_2.getBits(), self.vector.fec_parity_2)
        self.assertEqual(fec_parities.fec_parity_3.getBits(), self.vector.fec_parity_3)
        self.assertEqual(fec_parities.fec_tail_0.getBits(), self.vector.fec_tail_0)
        self.assertEqual(fec_parities.fec_tail_1.getBits(), self.vector.fec_tail_1)
        self.assertEqual(fec_parities.fec_tail_2.getBits(), self.vector.fec_tail_2)
        self.assertEqual(fec_parities.fec_tail_3.getBits(), self.vector.fec_tail_3)
        self.assertEqual(fec_parities.fec_parity_3a.getBits(), self.vector.fec_parity_3a)
        self.assertEqual(fec_parities.fec_parity_3b.getBits(), self.vector.fec_parity_3b)
        self.assertEqual(fec_parities.fec_parity_3c.getBits(), self.vector.fec_parity_3c)
    
    def test_decoder_single_burst_7_8(self):
        fec_parities = CommonFecEncodingSchemeParities()
        fec_parities.systematic.setSize(len(self.vector.systematic_output))
        fec_parities.fec_parity_3a.setSize(len(self.vector.fec_parity_3a))
        fec_parities.fec_tail_0.setSize(len(self.vector.fec_tail_0))
        fec_parities.systematic.setBitstream(toNrzArray(self.vector.systematic_output))
        fec_parities.fec_parity_3a.setBitstream(toNrzArray(self.vector.fec_parity_3a))
        fec_parities.fec_tail_0.setBitstream(toNrzArray(self.vector.fec_tail_0))
        fec_output = self.codec.decode(fec_parities, len(self.vector.input_data))
        self.assertEqual(Bits(fec_output), self.vector.input_data)
    
    def test_decoder_single_burst_1_2(self):
        fec_parities = CommonFecEncodingSchemeParities()
        fec_parities.systematic.setSize(len(self.vector.systematic_output))
        fec_parities.fec_parity_1.setSize(len(self.vector.fec_parity_1))
        fec_parities.fec_tail_1.setSize(len(self.vector.fec_tail_1))
        fec_parities.systematic.setBitstream(toNrzArray(self.vector.systematic_output))
        fec_parities.fec_parity_1.setBitstream(toNrzArray(self.vector.fec_parity_1))
        fec_parities.fec_tail_1.setBitstream(toNrzArray(self.vector.fec_tail_1))
        fec_output = self.codec.decode(fec_parities, len(self.vector.input_data))
        self.assertEqual(Bits(fec_output), self.vector.input_data)
    
    def test_decoder_single_burst_1_3(self):
        fec_parities = CommonFecEncodingSchemeParities()
        fec_parities.systematic.setSize(len(self.vector.systematic_output))
        fec_parities.fec_parity_1.setSize(len(self.vector.fec_parity_1))
        fec_parities.fec_tail_1.setSize(len(self.vector.fec_tail_1))
        fec_parities.fec_parity_2.setSize(len(self.vector.fec_parity_2))
        fec_parities.fec_tail_2.setSize(len(self.vector.fec_tail_2))
        fec_parities.systematic.setBitstream(toNrzArray(self.vector.systematic_output))
        fec_parities.fec_parity_1.setBitstream(toNrzArray(self.vector.fec_parity_1))
        fec_parities.fec_tail_1.setBitstream(toNrzArray(self.vector.fec_tail_1))
        fec_parities.fec_parity_2.setBitstream(toNrzArray(self.vector.fec_parity_2))
        fec_parities.fec_tail_2.setBitstream(toNrzArray(self.vector.fec_tail_2))
        fec_output = self.codec.decode(fec_parities, len(self.vector.input_data))
        self.assertEqual(Bits(fec_output), self.vector.input_data)
    
    def test_decoder_multi_burst_1(self):
        fec_parities = CommonFecEncodingSchemeParities()
        fec_parities.systematic.setSize(len(self.vector.systematic_output))
        fec_parities.fec_parity_3a.setSize(len(self.vector.fec_parity_3a))
        fec_parities.fec_tail_0.setSize(len(self.vector.fec_tail_0))
        fec_parities.systematic.setBitstream(toNrzArray(self.vector.systematic_output))
        fec_parities.fec_parity_3a.setBitstream(toNrzArray(self.vector.fec_parity_3a))
        fec_parities.fec_tail_0.setBitstream(toNrzArray(self.vector.fec_tail_0))
        fec_output = self.codec.decode(fec_parities, len(self.vector.input_data))
        self.assertEqual(Bits(fec_output), self.vector.input_data)
    
    def test_decoder_multi_burst_2(self):
        fec_parities = CommonFecEncodingSchemeParities()
        fec_parities.fec_parity_1.setSize(len(self.vector.fec_parity_1))
        fec_parities.fec_parity_3b.setSize(len(self.vector.fec_parity_3b))
        fec_parities.fec_tail_1.setSize(len(self.vector.fec_tail_1))
        fec_parities.fec_parity_1.setBitstream(toNrzArray(self.vector.fec_parity_1))
        fec_parities.fec_parity_3b.setBitstream(toNrzArray(self.vector.fec_parity_3b))
        fec_parities.fec_tail_1.setBitstream(toNrzArray(self.vector.fec_tail_1))
        fec_output = self.codec.decode(fec_parities, len(self.vector.input_data))
        self.assertEqual(Bits(fec_output), self.vector.input_data)
    
    def test_decoder_multi_burst_3(self):
        fec_parities = CommonFecEncodingSchemeParities()
        fec_parities.fec_parity_2.setSize(len(self.vector.fec_parity_2))
        fec_parities.fec_parity_3c.setSize(len(self.vector.fec_parity_3c))
        fec_parities.fec_tail_2.setSize(len(self.vector.fec_tail_2))
        fec_parities.fec_parity_2.setBitstream(toNrzArray(self.vector.fec_parity_2))
        fec_parities.fec_parity_3c.setBitstream(toNrzArray(self.vector.fec_parity_3c))
        fec_parities.fec_tail_2.setBitstream(toNrzArray(self.vector.fec_tail_2))
        fec_output = self.codec.decode(fec_parities, len(self.vector.input_data))
        self.assertEqual(Bits(fec_output), self.vector.input_data)



class InterleaverTest(unittest.TestCase):

    def setUp(self):
        self.interleaver = CommonInterleavingScheme()
        self.vector_40_bit = Interleaver40BitTestVector()
        self.vector_80_bit = Interleaver80BitTestVector()

    def test_interleaver(self):
        interleaver_input = toBinaryArray(self.vector_40_bit.coded_payload)
        data = Bits(self.interleaver.interleave(interleaver_input))
        self.assertEqual(data, self.vector_40_bit.data)

        interleaver_input = toBinaryArray(self.vector_80_bit.coded_payload)
        data = Bits(self.interleaver.interleave(interleaver_input))
        self.assertEqual(data, self.vector_80_bit.data)

    def test_deinterleaver(self):
        interleaver_input = toBinaryArray(self.vector_40_bit.data)
        coded_payload = Bits(self.interleaver.deinterleave(interleaver_input))
        self.assertEqual(coded_payload, self.vector_40_bit.coded_payload)

        interleaver_input = toBinaryArray(self.vector_80_bit.data)
        coded_payload = Bits(self.interleaver.deinterleave(interleaver_input))
        self.assertEqual(coded_payload, self.vector_80_bit.coded_payload)
    


class PrecoderTest(unittest.TestCase):

    def setUp(self):
        self.precoder = Precoder()
        self.vector_1 = Precoding1TestVector()
        self.data_1 = self.vector_1.preamble\
        + self.vector_1.sync\
        + self.vector_1.cl\
        + self.vector_1.data_a\
        + self.vector_1.midamble\
        + self.vector_1.coded_header\
        + self.vector_1.data_b
        self.vector_2 = Precoding2TestVector()
        self.data_2 = self.vector_2.preamble\
        + self.vector_2.sync\
        + self.vector_2.cl\
        + self.vector_2.data_a\
        + self.vector_2.midamble\
        + self.vector_2.coded_header\
        + self.vector_2.data_b

    def test_encoder(self):
        precoder_input = toBinaryArray(self.data_1)
        precoded = Bits(self.precoder.encode(precoder_input))
        self.assertEqual(precoded, self.vector_1.precoded_uplink_radio_burst)

        precoder_input = toBinaryArray(self.data_2)
        precoded = Bits(self.precoder.encode(precoder_input))
        self.assertEqual(precoded, self.vector_2.precoded_uplink_radio_burst)

    def test_decoder(self):
        precoder_input = toBinaryArray(self.vector_1.precoded_uplink_radio_burst)
        data = Bits(self.precoder.decode(precoder_input))
        self.assertEqual(data, self.data_1)

        precoder_input = toBinaryArray(self.vector_2.precoded_uplink_radio_burst)
        data = Bits(self.precoder.decode(precoder_input))
        self.assertEqual(data, self.data_2)