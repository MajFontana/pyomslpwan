import unittest
from bitstring import Bits

from pyomslpwan.tests.vectors import *
from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator, BurstModeUplinkParser
from pyomslpwan.src.uplink.pdu import *
from pyomslpwan.src.structs import *
from pyomslpwan.lib.fields import FieldGroup
from pyomslpwan.lib.coding import toBinaryArray, nrzToBinary



class SingleBurstRate78Test(unittest.TestCase):

    def setUp(self):
        self.vector = FullUplinkSingleBurstRate78TestVector()
        self.generator = BurstModeUplinkGenerator()
        self.parser = BurstModeUplinkParser()

    def test_generator(self):
        frame = UplinkFrame()
        frame.coded_payload.phy_payload = self.vector.phy_payload.bytes
        frame.coded_header.timing_input_value = self.vector.timing_input_value.uint
        frame.coded_header.burst_mode = BURST_MODE_SINGLE_BURST
        frame.coded_header.burst_type = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8
        self.generator.generateFrame(frame)

        burst = frame.uplink_0
        coded_payload = frame.coded_payload
        coded_header = frame.coded_header

        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        self.assertEqual(coded_payload.single_burst_fec_7_8_struct.phy_payload.getBits(), self.vector.phy_payload)
        self.assertEqual(coded_payload.single_burst_fec_7_8_struct.getBits(), self.vector.coded_payload)
        self.assertEqual(Bits(burst.data_bitstream), self.vector.data)

        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_length.getBits(), self.vector.cl)
        self.assertEqual(burst.struct.data_a.getBits(), self.vector.data_a)
        self.assertEqual(burst.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(burst.struct.data_b.getBits(), self.vector.data_b)

        self.assertEqual(burst.struct.getBits(), self.vector.radio_burst)
        self.assertEqual(Bits(burst.bitstream), self.vector.radio_burst_after_precoding)
    
    def test_parser(self):
        bitstream = toBinaryArray(self.vector.radio_burst)

        burst = UplinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_length
        ])
        group2 = FieldGroup([
            burst.struct.data_a,
            burst.struct.midamble,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_length.getBits(), self.vector.cl)
        self.parser.parseCodedLength(burst)

        input, bitstream = numpy.split(bitstream, [group2.getSize()])
        group2.setBitstream(input)
        self.assertEqual(burst.struct.data_a.getBits(), self.vector.data_a)
        self.assertEqual(burst.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data_b.getSize()])
        burst.struct.data_b.setBitstream(input)
        self.assertEqual(burst.struct.data_b.getBits(), self.vector.data_b)
        self.parser.parseData(burst)
        self.assertEqual(Bits(nrzToBinary(burst.data_bitstream)), self.vector.data)

        frame = UplinkFrame()
        frame.uplink_0 = burst
        self.parser.parseFrame(frame)
        coded_payload = frame.coded_payload
        self.assertEqual(coded_payload.single_burst_fec_7_8_struct.getBits(), self.vector.coded_payload)
        self.assertEqual(Bits(coded_payload.phy_payload), self.vector.phy_payload)



class SingleBurstRate12Test(unittest.TestCase):

    def setUp(self):
        self.vector = FullUplinkSingleBurstRate12TestVector()
        self.generator = BurstModeUplinkGenerator()
        self.parser = BurstModeUplinkParser()

    def test_generator(self):
        frame = UplinkFrame()
        frame.coded_payload.phy_payload = self.vector.phy_payload.bytes
        frame.coded_header.timing_input_value = self.vector.timing_input_value.uint
        frame.coded_header.burst_mode = BURST_MODE_SINGLE_BURST
        frame.coded_header.burst_type = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2
        self.generator.generateFrame(frame)

        burst = frame.uplink_0
        coded_payload = frame.coded_payload
        coded_header = frame.coded_header

        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        self.assertEqual(coded_payload.single_burst_fec_1_2_struct.phy_payload.getBits(), self.vector.phy_payload)
        self.assertEqual(coded_payload.single_burst_fec_1_2_struct.getBits(), self.vector.coded_payload)
        self.assertEqual(Bits(burst.data_bitstream), self.vector.data)

        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_length.getBits(), self.vector.cl)
        self.assertEqual(burst.struct.data_a.getBits(), self.vector.data_a)
        self.assertEqual(burst.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(burst.struct.data_b.getBits(), self.vector.data_b)

        self.assertEqual(burst.struct.getBits(), self.vector.radio_burst)
        self.assertEqual(Bits(burst.bitstream), self.vector.radio_burst_after_precoding)

    def test_parser(self):
        bitstream = toBinaryArray(self.vector.radio_burst)

        burst = UplinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_length
        ])
        group2 = FieldGroup([
            burst.struct.data_a,
            burst.struct.midamble,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_length.getBits(), self.vector.cl)
        self.parser.parseCodedLength(burst)

        input, bitstream = numpy.split(bitstream, [group2.getSize()])
        group2.setBitstream(input)
        self.assertEqual(burst.struct.data_a.getBits(), self.vector.data_a)
        self.assertEqual(burst.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data_b.getSize()])
        burst.struct.data_b.setBitstream(input)
        self.assertEqual(burst.struct.data_b.getBits(), self.vector.data_b)
        self.parser.parseData(burst)
        self.assertEqual(Bits(nrzToBinary(burst.data_bitstream)), self.vector.data)

        frame = UplinkFrame()
        frame.uplink_0 = burst
        self.parser.parseFrame(frame)
        coded_payload = frame.coded_payload
        self.assertEqual(coded_payload.single_burst_fec_1_2_struct.getBits(), self.vector.coded_payload)
        self.assertEqual(Bits(coded_payload.phy_payload), self.vector.phy_payload)



