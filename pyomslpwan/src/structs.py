from pyomslpwan.lib.fields import *



BURST_MODES = [BURST_MODE_SINGLE_BURST := 0,
               BURST_MODE_MULTI_BURST := 1]



BURST_TYPES_UPLINK_SINGLE_BURST = [BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_7_8 := 0,
                                   BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_2 := 1,
                                   BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3 := 2]

BURST_TYPES_UPLINK_MULTI_BURST = [BURST_TYPE_UPLINK_MULTI_BURST_TIMING_1 := 0,
                                  BURST_TYPE_UPLINK_MULTI_BURST_TIMING_2 := 1,
                                  BURST_TYPE_UPLINK_MULTI_BURST_TIMING_3 := 2]

BURST_TYPES_DOWNLINK_SINGLE_BURST = [BURST_TYPE_DOWNLINK_SINGLE_BURST_FEC_RATE_7_8 := 0,
                                     BURST_TYPE_DOWNLINK_SINGLE_BURST_FEC_RATE_1_2 := 1,
                                     BURST_TYPE_DOWNLINK_SINGLE_BURST_FEC_RATE_1_3 := 2]

BURST_TYPES_DOWNLINK_MULTI_BURST = [BURST_TYPE_DOWNLINK_MULTI_BURST := 0]



SUB_MODES_UPLINK = [SUB_MODE_UPLINK_BURST_1 := 0,
                    SUB_MODE_UPLINK_BURST_2 := 1,
                    SUB_MODE_UPLINK_BURST_3 := 2,
                    SUB_MODE_UPLINK_BURST_4 := 3]

SUB_MODES_DOWNLINK = [SUB_MODE_DOWNLINK_BURST_1 := 0,
                      SUB_MODE_DOWNLINK_BURST_2 := 1,
                      SUB_MODE_DOWNLINK_BURST_3 := 2,
                      SUB_MODE_DOWNLINK_BURST_4 := 3]



class BurstModeUplink(FieldGroup):

    PREAMBLE = 0x66666666
    SYNCWORD = 0x8153884C
    MIDAMBLE = 0xDF46428F20B9BD70DF46428F

    def __init__(self):
        with self.defineFields():
            self.preamble = Field(32, uint=BurstModeUplink.PREAMBLE)
            self.syncword = Field(32, uint=BurstModeUplink.SYNCWORD)
            self.coded_length = CodedLength()
            self.data_a = Field()
            self.midamble = Field(96, uint=BurstModeUplink.MIDAMBLE)
            self.coded_header = CodedHeader()
            self.data_b = Field()



class BurstModeDownlink(FieldGroup):

    PREAMBLE = 0x55555555
    SYNCWORD = 0xC1FA4C6A

    def __init__(self):
        with self.defineFields():
            self.preamble = Field(32, uint=BurstModeDownlink.PREAMBLE)
            self.syncword = Field(32, uint=BurstModeDownlink.SYNCWORD)
            self.coded_header = CodedHeader()
            self.data = Field()



class CodedLength(FieldGroup):

    def __init__(self):
        with self.defineFields():
            self.length_data_a = Field(9)
            self.crc_15 = Field(15)



class CodedHeader(FieldGroup):

    VERSION = 0

    def __init__(self):
        with self.defineFields():
            self.version = Field(2, uint=CodedHeader.VERSION)
            self.phy_payload_length = Field(8)
            self.timing_input_value = Field(7)
            self.burst_mode = Field(1)
            self.burst_type = Field(2)
            self.coded_header_crc = Field(8)
            self.fec_parity_ch1 = Field(28)
            self.fec_parity_ch2 = Field(28)
            self.fec_tail_ch1 = Field(6)
            self.fec_tail_ch2 = Field(6)
        
        self.crc_systematic = FieldGroup([
            self.version,
            self.phy_payload_length,
            self.timing_input_value,
            self.burst_mode,
            self.burst_type
        ])

        self.fec_systematic = FieldGroup([
            self.version,
            self.phy_payload_length,
            self.timing_input_value,
            self.burst_mode,
            self.burst_type,
            self.coded_header_crc
        ])



class CodedPayloadSingleBurstFec78(FieldGroup):

    def __init__(self):
        with self.defineFields():
            self.phy_payload = Field()
            self._7_8_padding = Field()
            self.fec_parity_3a = Field()
            self.fec_tail_0 = Field(6)
            self.padding = Field(2, uint=0)
        
        self.fec_systematic = FieldGroup([
            self.phy_payload,
            self._7_8_padding
        ])



class CodedPayloadSingleBurstFec12(FieldGroup):

    def __init__(self):
        with self.defineFields():
            self.phy_payload = Field()
            self.fec_parity_1 = Field()
            self.fec_tail_1 = Field(6)
            self.padding = Field(2, uint=0)



class CodedPayloadSingleBurstFec13(FieldGroup):

    def __init__(self):
        with self.defineFields():
            self.phy_payload = Field()
            self.fec_parity_1 = Field()
            self.fec_tail_1 = Field(6)
            self.padding = Field(2, uint=0)
            self.fec_parity_2 = Field()
            self.fec_tail_2 = Field(6)
            self.padding = Field(2, uint=0)



class CodedPayloadMultiBurst1(FieldGroup):

    def __init__(self):
        with self.defineFields():
            self.phy_payload = Field()
            self._7_8_padding = Field()
            self.fec_parity_3a = Field()
            self.fec_tail_0 = Field(6)
            self.padding = Field(2, uint=0)
        
        self.fec_systematic = FieldGroup([
            self.phy_payload,
            self._7_8_padding
        ])



class CodedPayloadMultiBurst2(FieldGroup):

    def __init__(self):
        with self.defineFields():
            self.fec_parity_1 = Field()
            self.fec_parity_3b = Field()
            self.fec_tail_1 = Field(6)
            self.padding = Field(2, uint=0)



class CodedPayloadMultiBurst3(FieldGroup):

    def __init__(self):
        with self.defineFields():
            self.fec_parity_2 = Field()
            self.fec_parity_3c = Field()
            self.fec_tail_2 = Field(6)
            self.padding = Field(2, uint=0)
