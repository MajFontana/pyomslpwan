import unittest
from bitstring import Bits

from pyomslpwan.tests.vectors import *
from pyomslpwan.src.downlink.frame import BurstModeDownlinkGenerator, BurstModeDownlinkParser
from pyomslpwan.src.downlink.pdu import *
from pyomslpwan.src.structs import *
from pyomslpwan.lib.coding import toBinaryArray



class SingleBurstRate78Test(unittest.TestCase):

    def setUp(self):
        self.vector = FullDownlinkSingleBurstRate78TestVector()
        self.generator = BurstModeDownlinkGenerator()
        self.parser = BurstModeDownlinkParser()

    def test_generator(self):
        frame = DownlinkFrame()
        frame.coded_payload.phy_payload = self.vector.phy_payload.bytes
        frame.coded_header.timing_input_value = self.vector.timing_input_value.uint
        frame.coded_header.burst_mode = BURST_MODE_SINGLE_BURST
        frame.coded_header.burst_type = BURST_TYPE_DOWNLINK_SINGLE_BURST_FEC_RATE_7_8
        self.generator.generateFrame(frame)

        burst = frame.downlink_0
        coded_payload = frame.coded_payload
        coded_header = frame.coded_header

        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        self.assertEqual(coded_payload.single_burst_fec_7_8_struct.phy_payload.getBits(), self.vector.phy_payload)
        self.assertEqual(coded_payload.single_burst_fec_7_8_struct.getBits(), self.vector.coded_payload)

        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(burst.struct.data.getBits(), self.vector.data)

        self.assertEqual(burst.struct.getBits(), self.vector.radio_burst)

    def test_parser(self):
        bitstream = toBinaryArray(self.vector.radio_burst)

        burst = DownlinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data.getSize()])
        burst.struct.data.setBitstream(input)
        self.assertEqual(burst.struct.data.getBits(), self.vector.data)

        frame = DownlinkFrame()
        frame.downlink_0 = burst
        self.parser.parseFrame(frame)
        coded_payload = frame.coded_payload
        self.assertEqual(coded_payload.single_burst_fec_7_8_struct.getBits(), self.vector.coded_payload)
        self.assertEqual(Bits(coded_payload.phy_payload), self.vector.phy_payload)



class SingleBurstRate12Test(unittest.TestCase):

    def setUp(self):
        self.vector = FullDownlinkSingleBurstRate12TestVector()
        self.generator = BurstModeDownlinkGenerator()
        self.parser = BurstModeDownlinkParser()

    def test_generator(self):
        frame = DownlinkFrame()
        frame.coded_payload.phy_payload = self.vector.phy_payload.bytes
        frame.coded_header.timing_input_value = self.vector.timing_input_value.uint
        frame.coded_header.burst_mode = BURST_MODE_SINGLE_BURST
        frame.coded_header.burst_type = BURST_TYPE_DOWNLINK_SINGLE_BURST_FEC_RATE_1_2
        self.generator.generateFrame(frame)

        burst = frame.downlink_0
        coded_payload = frame.coded_payload
        coded_header = frame.coded_header

        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        self.assertEqual(coded_payload.single_burst_fec_1_2_struct.phy_payload.getBits(), self.vector.phy_payload)
        self.assertEqual(coded_payload.single_burst_fec_1_2_struct.getBits(), self.vector.coded_payload)

        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(burst.struct.data.getBits(), self.vector.data)

        self.assertEqual(burst.struct.getBits(), self.vector.radio_burst)
    
    def test_parser(self):
        bitstream = toBinaryArray(self.vector.radio_burst)

        burst = DownlinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data.getSize()])
        burst.struct.data.setBitstream(input)
        self.assertEqual(burst.struct.data.getBits(), self.vector.data)

        frame = DownlinkFrame()
        frame.downlink_0 = burst
        self.parser.parseFrame(frame)
        coded_payload = frame.coded_payload
        self.assertEqual(coded_payload.single_burst_fec_1_2_struct.getBits(), self.vector.coded_payload)
        self.assertEqual(Bits(coded_payload.phy_payload), self.vector.phy_payload)



class SingleBurstRate13Test(unittest.TestCase):

    def setUp(self):
        self.vector = FullDownlinkSingleBurstRate13TestVector()
        self.generator = BurstModeDownlinkGenerator()
        self.parser = BurstModeDownlinkParser()

    def test_generator(self):
        frame = DownlinkFrame()
        frame.coded_payload.phy_payload = self.vector.phy_payload.bytes
        frame.coded_header.timing_input_value = self.vector.timing_input_value.uint
        frame.coded_header.burst_mode = BURST_MODE_SINGLE_BURST
        frame.coded_header.burst_type = BURST_TYPE_DOWNLINK_SINGLE_BURST_FEC_RATE_1_3
        self.generator.generateFrame(frame)

        burst = frame.downlink_0
        coded_payload = frame.coded_payload
        coded_header = frame.coded_header

        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        self.assertEqual(coded_payload.single_burst_fec_1_3_struct.phy_payload.getBits(), self.vector.phy_payload)
        self.assertEqual(coded_payload.single_burst_fec_1_3_struct.getBits(), self.vector.coded_payload)

        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(burst.struct.data.getBits(), self.vector.data)

        self.assertEqual(burst.struct.getBits(), self.vector.radio_burst)
    
    def test_parser(self):
        bitstream = toBinaryArray(self.vector.radio_burst)

        burst = DownlinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data.getSize()])
        burst.struct.data.setBitstream(input)
        self.assertEqual(burst.struct.data.getBits(), self.vector.data)

        frame = DownlinkFrame()
        frame.downlink_0 = burst
        self.parser.parseFrame(frame)
        coded_payload = frame.coded_payload
        self.assertEqual(coded_payload.single_burst_fec_1_3_struct.getBits(), self.vector.coded_payload)
        self.assertEqual(Bits(coded_payload.phy_payload), self.vector.phy_payload)