class SingleBurstRate13Test(unittest.TestCase):

    def setUp(self):
        self.vector = FullUplinkSingleBurstRate13TestVector()
        self.generator = BurstModeUplinkGenerator()
        self.parser = BurstModeUplinkParser()

    def test_generator(self):
        frame = UplinkFrame()
        frame.coded_payload.phy_payload = self.vector.phy_payload.bytes
        frame.coded_header.timing_input_value = self.vector.timing_input_value.uint
        frame.coded_header.burst_mode = BURST_MODE_SINGLE_BURST
        frame.coded_header.burst_type = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3
        self.generator.generateFrame(frame)

        burst = frame.uplink_0
        coded_payload = frame.coded_payload
        coded_header = frame.coded_header

        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        self.assertEqual(coded_payload.single_burst_fec_1_3_struct.phy_payload.getBits(), self.vector.phy_payload)
        self.assertEqual(coded_payload.single_burst_fec_1_3_struct.getBits(), self.vector.coded_payload)
        self.assertEqual(Bits(burst.data_bitstream), self.vector.data)

        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_length.getBits(), self.vector.cl)
        self.assertEqual(burst.struct.data_a.getBits(), self.vector.data_a)
        self.assertEqual(burst.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(burst.struct.data_b.getBits(), self.vector.data_b)

        self.assertEqual(burst.struct.getBits(), self.vector.radio_burst)
        self.assertEqual(Bits(burst.bitstream), self.vector.radio_burst_after_precoding)
    
    def test_parser(self):
        bitstream = toBinaryArray(self.vector.radio_burst)

        burst = UplinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_length
        ])
        group2 = FieldGroup([
            burst.struct.data_a,
            burst.struct.midamble,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_length.getBits(), self.vector.cl)
        self.parser.parseCodedLength(burst)

        input, bitstream = numpy.split(bitstream, [group2.getSize()])
        group2.setBitstream(input)
        self.assertEqual(burst.struct.data_a.getBits(), self.vector.data_a)
        self.assertEqual(burst.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data_b.getSize()])
        burst.struct.data_b.setBitstream(input)
        self.assertEqual(burst.struct.data_b.getBits(), self.vector.data_b)
        self.parser.parseData(burst)
        self.assertEqual(Bits(nrzToBinary(burst.data_bitstream)), self.vector.data)

        frame = UplinkFrame()
        frame.uplink_0 = burst
        self.parser.parseFrame(frame)
        coded_payload = frame.coded_payload
        self.assertEqual(coded_payload.single_burst_fec_1_3_struct.getBits(), self.vector.coded_payload)
        self.assertEqual(Bits(coded_payload.phy_payload), self.vector.phy_payload)



