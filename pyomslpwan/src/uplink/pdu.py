from typing import Optional

import pyomslpwan.src.structs as structs
import pyomslpwan.src.coding as coding



class CodedLength:

    def __init__(self):
        self.struct = structs.CodedLength()
        
        self.length_data_a = None



class CodedHeader:
    
    def __init__(self):
        self.struct = structs.CodedHeader()

        self.version = None
        self.phy_payload_length = None
        self.timing_input_value = None
        self.burst_mode = None
        self.burst_type = None



class CodedPayload:

    def __init__(self):
        self.single_burst_fec_7_8_struct: Optional[structs.CodedPayloadSingleBurstFec78] = None
        self.single_burst_fec_1_2_struct: Optional[structs.CodedPayloadSingleBurstFec12] = None
        self.single_burst_fec_1_3_struct: Optional[structs.CodedPayloadSingleBurstFec13] = None
        self.multi_burst_1_struct: Optional[structs.CodedPayloadMultiBurst1] = None
        self.multi_burst_2_struct: Optional[structs.CodedPayloadMultiBurst2] = None
        self.multi_burst_3_struct: Optional[structs.CodedPayloadMultiBurst3] = None

        self.phy_payload = None

        self.bits_payload = None
        self.bits_padding_7_8 = None
        self.bits_fec = None
        self.bits_coded_payload = None
        self.fec_parities = coding.CommonFecEncodingSchemeParities()



class UplinkBurst:

    def __init__(self):
        self.time = None
        self.bitstream = None

        self.struct = structs.BurstModeUplink()
        self.coded_length = CodedLength()
        self.coded_header = CodedHeader()
        self.coded_payload = CodedPayload()
        self.data_bitstream = None

        self.length_data_a = None
        self.length_data_b = None
        self.length_data = None

        self.sub_mode = None
        self.time_burst = None
        self.time_jitter = None



class UplinkFrame:

    def __init__(self):
        self.uplink_0: Optional[UplinkBurst] = None
        self.uplink_1: Optional[UplinkBurst] = None
        self.uplink_2: Optional[UplinkBurst] = None
        self.uplink_3: Optional[UplinkBurst] = None

        self.coded_header = CodedHeader()
        self.coded_payload = CodedPayload()