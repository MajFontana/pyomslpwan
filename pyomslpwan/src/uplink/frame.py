import numpy
import math
import bitstring
from typing import Union, Optional

import pyomslpwan.src.structs as structs
import pyomslpwan.src.coding as coding
from pyomslpwan.src.uplink.pdu import UplinkBurst, UplinkFrame



def generateCodedLength(crc_codec: coding.CodedLengthCrc, length_data_a):
    assert 4 <= length_data_a <= 384

    coded_length = structs.CodedLength()
    coded_length.length_data_a.setBits(uint=length_data_a)

    crc_input = coded_length.length_data_a.getBitstream()
    crc_output = crc_codec.parity(crc_input)
    coded_length.crc_15.setBitstream(crc_output)

    return coded_length



def parseCodedLength(crc_codec: coding.CodedLengthCrc, coded_length: structs.CodedLength):
    crc_input = coded_length.getNrzStream()
    crc_output = crc_codec.decode(crc_input, soft=True)

    decoded_coded_length = structs.CodedLength()
    decoded_coded_length.length_data_a.setBitstream(crc_output)
    length_data_a = decoded_coded_length.length_data_a.getBits().uint

    assert 4 <= length_data_a <= 384

    return length_data_a



def generateCodedHeader(crc_codec: coding.CodedHeaderCrc, fec_codec: coding.CommonFecEncodingScheme, phy_payload_length, timing_input_value, burst_mode, burst_type) -> structs.CodedHeader:
    assert phy_payload_length >= 5
    match burst_mode:
        case structs.BURST_MODE_SINGLE_BURST:
            assert burst_type in structs.BURST_TYPES_UPLINK_SINGLE_BURST
        case structs.BURST_MODE_MULTI_BURST:
            assert burst_type in structs.BURST_TYPES_UPLINK_MULTI_BURST
    
    coded_header = structs.CodedHeader()
    coded_header.phy_payload_length.setBits(uint=phy_payload_length)
    coded_header.timing_input_value.setBits(uint=timing_input_value)
    coded_header.burst_mode.setBits(uint=burst_mode)
    coded_header.burst_type.setBits(uint=burst_type)

    crc_input = coded_header.crc_systematic.getBitstream()
    crc_output = crc_codec.parity(crc_input)

    coded_header.coded_header_crc.setBitstream(crc_output)

    fec_input = coded_header.fec_systematic.getBitstream()
    fec_parities = fec_codec.encode(fec_input)

    coded_header.fec_parity_ch1.copyFrom(fec_parities.fec_parity_1)
    coded_header.fec_parity_ch2.copyFrom(fec_parities.fec_parity_2)
    coded_header.fec_tail_ch1.copyFrom(fec_parities.fec_tail_1)
    coded_header.fec_tail_ch2.copyFrom(fec_parities.fec_tail_2)

    return coded_header



def parseCodedHeader(crc_codec: coding.CodedHeaderCrc, fec_codec: coding.CommonFecEncodingScheme, coded_header: structs.CodedHeader):
    fec_parities = coding.CommonFecEncodingSchemeParities()
    fec_parities.systematic.setSize(coded_header.fec_systematic.getSize())
    fec_parities.fec_parity_1.setSize(coded_header.fec_parity_ch1.getSize())
    fec_parities.fec_parity_2.setSize(coded_header.fec_parity_ch2.getSize())
    fec_parities.fec_tail_1.setSize(coded_header.fec_tail_ch1.getSize())
    fec_parities.fec_tail_2.setSize(coded_header.fec_tail_ch2.getSize())
    fec_parities.systematic.copyFrom(coded_header.fec_systematic)
    fec_parities.fec_parity_1.copyFrom(coded_header.fec_parity_ch1)
    fec_parities.fec_parity_2.copyFrom(coded_header.fec_parity_ch2)
    fec_parities.fec_tail_1.copyFrom(coded_header.fec_tail_ch1)
    fec_parities.fec_tail_2.copyFrom(coded_header.fec_tail_ch2)
    fec_output = fec_codec.decode(fec_parities, coded_header.fec_systematic.getSize())
    
    crc_input = fec_output
    crc_output = crc_codec.decode(crc_input)

    coded_header.crc_systematic.setBitstream(crc_output)
    version = coded_header.version.getBits().uint
    phy_payload_length = coded_header.phy_payload_length.getBits().uint
    timing_input_value = coded_header.timing_input_value.getBits().uint
    burst_mode = coded_header.burst_mode.getBits().uint
    burst_type = coded_header.burst_type.getBits().uint

    assert version == 0
    assert phy_payload_length >= 5
    match burst_mode:
        case structs.BURST_MODE_SINGLE_BURST:
            assert burst_type in structs.BURST_TYPES_UPLINK_SINGLE_BURST
        case structs.BURST_MODE_MULTI_BURST:
            assert burst_type in structs.BURST_TYPES_UPLINK_MULTI_BURST

    return (phy_payload_length, timing_input_value, burst_mode, burst_type)