class MultiBurstTest(unittest.TestCase):

    def setUp(self):
        self.vector = FullUplinkMultiBurstTestVector()
        self.generator = BurstModeUplinkGenerator()
        self.parser = BurstModeUplinkParser()

    def test_generator(self):
        frame = UplinkFrame()
        frame.coded_payload.phy_payload = self.vector.phy_payload.bytes
        frame.coded_header.timing_input_value = self.vector.timing_input_value.uint
        frame.coded_header.burst_mode = BURST_MODE_MULTI_BURST
        frame.coded_header.burst_type = self.vector.burst_type.uint
        self.generator.generateFrame(frame)

        coded_payload = frame.coded_payload
        coded_header = frame.coded_header

        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        self.assertEqual(coded_payload.multi_burst_1_struct.phy_payload.getBits(), self.vector.phy_payload)
        self.assertEqual(coded_payload.multi_burst_1_struct.getBits(), self.vector.coded_payload_ul1)
        self.assertEqual(coded_payload.multi_burst_2_struct.getBits(), self.vector.coded_payload_ul2)
        self.assertEqual(coded_payload.multi_burst_3_struct.getBits(), self.vector.coded_payload_ul3)
        self.assertEqual(Bits(frame.uplink_1.data_bitstream), self.vector.data_ul1)
        self.assertEqual(Bits(frame.uplink_2.data_bitstream), self.vector.data_ul2)
        self.assertEqual(Bits(frame.uplink_3.data_bitstream), self.vector.data_ul3)

        self.assertEqual(frame.uplink_1.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(frame.uplink_1.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(frame.uplink_1.struct.coded_length.getBits(), self.vector.cl)
        self.assertEqual(frame.uplink_1.struct.data_a.getBits(), self.vector.data_a_ul1)
        self.assertEqual(frame.uplink_1.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(frame.uplink_1.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(frame.uplink_1.struct.data_b.getBits(), self.vector.data_b_ul1)

        self.assertEqual(frame.uplink_2.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(frame.uplink_2.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(frame.uplink_2.struct.coded_length.getBits(), self.vector.cl)
        self.assertEqual(frame.uplink_2.struct.data_a.getBits(), self.vector.data_a_ul2)
        self.assertEqual(frame.uplink_2.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(frame.uplink_2.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(frame.uplink_2.struct.data_b.getBits(), self.vector.data_b_ul2)

        self.assertEqual(frame.uplink_3.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(frame.uplink_3.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(frame.uplink_3.struct.coded_length.getBits(), self.vector.cl)
        self.assertEqual(frame.uplink_3.struct.data_a.getBits(), self.vector.data_a_ul3)
        self.assertEqual(frame.uplink_3.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(frame.uplink_3.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(frame.uplink_3.struct.data_b.getBits(), self.vector.data_b_ul3)

        self.assertEqual(frame.uplink_1.struct.getBits(), self.vector.radio_burst_ul1)
        self.assertEqual(frame.uplink_2.struct.getBits(), self.vector.radio_burst_ul2)
        self.assertEqual(frame.uplink_3.struct.getBits(), self.vector.radio_burst_ul3)
        self.assertEqual(Bits(frame.uplink_1.bitstream), self.vector.radio_burst_after_precoding_ul1)
        self.assertEqual(Bits(frame.uplink_2.bitstream), self.vector.radio_burst_after_precoding_ul2)
        self.assertEqual(Bits(frame.uplink_3.bitstream), self.vector.radio_burst_after_precoding_ul3)

    def test_parser(self):
        # UL1
        bitstream = toBinaryArray(self.vector.radio_burst_ul1)

        burst = UplinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_length
        ])
        group2 = FieldGroup([
            burst.struct.data_a,
            burst.struct.midamble,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_length.getBits(), self.vector.cl)
        self.parser.parseCodedLength(burst)

        input, bitstream = numpy.split(bitstream, [group2.getSize()])
        group2.setBitstream(input)
        self.assertEqual(burst.struct.data_a.getBits(), self.vector.data_a_ul1)
        self.assertEqual(burst.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data_b.getSize()])
        burst.struct.data_b.setBitstream(input)
        self.assertEqual(burst.struct.data_b.getBits(), self.vector.data_b_ul1)
        self.parser.parseData(burst)
        self.assertEqual(Bits(nrzToBinary(burst.data_bitstream)), self.vector.data_ul1)

        burst_ul1 = burst

        # UL2
        bitstream = toBinaryArray(self.vector.radio_burst_ul2)

        burst = UplinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_length
        ])
        group2 = FieldGroup([
            burst.struct.data_a,
            burst.struct.midamble,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_length.getBits(), self.vector.cl)
        self.parser.parseCodedLength(burst)

        input, bitstream = numpy.split(bitstream, [group2.getSize()])
        group2.setBitstream(input)
        self.assertEqual(burst.struct.data_a.getBits(), self.vector.data_a_ul2)
        self.assertEqual(burst.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data_b.getSize()])
        burst.struct.data_b.setBitstream(input)
        self.assertEqual(burst.struct.data_b.getBits(), self.vector.data_b_ul2)
        self.parser.parseData(burst)
        self.assertEqual(Bits(nrzToBinary(burst.data_bitstream)), self.vector.data_ul2)

        burst_ul2 = burst

        # UL3
        bitstream = toBinaryArray(self.vector.radio_burst_ul3)

        burst = UplinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_length
        ])
        group2 = FieldGroup([
            burst.struct.data_a,
            burst.struct.midamble,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_length.getBits(), self.vector.cl)
        self.parser.parseCodedLength(burst)

        input, bitstream = numpy.split(bitstream, [group2.getSize()])
        group2.setBitstream(input)
        self.assertEqual(burst.struct.data_a.getBits(), self.vector.data_a_ul3)
        self.assertEqual(burst.struct.midamble.getBits(), self.vector.midamble)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data_b.getSize()])
        burst.struct.data_b.setBitstream(input)
        self.assertEqual(burst.struct.data_b.getBits(), self.vector.data_b_ul3)
        self.parser.parseData(burst)
        self.assertEqual(Bits(nrzToBinary(burst.data_bitstream)), self.vector.data_ul3)

        burst_ul3 = burst

        frame = UplinkFrame()
        frame.uplink_1 = burst_ul1
        frame.uplink_2 = burst_ul2
        frame.uplink_3 = burst_ul3
        self.parser.parseFrame(frame)
        coded_payload = frame.coded_payload
        self.assertEqual(coded_payload.multi_burst_1_struct.getBits(), self.vector.coded_payload_ul1)
        self.assertEqual(coded_payload.multi_burst_2_struct.getBits(), self.vector.coded_payload_ul2)
        self.assertEqual(coded_payload.multi_burst_3_struct.getBits(), self.vector.coded_payload_ul3)
        self.assertEqual(Bits(coded_payload.phy_payload), self.vector.phy_payload)