class MultiBurstTest(unittest.TestCase):

    def setUp(self):
        self.vector = FullDownlinkMultiBurstTestVector()
        self.generator = BurstModeDownlinkGenerator()
        self.parser = BurstModeDownlinkParser()

    def test_generator(self):
        frame = DownlinkFrame()
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
        self.assertEqual(coded_payload.multi_burst_1_struct.getBits(), self.vector.coded_payload_dl1)
        self.assertEqual(coded_payload.multi_burst_2_struct.getBits(), self.vector.coded_payload_dl2)
        self.assertEqual(coded_payload.multi_burst_3_struct.getBits(), self.vector.coded_payload_dl3)

        self.assertEqual(frame.downlink_1.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(frame.downlink_1.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(frame.downlink_1.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(frame.downlink_1.struct.data.getBits(), self.vector.data_dl1)

        self.assertEqual(frame.downlink_2.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(frame.downlink_2.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(frame.downlink_2.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(frame.downlink_2.struct.data.getBits(), self.vector.data_dl2)

        self.assertEqual(frame.downlink_3.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(frame.downlink_3.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(frame.downlink_3.struct.coded_header.getBits(), self.vector.coded_header)
        self.assertEqual(frame.downlink_3.struct.data.getBits(), self.vector.data_dl3)

        self.assertEqual(frame.downlink_1.struct.getBits(), self.vector.radio_burst_dl1)
        self.assertEqual(frame.downlink_2.struct.getBits(), self.vector.radio_burst_dl2)
        self.assertEqual(frame.downlink_3.struct.getBits(), self.vector.radio_burst_dl3)
    
    def test_parser(self):
        # DL1
        bitstream = toBinaryArray(self.vector.radio_burst_dl1)

        burst = DownlinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data.getSize()])
        burst.struct.data.setBitstream(input)
        self.assertEqual(burst.struct.data.getBits(), self.vector.data_dl1)

        burst_dl1 = burst

        # DL2
        bitstream = toBinaryArray(self.vector.radio_burst_dl2)

        burst = DownlinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data.getSize()])
        burst.struct.data.setBitstream(input)
        self.assertEqual(burst.struct.data.getBits(), self.vector.data_dl2)

        burst_dl2 = burst

        # DL3
        bitstream = toBinaryArray(self.vector.radio_burst_dl3)

        burst = DownlinkBurst()
        group1 = FieldGroup([
            burst.struct.preamble,
            burst.struct.syncword,
            burst.struct.coded_header
        ])

        input, bitstream = numpy.split(bitstream, [group1.getSize()])
        group1.setBitstream(input)
        self.assertEqual(burst.struct.preamble.getBits(), self.vector.preamble)
        self.assertEqual(burst.struct.syncword.getBits(), self.vector.sync)
        self.assertEqual(burst.struct.coded_header.getBits(), self.vector.coded_header)
        self.parser.parseCodedHeader(burst)
        coded_header = burst.coded_header
        self.assertEqual(coded_header.struct.version.getBits(), self.vector.version)
        self.assertEqual(coded_header.struct.phy_payload_length.getBits(), self.vector.phy_payload_length)
        self.assertEqual(coded_header.struct.timing_input_value.getBits(), self.vector.timing_input_value)
        self.assertEqual(coded_header.struct.burst_mode.getBits(), self.vector.burst_mode)
        self.assertEqual(coded_header.struct.burst_type.getBits(), self.vector.burst_type)

        input, bitstream = numpy.split(bitstream, [burst.struct.data.getSize()])
        burst.struct.data.setBitstream(input)
        self.assertEqual(burst.struct.data.getBits(), self.vector.data_dl3)

        burst_dl3 = burst

        frame = DownlinkFrame()
        frame.downlink_1 = burst_dl1
        frame.downlink_2 = burst_dl2
        frame.downlink_3 = burst_dl3
        self.parser.parseFrame(frame)
        coded_payload = frame.coded_payload
        self.assertEqual(coded_payload.multi_burst_1_struct.getBits(), self.vector.coded_payload_dl1)
        self.assertEqual(coded_payload.multi_burst_2_struct.getBits(), self.vector.coded_payload_dl2)
        self.assertEqual(coded_payload.multi_burst_3_struct.getBits(), self.vector.coded_payload_dl3)
        self.assertEqual(Bits(coded_payload.phy_payload), self.vector.phy_payload)