def generateCodedPayloadSingleBurst(fec_codec: coding.CommonFecEncodingScheme, interleaver: coding.CommonInterleavingScheme, phy_payload, burst_type):
    bits_payload = len(phy_payload) * 8
    match burst_type:
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
            bits_padding_7_8 = (-bits_payload) % 7
            bits_fec = bits_payload + bits_padding_7_8
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
            bits_fec = bits_payload
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
            bits_fec = bits_payload

    match burst_type:
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
            coded_payload = structs.CodedPayloadSingleBurstFec78()
            coded_payload.phy_payload.setSize(bits_payload)
            coded_payload._7_8_padding.setSize(bits_padding_7_8)
            coded_payload.fec_parity_3a.setSize(bits_fec // 7)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
            coded_payload = structs.CodedPayloadSingleBurstFec12()
            coded_payload.phy_payload.setSize(bits_payload)
            coded_payload.fec_parity_1.setSize(bits_fec)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
            coded_payload = structs.CodedPayloadSingleBurstFec13()
            coded_payload.phy_payload.setSize(bits_payload)
            coded_payload.fec_parity_1.setSize(bits_fec)
            coded_payload.fec_parity_2.setSize(bits_fec)

    match burst_type:
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
            coded_payload.phy_payload.setBits(bytes=phy_payload)
            fec_input = coded_payload.fec_systematic.getBitstream()
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
            coded_payload.phy_payload.setBits(bytes=phy_payload)
            fec_input = coded_payload.phy_payload.getBitstream()
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
            coded_payload.phy_payload.setBits(bytes=phy_payload)
            fec_input = coded_payload.phy_payload.getBitstream()
    
    fec_parities = fec_codec.encode(fec_input)

    match burst_type:
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
            coded_payload.fec_systematic.copyFrom(fec_parities.systematic)
            coded_payload.fec_parity_3a.copyFrom(fec_parities.fec_parity_3a)
            coded_payload.fec_tail_0.copyFrom(fec_parities.fec_tail_0)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
            coded_payload.phy_payload.copyFrom(fec_parities.systematic)
            coded_payload.fec_parity_1.copyFrom(fec_parities.fec_parity_1)
            coded_payload.fec_tail_1.copyFrom(fec_parities.fec_tail_1)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
            coded_payload.phy_payload.copyFrom(fec_parities.systematic)
            coded_payload.fec_parity_1.copyFrom(fec_parities.fec_parity_1)
            coded_payload.fec_tail_1.copyFrom(fec_parities.fec_tail_1)
            coded_payload.fec_parity_2.copyFrom(fec_parities.fec_parity_2)
            coded_payload.fec_tail_2.copyFrom(fec_parities.fec_tail_2)
    
    interleaver_input = coded_payload.getBitstream()
    interleaver_output = interleaver.interleave(interleaver_input)

    return interleaver_output



def generateCodedPayloadMultiBurst(fec_codec: coding.CommonFecEncodingScheme, interleaver: coding.CommonInterleavingScheme, phy_payload):
    bits_payload = len(phy_payload) * 8
    bits_padding_7_8 = (-bits_payload) % 7
    bits_fec = bits_payload + bits_padding_7_8

    coded_payload_1 = structs.CodedPayloadMultiBurst1()
    coded_payload_1.phy_payload.setSize(bits_payload)
    coded_payload_1._7_8_padding.setSize(bits_padding_7_8)
    coded_payload_1.fec_parity_3a.setSize(bits_fec // 7)

    coded_payload_2 = structs.CodedPayloadMultiBurst2()
    coded_payload_2.fec_parity_1.setSize(bits_fec)
    coded_payload_2.fec_parity_3b.setSize(bits_fec // 7)

    coded_payload_3 = structs.CodedPayloadMultiBurst3()
    coded_payload_3.fec_parity_2.setSize(bits_fec)
    coded_payload_3.fec_parity_3c.setSize(bits_fec // 7)

    coded_payload_1.phy_payload.setBits(bytes=phy_payload)
    fec_input = coded_payload_1.fec_systematic.getBitstream()
    
    fec_parities = fec_codec.encode(fec_input)

    coded_payload_1.fec_systematic.copyFrom(fec_parities.systematic)
    coded_payload_1.fec_parity_3a.copyFrom(fec_parities.fec_parity_3a)
    coded_payload_1.fec_tail_0.copyFrom(fec_parities.fec_tail_0)

    coded_payload_2.fec_parity_1.copyFrom(fec_parities.fec_parity_1)
    coded_payload_2.fec_parity_3b.copyFrom(fec_parities.fec_parity_3b)
    coded_payload_2.fec_tail_1.copyFrom(fec_parities.fec_tail_1)

    coded_payload_3.fec_parity_2.copyFrom(fec_parities.fec_parity_2)
    coded_payload_3.fec_parity_3c.copyFrom(fec_parities.fec_parity_3c)
    coded_payload_3.fec_tail_2.copyFrom(fec_parities.fec_tail_2)
    
    interleaver_input_1 = coded_payload_1.getBitstream()
    interleaver_output_1 = interleaver.interleave(interleaver_input_1)

    interleaver_input_2 = coded_payload_2.getBitstream()
    interleaver_output_2 = interleaver.interleave(interleaver_input_2)

    interleaver_input_3 = coded_payload_3.getBitstream()
    interleaver_output_3 = interleaver.interleave(interleaver_input_3)

    return (interleaver_output_1, interleaver_output_2, interleaver_output_3)



def parseCodedPayloadSingleBurst(fec_codec: coding.CommonFecEncodingScheme, interleaver: coding.CommonInterleavingScheme, nrz, phy_payload_length, burst_type):
    bits_payload = phy_payload_length * 8
    match burst_type:
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
            bits_padding_7_8 = (-bits_payload) % 7
            bits_fec = bits_payload + bits_padding_7_8
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
            bits_fec = bits_payload
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
            bits_fec = bits_payload
    
    match burst_type:
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
            coded_payload = structs.CodedPayloadSingleBurstFec78()
            coded_payload.phy_payload.setSize(bits_payload)
            coded_payload._7_8_padding.setSize(bits_padding_7_8)
            coded_payload.fec_parity_3a.setSize(bits_fec // 7)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
            coded_payload = structs.CodedPayloadSingleBurstFec12()
            coded_payload.phy_payload.setSize(bits_payload)
            coded_payload.fec_parity_1.setSize(bits_fec)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
            coded_payload = structs.CodedPayloadSingleBurstFec13()
            coded_payload.phy_payload.setSize(bits_payload)
            coded_payload.fec_parity_1.setSize(bits_fec)
            coded_payload.fec_parity_2.setSize(bits_fec)
    
    interleaver_input = nrz
    interleaver_output = interleaver.deinterleave(interleaver_input)

    match burst_type:
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
            coded_payload.setNrzStream(interleaver_output)
            coded_payload._7_8_padding.setBits(uint=0)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
            coded_payload.setNrzStream(interleaver_output)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
            coded_payload.setNrzStream(interleaver_output)

    fec_parities = coding.CommonFecEncodingSchemeParities()

    match burst_type:
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
            fec_parities.systematic.setSize(bits_fec)
            fec_parities.fec_parity_3a.setSize(bits_fec // 7)
            fec_parities.fec_tail_0.setSize(6)

            fec_parities.systematic.copyFrom(coded_payload.fec_systematic)
            fec_parities.fec_parity_3a.copyFrom(coded_payload.fec_parity_3a)
            fec_parities.fec_tail_0.copyFrom(coded_payload.fec_tail_0)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:

            fec_parities.systematic.setSize(bits_fec)
            fec_parities.fec_parity_1.setSize(bits_fec)
            fec_parities.fec_tail_1.setSize(6)

            fec_parities.systematic.copyFrom(coded_payload.phy_payload)
            fec_parities.fec_parity_1.copyFrom(coded_payload.fec_parity_1)
            fec_parities.fec_tail_1.copyFrom(coded_payload.fec_tail_1)
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
            fec_parities.systematic.setSize(bits_fec)
            fec_parities.fec_parity_1.setSize(bits_fec)
            fec_parities.fec_tail_1.setSize(6)
            fec_parities.fec_parity_2.setSize(bits_fec)
            fec_parities.fec_tail_2.setSize(6)

            fec_parities.systematic.copyFrom(coded_payload.phy_payload)
            fec_parities.fec_parity_1.copyFrom(coded_payload.fec_parity_1)
            fec_parities.fec_tail_1.copyFrom(coded_payload.fec_tail_1)
            fec_parities.fec_parity_2.copyFrom(coded_payload.fec_parity_2)
            fec_parities.fec_tail_2.copyFrom(coded_payload.fec_tail_2)
    
    fec_output = fec_codec.decode(fec_parities, bits_fec)

    match burst_type:
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
            coded_payload.fec_systematic.setBitstream(fec_output)
            phy_payload = coded_payload.phy_payload.getBits().bytes
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
            coded_payload.phy_payload.setBitstream(fec_output)
            phy_payload = coded_payload.phy_payload.getBits().bytes
        case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
            coded_payload.phy_payload.setBitstream(fec_output)
            phy_payload = coded_payload.phy_payload.getBits().bytes
    
    return phy_payload



def parseCodedPayloadMultiBurst(fec_codec: coding.CommonFecEncodingScheme, interleaver: coding.CommonInterleavingScheme, nrzs, phy_payload_length):
    nrz1, nrz2, nrz3 = nrzs

    bits_payload = phy_payload_length * 8
    bits_padding_7_8 = (-bits_payload) % 7
    bits_fec = bits_payload + bits_padding_7_8
    
    coded_payload_1 = structs.CodedPayloadMultiBurst1()
    coded_payload_1.phy_payload.setSize(bits_payload)
    coded_payload_1._7_8_padding.setSize(bits_padding_7_8)
    coded_payload_1.fec_parity_3a.setSize(bits_fec // 7)
    if nrz2 is not None:
        coded_payload_2 = structs.CodedPayloadMultiBurst2()
        coded_payload_2.fec_parity_1.setSize(bits_fec)
        coded_payload_2.fec_parity_3b.setSize(bits_fec // 7)
    if nrz3 is not None:
        coded_payload_3 = structs.CodedPayloadMultiBurst3()
        coded_payload_3.fec_parity_2.setSize(bits_fec)
        coded_payload_3.fec_parity_3c.setSize(bits_fec // 7)
    
    if nrz1 is not None:
        interleaver_input = nrz1
        interleaver_output = interleaver.deinterleave(interleaver_input)
        coded_payload_1.setNrzStream(interleaver_output)
        coded_payload_1._7_8_padding.setBits(uint=0)
    if nrz2 is not None:
        interleaver_input = nrz2
        interleaver_output = interleaver.deinterleave(interleaver_input)
        coded_payload_2.setNrzStream(interleaver_output)
    if nrz3 is not None:
        interleaver_input = nrz3
        interleaver_output = interleaver.deinterleave(interleaver_input)
        coded_payload_3.setNrzStream(interleaver_output)

    fec_parities = coding.CommonFecEncodingSchemeParities()

    if nrz1 is not None:
        fec_parities.systematic.setSize(bits_fec)
        fec_parities.fec_parity_3a.setSize(bits_fec // 7)
        fec_parities.fec_tail_0.setSize(6)

        fec_parities.systematic.copyFrom(coded_payload_1.fec_systematic)
        fec_parities.fec_parity_3a.copyFrom(coded_payload_1.fec_parity_3a)
        fec_parities.fec_tail_0.copyFrom(coded_payload_1.fec_tail_0)

    if nrz2 is not None:
        fec_parities.fec_parity_1.setSize(bits_fec)
        fec_parities.fec_parity_3b.setSize(bits_fec // 7)
        fec_parities.fec_tail_1.setSize(6)

        fec_parities.fec_parity_1.copyFrom(coded_payload_2.fec_parity_1)
        fec_parities.fec_parity_3b.copyFrom(coded_payload_2.fec_parity_3b)
        fec_parities.fec_tail_1.copyFrom(coded_payload_2.fec_tail_1)

    if nrz3 is not None:
        fec_parities.fec_parity_2.setSize(bits_fec)
        fec_parities.fec_parity_3c.setSize(bits_fec // 7)
        fec_parities.fec_tail_2.setSize(6)

        fec_parities.fec_parity_2.copyFrom(coded_payload_3.fec_parity_2)
        fec_parities.fec_parity_3c.copyFrom(coded_payload_3.fec_parity_3c)
        fec_parities.fec_tail_2.copyFrom(coded_payload_3.fec_tail_2)
    
    fec_output = fec_codec.decode(fec_parities, bits_fec)

    coded_payload_1.fec_systematic.setBitstream(fec_output)
    phy_payload = coded_payload_1.phy_payload.getBits().bytes

    return phy_payload



class BurstModeUplinkGenerator:
    
    def __init__(self):
        self.interleaver = coding.CommonInterleavingScheme()
        self.precoder = coding.Precoder()
        self.coded_header_crc_codec = coding.CodedHeaderCrc()
        self.coded_length_crc_codec = coding.CodedLengthCrc()
        self.fec_codec = coding.CommonFecEncodingScheme()

    def generateCodedHeader(self, frame: UplinkFrame):
        # Calculate phy payload length
        frame.coded_header.phy_payload_length = len(frame.coded_payload.phy_payload)

        # Set parameter fields in header struct
        frame.coded_header.struct.phy_payload_length.setBits(uint=frame.coded_header.phy_payload_length)
        frame.coded_header.struct.timing_input_value.setBits(uint=frame.coded_header.timing_input_value)
        frame.coded_header.struct.burst_mode.setBits(uint=frame.coded_header.burst_mode)
        frame.coded_header.struct.burst_type.setBits(uint=frame.coded_header.burst_type)

        # Calculate CRC
        crc_input = frame.coded_header.struct.crc_systematic.getBitstream()
        crc_output = self.coded_header_crc_codec.parity(crc_input)

        # Set CRC field in header struct
        frame.coded_header.struct.coded_header_crc.setBitstream(crc_output)

        # Calculate FEC parities
        fec_input = frame.coded_header.struct.fec_systematic.getBitstream()
        fec_parities = self.fec_codec.encode(fec_input)

        # Set FEC fields in header struct
        frame.coded_header.struct.fec_parity_ch1.copyFrom(fec_parities.fec_parity_1)
        frame.coded_header.struct.fec_parity_ch2.copyFrom(fec_parities.fec_parity_2)
        frame.coded_header.struct.fec_tail_ch1.copyFrom(fec_parities.fec_tail_1)
        frame.coded_header.struct.fec_tail_ch2.copyFrom(fec_parities.fec_tail_2)
    
    def generateCodedPayload(self, frame: UplinkFrame):
        # Calculate sizes for coded payload
        frame.coded_payload.bits_payload = frame.coded_header.phy_payload_length * 8
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                match frame.coded_header.burst_type:
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        frame.coded_payload.bits_padding_7_8 = (-frame.coded_payload.bits_payload) % 7
                        frame.coded_payload.bits_fec = frame.coded_payload.bits_payload + frame.coded_payload.bits_padding_7_8
                        frame.coded_payload.bits_coded_payload = frame.coded_payload.bits_fec * 8 // 7 + 8
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        frame.coded_payload.bits_fec = frame.coded_payload.bits_payload
                        frame.coded_payload.bits_coded_payload = frame.coded_payload.bits_fec * 2 + 8
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        frame.coded_payload.bits_fec = frame.coded_payload.bits_payload
                        frame.coded_payload.bits_coded_payload = frame.coded_payload.bits_fec * 3 + 16
            case structs.BURST_MODE_MULTI_BURST:
                frame.coded_payload.bits_padding_7_8 = (-frame.coded_payload.bits_payload) % 7
                frame.coded_payload.bits_fec = frame.coded_payload.bits_payload + frame.coded_payload.bits_padding_7_8
                frame.coded_payload.bits_coded_payload = frame.coded_payload.bits_fec * 8 // 7 + 8

        # Create coded payload structs and set sizes of coded payload fields
        match frame.coded_header.burst_mode:

            case structs.BURST_MODE_SINGLE_BURST:
                match frame.coded_header.burst_type:

                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        frame.coded_payload.single_burst_fec_7_8_struct = structs.CodedPayloadSingleBurstFec78()
                        frame.coded_payload.single_burst_fec_7_8_struct.phy_payload.setSize(frame.coded_payload.bits_payload)
                        frame.coded_payload.single_burst_fec_7_8_struct._7_8_padding.setSize(frame.coded_payload.bits_padding_7_8)
                        frame.coded_payload.single_burst_fec_7_8_struct.fec_parity_3a.setSize(frame.coded_payload.bits_fec // 7)

                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        frame.coded_payload.single_burst_fec_1_2_struct = structs.CodedPayloadSingleBurstFec12()
                        frame.coded_payload.single_burst_fec_1_2_struct.phy_payload.setSize(frame.coded_payload.bits_payload)
                        frame.coded_payload.single_burst_fec_1_2_struct.fec_parity_1.setSize(frame.coded_payload.bits_fec)

                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        frame.coded_payload.single_burst_fec_1_3_struct = structs.CodedPayloadSingleBurstFec13()
                        frame.coded_payload.single_burst_fec_1_3_struct.phy_payload.setSize(frame.coded_payload.bits_payload)
                        frame.coded_payload.single_burst_fec_1_3_struct.fec_parity_1.setSize(frame.coded_payload.bits_fec)
                        frame.coded_payload.single_burst_fec_1_3_struct.fec_parity_2.setSize(frame.coded_payload.bits_fec)

            case structs.BURST_MODE_MULTI_BURST:

                frame.coded_payload.multi_burst_1_struct = structs.CodedPayloadMultiBurst1()
                frame.coded_payload.multi_burst_1_struct.phy_payload.setSize(frame.coded_payload.bits_payload)
                frame.coded_payload.multi_burst_1_struct._7_8_padding.setSize(frame.coded_payload.bits_padding_7_8)
                frame.coded_payload.multi_burst_1_struct.fec_parity_3a.setSize(frame.coded_payload.bits_fec // 7)

                frame.coded_payload.multi_burst_2_struct = structs.CodedPayloadMultiBurst2()
                frame.coded_payload.multi_burst_2_struct.fec_parity_1.setSize(frame.coded_payload.bits_fec)
                frame.coded_payload.multi_burst_2_struct.fec_parity_3b.setSize(frame.coded_payload.bits_fec // 7)

                frame.coded_payload.multi_burst_3_struct = structs.CodedPayloadMultiBurst3()
                frame.coded_payload.multi_burst_3_struct.fec_parity_2.setSize(frame.coded_payload.bits_fec)
                frame.coded_payload.multi_burst_3_struct.fec_parity_3c.setSize(frame.coded_payload.bits_fec // 7)

        # Set phy_payload field in coded payload struct and prepare FEC input
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                match frame.coded_header.burst_type:
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        frame.coded_payload.single_burst_fec_7_8_struct.phy_payload.setBits(bytes=frame.coded_payload.phy_payload)
                        fec_input = frame.coded_payload.single_burst_fec_7_8_struct.fec_systematic.getBitstream()
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        frame.coded_payload.single_burst_fec_1_2_struct.phy_payload.setBits(bytes=frame.coded_payload.phy_payload)
                        fec_input = frame.coded_payload.single_burst_fec_1_2_struct.phy_payload.getBitstream()
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        frame.coded_payload.single_burst_fec_1_3_struct.phy_payload.setBits(bytes=frame.coded_payload.phy_payload)
                        fec_input = frame.coded_payload.single_burst_fec_1_3_struct.phy_payload.getBitstream()
            case structs.BURST_MODE_MULTI_BURST:
                frame.coded_payload.multi_burst_1_struct.phy_payload.setBits(bytes=frame.coded_payload.phy_payload)
                fec_input = frame.coded_payload.multi_burst_1_struct.fec_systematic.getBitstream()
        
        # Calculate FEC parities
        fec_parities = self.fec_codec.encode(fec_input)
        frame.coded_payload.fec_parities = fec_parities

        # Set FEC fields in coded payload struct
        match frame.coded_header.burst_mode:

            case structs.BURST_MODE_SINGLE_BURST:
                match frame.coded_header.burst_type:

                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        frame.coded_payload.single_burst_fec_7_8_struct.fec_systematic.copyFrom(frame.coded_payload.fec_parities.systematic)
                        frame.coded_payload.single_burst_fec_7_8_struct.fec_parity_3a.copyFrom(frame.coded_payload.fec_parities.fec_parity_3a)
                        frame.coded_payload.single_burst_fec_7_8_struct.fec_tail_0.copyFrom(frame.coded_payload.fec_parities.fec_tail_0)

                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        frame.coded_payload.single_burst_fec_1_2_struct.phy_payload.copyFrom(frame.coded_payload.fec_parities.systematic)
                        frame.coded_payload.single_burst_fec_1_2_struct.fec_parity_1.copyFrom(frame.coded_payload.fec_parities.fec_parity_1)
                        frame.coded_payload.single_burst_fec_1_2_struct.fec_tail_1.copyFrom(frame.coded_payload.fec_parities.fec_tail_1)

                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        frame.coded_payload.single_burst_fec_1_3_struct.phy_payload.copyFrom(frame.coded_payload.fec_parities.systematic)
                        frame.coded_payload.single_burst_fec_1_3_struct.fec_parity_1.copyFrom(frame.coded_payload.fec_parities.fec_parity_1)
                        frame.coded_payload.single_burst_fec_1_3_struct.fec_tail_1.copyFrom(frame.coded_payload.fec_parities.fec_tail_1)
                        frame.coded_payload.single_burst_fec_1_3_struct.fec_parity_2.copyFrom(frame.coded_payload.fec_parities.fec_parity_2)
                        frame.coded_payload.single_burst_fec_1_3_struct.fec_tail_2.copyFrom(frame.coded_payload.fec_parities.fec_tail_2)

            case structs.BURST_MODE_MULTI_BURST:

                frame.coded_payload.multi_burst_1_struct.fec_systematic.copyFrom(frame.coded_payload.fec_parities.systematic)
                frame.coded_payload.multi_burst_1_struct.fec_parity_3a.copyFrom(frame.coded_payload.fec_parities.fec_parity_3a)
                frame.coded_payload.multi_burst_1_struct.fec_tail_0.copyFrom(frame.coded_payload.fec_parities.fec_tail_0)

                frame.coded_payload.multi_burst_2_struct.fec_parity_1.copyFrom(frame.coded_payload.fec_parities.fec_parity_1)
                frame.coded_payload.multi_burst_2_struct.fec_parity_3b.copyFrom(frame.coded_payload.fec_parities.fec_parity_3b)
                frame.coded_payload.multi_burst_2_struct.fec_tail_1.copyFrom(frame.coded_payload.fec_parities.fec_tail_1)

                frame.coded_payload.multi_burst_3_struct.fec_parity_2.copyFrom(frame.coded_payload.fec_parities.fec_parity_2)
                frame.coded_payload.multi_burst_3_struct.fec_parity_3c.copyFrom(frame.coded_payload.fec_parities.fec_parity_3c)
                frame.coded_payload.multi_burst_3_struct.fec_tail_2.copyFrom(frame.coded_payload.fec_parities.fec_tail_2)
        
    def generateData(self, frame: UplinkFrame):
        # Calculate data field lengths
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                frame.uplink_0.length_data = frame.coded_payload.bits_coded_payload // 8
                frame.uplink_0.length_data_a = math.ceil(frame.uplink_0.length_data / 2)
                frame.uplink_0.length_data_b = frame.uplink_0.length_data - frame.uplink_0.length_data_a
            case structs.BURST_MODE_MULTI_BURST:
                frame.uplink_1.length_data = frame.coded_payload.bits_coded_payload // 8
                frame.uplink_1.length_data_a = math.ceil(frame.uplink_1.length_data / 2)
                frame.uplink_1.length_data_b = frame.uplink_1.length_data - frame.uplink_1.length_data_a

                frame.uplink_2.length_data = frame.coded_payload.bits_coded_payload // 8
                frame.uplink_2.length_data_a = math.ceil(frame.uplink_2.length_data / 2)
                frame.uplink_2.length_data_b = frame.uplink_2.length_data - frame.uplink_2.length_data_a

                frame.uplink_3.length_data = frame.coded_payload.bits_coded_payload // 8
                frame.uplink_3.length_data_a = math.ceil(frame.uplink_3.length_data / 2)
                frame.uplink_3.length_data_b = frame.uplink_3.length_data - frame.uplink_3.length_data_a
        
        # Set data field sizes
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                frame.uplink_0.struct.data_a.setSize(frame.uplink_0.length_data_a * 8)
                frame.uplink_0.struct.data_b.setSize(frame.uplink_0.length_data_b * 8)
            case structs.BURST_MODE_MULTI_BURST:
                frame.uplink_1.struct.data_a.setSize(frame.uplink_1.length_data_a * 8)
                frame.uplink_1.struct.data_b.setSize(frame.uplink_1.length_data_b * 8)

                frame.uplink_2.struct.data_a.setSize(frame.uplink_2.length_data_a * 8)
                frame.uplink_2.struct.data_b.setSize(frame.uplink_2.length_data_b * 8)

                frame.uplink_3.struct.data_a.setSize(frame.uplink_3.length_data_a * 8)
                frame.uplink_3.struct.data_b.setSize(frame.uplink_3.length_data_b * 8)

        # Retrieve and interleave coded payload bitstreams
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                match frame.coded_header.burst_type:
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        interleaver_input = frame.coded_payload.single_burst_fec_7_8_struct.getBitstream()
                        interleaver_output = self.interleaver.interleave(interleaver_input)
                        frame.uplink_0.data_bitstream = interleaver_output
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        interleaver_input = frame.coded_payload.single_burst_fec_1_2_struct.getBitstream()
                        interleaver_output = self.interleaver.interleave(interleaver_input)
                        frame.uplink_0.data_bitstream = interleaver_output
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        interleaver_input = frame.coded_payload.single_burst_fec_1_3_struct.getBitstream()
                        interleaver_output = self.interleaver.interleave(interleaver_input)
                        frame.uplink_0.data_bitstream = interleaver_output
            case structs.BURST_MODE_MULTI_BURST:
                interleaver_input = frame.coded_payload.multi_burst_1_struct.getBitstream()
                interleaver_output = self.interleaver.interleave(interleaver_input)
                frame.uplink_1.data_bitstream = interleaver_output

                interleaver_input = frame.coded_payload.multi_burst_2_struct.getBitstream()
                interleaver_output = self.interleaver.interleave(interleaver_input)
                frame.uplink_2.data_bitstream = interleaver_output

                interleaver_input = frame.coded_payload.multi_burst_3_struct.getBitstream()
                interleaver_output = self.interleaver.interleave(interleaver_input)
                frame.uplink_3.data_bitstream = interleaver_output
        
        # Set data fields
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                frame.uplink_0.struct.data_a.setBitstream(frame.uplink_0.data_bitstream[:frame.uplink_0.length_data_a * 8])
                frame.uplink_0.struct.data_b.setBitstream(frame.uplink_0.data_bitstream[frame.uplink_0.length_data_a * 8:])
            case structs.BURST_MODE_MULTI_BURST:
                frame.uplink_1.struct.data_a.setBitstream(frame.uplink_1.data_bitstream[:frame.uplink_1.length_data_a * 8])
                frame.uplink_1.struct.data_b.setBitstream(frame.uplink_1.data_bitstream[frame.uplink_1.length_data_a * 8:])

                frame.uplink_2.struct.data_a.setBitstream(frame.uplink_2.data_bitstream[:frame.uplink_2.length_data_a * 8])
                frame.uplink_2.struct.data_b.setBitstream(frame.uplink_2.data_bitstream[frame.uplink_2.length_data_a * 8:])

                frame.uplink_3.struct.data_a.setBitstream(frame.uplink_3.data_bitstream[:frame.uplink_3.length_data_a * 8])
                frame.uplink_3.struct.data_b.setBitstream(frame.uplink_3.data_bitstream[frame.uplink_3.length_data_a * 8:])
    
    def generateCodedLength(self, frame: UplinkFrame):
        # Retrieve data a length
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                frame.uplink_0.coded_length.length_data_a = frame.uplink_0.length_data_a
            case structs.BURST_MODE_MULTI_BURST:
                frame.uplink_1.coded_length.length_data_a = frame.uplink_1.length_data_a
                frame.uplink_2.coded_length.length_data_a = frame.uplink_2.length_data_a
                frame.uplink_3.coded_length.length_data_a = frame.uplink_3.length_data_a
        
        # Calculate crc parity and set coded length fields
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                frame.uplink_0.coded_length.struct.length_data_a.setBits(uint=frame.uplink_0.coded_length.length_data_a)
                crc_input = frame.uplink_0.coded_length.struct.length_data_a.getBitstream()
                crc_output = self.coded_length_crc_codec.parity(crc_input)
                frame.uplink_0.coded_length.struct.crc_15.setBitstream(crc_output)
            case structs.BURST_MODE_MULTI_BURST:
                frame.uplink_1.coded_length.struct.length_data_a.setBits(uint=frame.uplink_1.coded_length.length_data_a)
                crc_input = frame.uplink_1.coded_length.struct.length_data_a.getBitstream()
                crc_output = self.coded_length_crc_codec.parity(crc_input)
                frame.uplink_1.coded_length.struct.crc_15.setBitstream(crc_output)

                frame.uplink_2.coded_length.struct.length_data_a.setBits(uint=frame.uplink_2.coded_length.length_data_a)
                crc_input = frame.uplink_2.coded_length.struct.length_data_a.getBitstream()
                crc_output = self.coded_length_crc_codec.parity(crc_input)
                frame.uplink_2.coded_length.struct.crc_15.setBitstream(crc_output)

                frame.uplink_3.coded_length.struct.length_data_a.setBits(uint=frame.uplink_3.coded_length.length_data_a)
                crc_input = frame.uplink_3.coded_length.struct.length_data_a.getBitstream()
                crc_output = self.coded_length_crc_codec.parity(crc_input)
                frame.uplink_3.coded_length.struct.crc_15.setBitstream(crc_output)
    
    def generateFrame(self, frame: UplinkFrame):
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                frame.uplink_0 = UplinkBurst()
            case structs.BURST_MODE_MULTI_BURST:
                frame.uplink_1 = UplinkBurst()
                frame.uplink_2 = UplinkBurst()
                frame.uplink_3 = UplinkBurst()

        self.generateCodedHeader(frame)
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                frame.uplink_0.struct.coded_header.copyFrom(frame.coded_header.struct)
            case structs.BURST_MODE_MULTI_BURST:
                frame.uplink_1.struct.coded_header.copyFrom(frame.coded_header.struct)
                frame.uplink_2.struct.coded_header.copyFrom(frame.coded_header.struct)
                frame.uplink_3.struct.coded_header.copyFrom(frame.coded_header.struct)
        
        self.generateCodedPayload(frame)
        self.generateData(frame)

        self.generateCodedLength(frame)
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                frame.uplink_0.struct.coded_length.copyFrom(frame.uplink_0.coded_length.struct)
            case structs.BURST_MODE_MULTI_BURST:
                frame.uplink_1.struct.coded_length.copyFrom(frame.uplink_1.coded_length.struct)
                frame.uplink_2.struct.coded_length.copyFrom(frame.uplink_2.coded_length.struct)
                frame.uplink_3.struct.coded_length.copyFrom(frame.uplink_3.coded_length.struct)
        
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                precoder_input = frame.uplink_0.struct.getBitstream()
                precoder_output = self.precoder.encode(precoder_input)
                frame.uplink_0.bitstream = precoder_output
            case structs.BURST_MODE_MULTI_BURST:
                precoder_input = frame.uplink_1.struct.getBitstream()
                precoder_output = self.precoder.encode(precoder_input)
                frame.uplink_1.bitstream = precoder_output

                precoder_input = frame.uplink_2.struct.getBitstream()
                precoder_output = self.precoder.encode(precoder_input)
                frame.uplink_2.bitstream = precoder_output

                precoder_input = frame.uplink_3.struct.getBitstream()
                precoder_output = self.precoder.encode(precoder_input)
                frame.uplink_3.bitstream = precoder_output



class BurstModeUplinkParser:

    def __init__(self):
        self.interleaver = coding.CommonInterleavingScheme()
        self.precoder = coding.Precoder()
        self.coded_header_crc_codec = coding.CodedHeaderCrc()
        self.coded_length_crc_codec = coding.CodedLengthCrc()
        self.fec_codec = coding.CommonFecEncodingScheme()

    def parseCodedLength(self, burst: UplinkBurst):
        crc_input = burst.struct.coded_length.getNrzStream()
        crc_output = self.coded_length_crc_codec.decode(crc_input, soft=True)

        burst.coded_length.struct.length_data_a.setBitstream(crc_output)
        burst.coded_length.length_data_a = burst.coded_length.struct.length_data_a.getBits().uint

        assert 4 <= burst.coded_length.length_data_a <= 384

        burst.struct.data_a.setSize(burst.coded_length.length_data_a * 8)

    def parseCodedHeader(self, burst: UplinkBurst):
        fec_parities = coding.CommonFecEncodingSchemeParities()
        fec_parities.systematic.setSize(28)
        fec_parities.fec_parity_1.setSize(28)
        fec_parities.fec_parity_2.setSize(28)
        fec_parities.fec_tail_1.setSize(6)
        fec_parities.fec_tail_2.setSize(6)
        fec_parities.systematic.copyFrom(burst.struct.coded_header.fec_systematic)
        fec_parities.fec_parity_1.copyFrom(burst.struct.coded_header.fec_parity_ch1)
        fec_parities.fec_parity_2.copyFrom(burst.struct.coded_header.fec_parity_ch2)
        fec_parities.fec_tail_1.copyFrom(burst.struct.coded_header.fec_tail_ch1)
        fec_parities.fec_tail_2.copyFrom(burst.struct.coded_header.fec_tail_ch2)
        fec_output = self.fec_codec.decode(fec_parities, burst.struct.coded_header.fec_systematic.getSize())
        
        crc_input = fec_output
        crc_output = self.coded_header_crc_codec.decode(crc_input)

        burst.coded_header.struct.crc_systematic.setBitstream(crc_output)
        burst.coded_header.version = burst.coded_header.struct.version.getBits().uint
        burst.coded_header.phy_payload_length = burst.coded_header.struct.phy_payload_length.getBits().uint
        burst.coded_header.timing_input_value = burst.coded_header.struct.timing_input_value.getBits().uint
        burst.coded_header.burst_mode = burst.coded_header.struct.burst_mode.getBits().uint
        burst.coded_header.burst_type = burst.coded_header.struct.burst_type.getBits().uint

        assert burst.coded_header.version == 0
        assert burst.coded_header.phy_payload_length >= 5
        match burst.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                assert burst.coded_header.burst_type in structs.BURST_TYPES_UPLINK_SINGLE_BURST
            case structs.BURST_MODE_MULTI_BURST:
                assert burst.coded_header.burst_type in structs.BURST_TYPES_UPLINK_MULTI_BURST

        burst.coded_payload.bits_payload = burst.coded_header.phy_payload_length * 8
        match burst.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                match burst.coded_header.burst_type:
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        burst.coded_payload.bits_padding_7_8 = (-burst.coded_payload.bits_payload) % 7
                        burst.coded_payload.bits_fec = burst.coded_payload.bits_payload + burst.coded_payload.bits_padding_7_8
                        burst.coded_payload.bits_coded_payload = burst.coded_payload.bits_fec * 8 // 7 + 8
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        burst.coded_payload.bits_fec = burst.coded_payload.bits_payload
                        burst.coded_payload.bits_coded_payload = burst.coded_payload.bits_fec * 2 + 8
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        burst.coded_payload.bits_fec = burst.coded_payload.bits_payload
                        burst.coded_payload.bits_coded_payload = burst.coded_payload.bits_fec * 3 + 16
            case structs.BURST_MODE_MULTI_BURST:
                burst.coded_payload.bits_padding_7_8 = (-burst.coded_payload.bits_payload) % 7
                burst.coded_payload.bits_fec = burst.coded_payload.bits_payload + burst.coded_payload.bits_padding_7_8
                burst.coded_payload.bits_coded_payload = burst.coded_payload.bits_fec * 8 // 7 + 8
        
        burst.length_data = burst.coded_payload.bits_coded_payload // 8
        burst.length_data_a = math.ceil(burst.length_data / 2)
        burst.length_data_b = burst.length_data - burst.length_data_a

        if burst.struct.data_a.getSize() == 0:
            burst.struct.data_a.setSize(burst.length_data_a * 8)
        burst.struct.data_b.setSize(burst.length_data_b * 8)
    
    def parseData(self, burst: UplinkBurst):
        burst.data_bitstream = numpy.concatenate([burst.struct.data_a.getNrzStream(), burst.struct.data_b.getNrzStream()])
    
    def parseFrame(self, frame: UplinkFrame):
        if frame.uplink_0 is not None:
            frame.coded_header = frame.uplink_0.coded_header
        elif frame.uplink_1 is not None:
            frame.coded_header = frame.uplink_1.coded_header
        elif frame.uplink_2 is not None:
            frame.coded_header = frame.uplink_2.coded_header
        elif frame.uplink_3 is not None:
            frame.coded_header = frame.uplink_3.coded_header

        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                frame.coded_payload = frame.uplink_0.coded_payload
            case structs.BURST_MODE_MULTI_BURST:
                if frame.uplink_1 is not None:
                    frame.coded_payload = frame.uplink_1.coded_payload
                elif frame.uplink_2 is not None:
                    frame.coded_payload = frame.uplink_2.coded_payload
                elif frame.uplink_3 is not None:
                    frame.coded_payload = frame.uplink_3.coded_payload
        
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                match frame.coded_header.burst_type:
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        frame.coded_payload.single_burst_fec_7_8_struct = structs.CodedPayloadSingleBurstFec78()
                        frame.coded_payload.single_burst_fec_7_8_struct.phy_payload.setSize(frame.coded_payload.bits_payload)
                        frame.coded_payload.single_burst_fec_7_8_struct._7_8_padding.setSize(frame.coded_payload.bits_padding_7_8)
                        frame.coded_payload.single_burst_fec_7_8_struct.fec_parity_3a.setSize(frame.coded_payload.bits_fec // 7)
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        frame.coded_payload.single_burst_fec_1_2_struct = structs.CodedPayloadSingleBurstFec12()
                        frame.coded_payload.single_burst_fec_1_2_struct.phy_payload.setSize(frame.coded_payload.bits_payload)
                        frame.coded_payload.single_burst_fec_1_2_struct.fec_parity_1.setSize(frame.coded_payload.bits_fec)
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        frame.coded_payload.single_burst_fec_1_3_struct = structs.CodedPayloadSingleBurstFec13()
                        frame.coded_payload.single_burst_fec_1_3_struct.phy_payload.setSize(frame.coded_payload.bits_payload)
                        frame.coded_payload.single_burst_fec_1_3_struct.fec_parity_1.setSize(frame.coded_payload.bits_fec)
                        frame.coded_payload.single_burst_fec_1_3_struct.fec_parity_2.setSize(frame.coded_payload.bits_fec)
            case structs.BURST_MODE_MULTI_BURST:
                if frame.uplink_1 is not None:
                    frame.coded_payload.multi_burst_1_struct = structs.CodedPayloadMultiBurst1()
                    frame.coded_payload.multi_burst_1_struct.phy_payload.setSize(frame.coded_payload.bits_payload)
                    frame.coded_payload.multi_burst_1_struct._7_8_padding.setSize(frame.coded_payload.bits_padding_7_8)
                    frame.coded_payload.multi_burst_1_struct.fec_parity_3a.setSize(frame.coded_payload.bits_fec // 7)
                if frame.uplink_2 is not None:
                    frame.coded_payload.multi_burst_2_struct = structs.CodedPayloadMultiBurst2()
                    frame.coded_payload.multi_burst_2_struct.fec_parity_1.setSize(frame.coded_payload.bits_fec)
                    frame.coded_payload.multi_burst_2_struct.fec_parity_3b.setSize(frame.coded_payload.bits_fec // 7)
                if frame.uplink_3 is not None:
                    frame.coded_payload.multi_burst_3_struct = structs.CodedPayloadMultiBurst3()
                    frame.coded_payload.multi_burst_3_struct.fec_parity_2.setSize(frame.coded_payload.bits_fec)
                    frame.coded_payload.multi_burst_3_struct.fec_parity_3c.setSize(frame.coded_payload.bits_fec // 7)
        
        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                match frame.coded_header.burst_type:
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        interleaver_input = frame.uplink_0.data_bitstream
                        interleaver_output = self.interleaver.deinterleave(interleaver_input)
                        frame.coded_payload.single_burst_fec_7_8_struct.setNrzStream(interleaver_output)
                        frame.coded_payload.single_burst_fec_7_8_struct._7_8_padding.setBits(uint=0)
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        interleaver_input = frame.uplink_0.data_bitstream
                        interleaver_output = self.interleaver.deinterleave(interleaver_input)
                        frame.coded_payload.single_burst_fec_1_2_struct.setNrzStream(interleaver_output)
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        interleaver_input = frame.uplink_0.data_bitstream
                        interleaver_output = self.interleaver.deinterleave(interleaver_input)
                        frame.coded_payload.single_burst_fec_1_3_struct.setNrzStream(interleaver_output)
            case structs.BURST_MODE_MULTI_BURST:
                if frame.uplink_1 is not None:
                    interleaver_input = frame.uplink_1.data_bitstream
                    interleaver_output = self.interleaver.deinterleave(interleaver_input)
                    frame.coded_payload.multi_burst_1_struct.setNrzStream(interleaver_output)
                    frame.coded_payload.multi_burst_1_struct._7_8_padding.setBits(uint=0)
                if frame.uplink_2 is not None:
                    interleaver_input = frame.uplink_2.data_bitstream
                    interleaver_output = self.interleaver.deinterleave(interleaver_input)
                    frame.coded_payload.multi_burst_2_struct.setNrzStream(interleaver_output)
                if frame.uplink_3 is not None:
                    interleaver_input = frame.uplink_3.data_bitstream
                    interleaver_output = self.interleaver.deinterleave(interleaver_input)
                    frame.coded_payload.multi_burst_3_struct.setNrzStream(interleaver_output)

        match frame.coded_header.burst_mode:

            case structs.BURST_MODE_SINGLE_BURST:
                match frame.coded_header.burst_type:

                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        frame.coded_payload.fec_parities.systematic.setSize(frame.coded_payload.bits_fec)
                        frame.coded_payload.fec_parities.fec_parity_3a.setSize(frame.coded_payload.bits_fec // 7)
                        frame.coded_payload.fec_parities.fec_tail_0.setSize(6)

                        frame.coded_payload.fec_parities.systematic.copyFrom(frame.coded_payload.single_burst_fec_7_8_struct.fec_systematic)
                        frame.coded_payload.fec_parities.fec_parity_3a.copyFrom(frame.coded_payload.single_burst_fec_7_8_struct.fec_parity_3a)
                        frame.coded_payload.fec_parities.fec_tail_0.copyFrom(frame.coded_payload.single_burst_fec_7_8_struct.fec_tail_0)

                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        frame.coded_payload.fec_parities.systematic.setSize(frame.coded_payload.bits_fec)
                        frame.coded_payload.fec_parities.fec_parity_1.setSize(frame.coded_payload.bits_fec)
                        frame.coded_payload.fec_parities.fec_tail_1.setSize(6)

                        frame.coded_payload.fec_parities.systematic.copyFrom(frame.coded_payload.single_burst_fec_1_2_struct.phy_payload)
                        frame.coded_payload.fec_parities.fec_parity_1.copyFrom(frame.coded_payload.single_burst_fec_1_2_struct.fec_parity_1)
                        frame.coded_payload.fec_parities.fec_tail_1.copyFrom(frame.coded_payload.single_burst_fec_1_2_struct.fec_tail_1)

                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        frame.coded_payload.fec_parities.systematic.setSize(frame.coded_payload.bits_fec)
                        frame.coded_payload.fec_parities.fec_parity_1.setSize(frame.coded_payload.bits_fec)
                        frame.coded_payload.fec_parities.fec_tail_1.setSize(6)
                        frame.coded_payload.fec_parities.fec_parity_2.setSize(frame.coded_payload.bits_fec)
                        frame.coded_payload.fec_parities.fec_tail_2.setSize(6)

                        frame.coded_payload.fec_parities.systematic.copyFrom(frame.coded_payload.single_burst_fec_1_3_struct.phy_payload)
                        frame.coded_payload.fec_parities.fec_parity_1.copyFrom(frame.coded_payload.single_burst_fec_1_3_struct.fec_parity_1)
                        frame.coded_payload.fec_parities.fec_tail_1.copyFrom(frame.coded_payload.single_burst_fec_1_3_struct.fec_tail_1)
                        frame.coded_payload.fec_parities.fec_parity_2.copyFrom(frame.coded_payload.single_burst_fec_1_3_struct.fec_parity_2)
                        frame.coded_payload.fec_parities.fec_tail_2.copyFrom(frame.coded_payload.single_burst_fec_1_3_struct.fec_tail_2)

            case structs.BURST_MODE_MULTI_BURST:

                if frame.uplink_1 is not None:
                    frame.coded_payload.fec_parities.systematic.setSize(frame.coded_payload.bits_fec)
                    frame.coded_payload.fec_parities.fec_parity_3a.setSize(frame.coded_payload.bits_fec // 7)
                    frame.coded_payload.fec_parities.fec_tail_0.setSize(6)

                    frame.coded_payload.fec_parities.systematic.copyFrom(frame.coded_payload.multi_burst_1_struct.fec_systematic)
                    frame.coded_payload.fec_parities.fec_parity_3a.copyFrom(frame.coded_payload.multi_burst_1_struct.fec_parity_3a)
                    frame.coded_payload.fec_parities.fec_tail_0.copyFrom(frame.coded_payload.multi_burst_1_struct.fec_tail_0)

                if frame.uplink_2 is not None:
                    frame.coded_payload.fec_parities.fec_parity_1.setSize(frame.coded_payload.bits_fec)
                    frame.coded_payload.fec_parities.fec_parity_3b.setSize(frame.coded_payload.bits_fec // 7)
                    frame.coded_payload.fec_parities.fec_tail_1.setSize(6)

                    frame.coded_payload.fec_parities.fec_parity_1.copyFrom(frame.coded_payload.multi_burst_2_struct.fec_parity_1)
                    frame.coded_payload.fec_parities.fec_parity_3b.copyFrom(frame.coded_payload.multi_burst_2_struct.fec_parity_3b)
                    frame.coded_payload.fec_parities.fec_tail_1.copyFrom(frame.coded_payload.multi_burst_2_struct.fec_tail_1)

                if frame.uplink_3 is not None:
                    frame.coded_payload.fec_parities.fec_parity_2.setSize(frame.coded_payload.bits_fec)
                    frame.coded_payload.fec_parities.fec_parity_3c.setSize(frame.coded_payload.bits_fec // 7)
                    frame.coded_payload.fec_parities.fec_tail_2.setSize(6)

                    frame.coded_payload.fec_parities.fec_parity_2.copyFrom(frame.coded_payload.multi_burst_3_struct.fec_parity_2)
                    frame.coded_payload.fec_parities.fec_parity_3c.copyFrom(frame.coded_payload.multi_burst_3_struct.fec_parity_3c)
                    frame.coded_payload.fec_parities.fec_tail_2.copyFrom(frame.coded_payload.multi_burst_3_struct.fec_tail_2)
        
        fec_parities = frame.coded_payload.fec_parities
        fec_output = self.fec_codec.decode(fec_parities, frame.coded_payload.bits_fec)

        match frame.coded_header.burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                match frame.coded_header.burst_type:
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8:
                        frame.uplink_0.coded_payload.single_burst_fec_7_8_struct.fec_systematic.setBitstream(fec_output)
                        frame.coded_payload.phy_payload = frame.uplink_0.coded_payload.single_burst_fec_7_8_struct.phy_payload.getBits().bytes
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2:
                        frame.uplink_0.coded_payload.single_burst_fec_1_2_struct.phy_payload.setBitstream(fec_output)
                        frame.coded_payload.phy_payload = frame.uplink_0.coded_payload.single_burst_fec_1_2_struct.phy_payload.getBits().bytes
                    case structs.BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
                        frame.uplink_0.coded_payload.single_burst_fec_1_3_struct.phy_payload.setBitstream(fec_output)
                        frame.coded_payload.phy_payload = frame.uplink_0.coded_payload.single_burst_fec_1_3_struct.phy_payload.getBits().bytes
            case structs.BURST_MODE_MULTI_BURST:
                frame.uplink_1.coded_payload.multi_burst_1_struct.fec_systematic.setBitstream(fec_output)
                frame.coded_payload.phy_payload = frame.uplink_1.coded_payload.multi_burst_1_struct.phy_payload.getBits().bytes
