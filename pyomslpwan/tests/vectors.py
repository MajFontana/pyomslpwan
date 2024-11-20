from bitstring import Bits



class FecTestVector:
    def __init__(self):
        self.input_data = Bits(bin="11000000110111101111111011101101000")
        self.systematic_output = Bits(bin="11000000110111101111111011101101000")
        self.fec_parity_1 = Bits(bin="10001110100000011001111001111101100")
        self.fec_parity_2 = Bits(bin="10110110110101010100101010101100011")
        self.fec_parity_3 = Bits(bin="11110101110011100001000111111001110")
        self.fec_parity_3a = Bits(bin="11101")
        self.fec_parity_3b = Bits(bin="11000")
        self.fec_parity_3c = Bits(bin="11010")
        self.fec_tail_0 = Bits(bin="111000")
        self.fec_tail_1 = Bits(bin="101000")
        self.fec_tail_2 = Bits(bin="001000")
        self.fec_tail_3 = Bits(bin="111000")



class Interleaver40BitTestVector:
    def __init__(self):
        self.coded_payload = Bits(bin="0101011000110000110100000011110010010110")
        self.data = Bits(bin="0011010100000100000101101010011010011101")



class Interleaver80BitTestVector:
    def __init__(self):
        self.coded_payload = Bits(bin="10110011110000010001001001110001001101000001101001001101000011001110011101010010")
        self.data = Bits(bin="10100100011101110100111101000000000000000011110010000001110101110111110100100010")



class Precoding1TestVector:
    def __init__(self):
        self.preamble = Bits(hex="66666666")
        self.sync = Bits(hex="8153884C")
        self.cl = Bits(hex="03DE4B")
        self.data_a = Bits(hex="56361021413150")
        self.midamble = Bits(hex="DF46428F20B9BD70DF46428F")
        self.coded_header = Bits(hex="0354178025B5AD02A9A5A179")
        self.data_b = Bits(hex="88E038484CA8")
        self.precoded_uplink_radio_burst = Bits(hex="55555555C1FA4C6A02316EFD2D1831E1A9F8B0E563C8B0E563C8B0E563C882FE1C40376F7B83FD7771C54C90246C6AFC")



class Precoding2TestVector:
    def __init__(self):
        self.preamble = Bits(hex="66666666")
        self.sync = Bits(hex="8153884C")
        self.cl = Bits(hex="03DE4B")
        self.data_a = Bits(hex="75803310367459")
        self.midamble = Bits(hex="DF46428F20B9BD70DF46428F")
        self.coded_header = Bits(hex="0354178025B5AD02A9A5A179")
        self.data_b = Bits(hex="E4CDE59E56AB")
        self.precoded_uplink_radio_burst = Bits(hex="55555555C1FA4C6A02316ECF402A982D4E7530E563C8B0E563C8B0E563C882FE1C40376F7B83FD7771C516AB17517DFE")



class FullUplinkSingleBurstRate78TestVector:
    def __init__(self):
        self.version = Bits(bin="00")
        self.phy_payload_length = Bits(bin="00001111")
        self.timing_input_value = Bits(bin="1011001")
        self.burst_mode = Bits(bin="0")
        self.burst_type = Bits(bin="00")
        self.phy_payload = Bits(hex="401A02A73D785634121503ACB46271")
        self.coded_payload = Bits(hex="401A02A73D785634121503ACB4627101826E0C")
        self.data = Bits(hex="22500904966F2114F90204FC23AC1E76106312")
        self.data_a = Bits(hex="22500904966F2114F902")
        self.data_b = Bits(hex="04FC23AC1E76106312")
        self.preamble = Bits(hex="66666666")
        self.sync = Bits(hex="8153884C")
        self.cl = Bits(hex="0528E4")
        self.midamble = Bits(hex="DF46428F20B9BD70DF46428F")
        self.coded_header = Bits(hex="03EC85902836700252E0A914")
        self.radio_burst = Bits(hex="666666668153884C0528E422500904966F2114F902DF46428F20B9BD70DF46428F03EC85902836700252E0A91404FC23AC1E76106312")
        self.radio_burst_after_precoding = Bits(hex="55555555C1FA4C6A07BC9633780D86DD58B19E8583B0E563C8B0E563C8B0E563C8821AC7583C2D48037B90FD9E0682327A114D18529B")



class FullUplinkSingleBurstRate12TestVector:
    def __init__(self):
        self.version = Bits(bin="00")
        self.phy_payload_length = Bits(bin="00001111")
        self.timing_input_value = Bits(bin="0101011")
        self.burst_mode = Bits(bin="0")
        self.burst_type = Bits(bin="01")
        self.phy_payload = Bits(hex="401A02A73D785634121503ACB46271")
        self.coded_payload = Bits(hex="401A02A73D785634121503ACB462717A1B9F29CB709268422DEADF70E955DC")
        self.data = Bits(hex="383F074B5D2D8C282B661C10659A80DD0DFA53552FA65247C48EA065B32267")
        self.data_a = Bits(hex="383F074B5D2D8C282B661C10659A80DD")
        self.data_b = Bits(hex="0DFA53552FA65247C48EA065B32267")
        self.preamble = Bits(hex="66666666")
        self.sync = Bits(hex="8153884C")
        self.cl = Bits(hex="0803AD")
        self.midamble = Bits(hex="DF46428F20B9BD70DF46428F")
        self.coded_header = Bits(hex="03D599802AE5EC027361D741")
        self.radio_burst = Bits(hex="666666668153884C0803AD383F074B5D2D8C282B661C10659A80DDDF46428F20B9BD70DF46428F03D599802AE5EC027361D7410DFA53552FA65247C48EA065B32267")
        self.radio_burst_after_precoding = Bits(hex="55555555C1FA4C6A0C027BA42084EEF3BB4A3C3ED512185757C0B330E563C8B0E563C8B0E563C8823F55403F971A034AD13CE18B077AFFB8757B6426C9F0576AB354")



class FullUplinkSingleBurstRate13TestVector:
    def __init__(self):
        self.version = Bits(bin="00")
        self.phy_payload_length = Bits(bin="00001111")
        self.timing_input_value = Bits(bin="0011010")
        self.burst_mode = Bits(bin="0")
        self.burst_type = Bits(bin="10")
        self.phy_payload = Bits(hex="401A02A73D785634121503ACB46271")
        self.coded_payload = Bits(hex="401A02A73D785634121503ACB462717A1B9F29CB709268422DEADF70E955DC6DC5EF66400CB4A93AFDB57E2DBD794C")
        self.data = Bits(hex="08B2A605823E0F137D0948100C1B22C1F397DF456B6D861492FA9F0534FBFB5F2C2DF60E4758BE6152B24F5D7EC94B")
        self.data_a = Bits(hex="08B2A605823E0F137D0948100C1B22C1F397DF456B6D8614")
        self.data_b = Bits(hex="92FA9F0534FBFB5F2C2DF60E4758BE6152B24F5D7EC94B")
        self.preamble = Bits(hex="66666666")
        self.sync = Bits(hex="8153884C")
        self.cl = Bits(hex="0C6170")
        self.midamble = Bits(hex="DF46428F20B9BD70DF46428F")
        self.coded_header = Bits(hex="03CD23502BF4600265578569")
        self.radio_burst = Bits(hex="666666668153884C0C617008B2A605823E0F137D0948100C1B22C1F397DF456B6D8614DF46428F20B9BD70DF46428F03CD23502BF460026557856992FA9F0534FBFB5F2C2DF60E4758BE6152B24F5D7EC94B")
        self.radio_burst_after_precoding = Bits(hex="55555555C1FA4C6A0A51C80CEBF5074321089AC38DEC180A16B3A10A5C30E7DEDB451EB0E563C8B0E563C8B0E563C8822BB2F83E0E500357FC47DD5B87D087AE8606F0BA3B0D0964F4E151FBEB68F3C1ADEE")



class FullUplinkMultiBurstTestVector:
    def __init__(self):
        self.version = Bits(bin="00")
        self.phy_payload_length = Bits(bin="00001111")
        self.timing_input_value = Bits(bin="0100101")
        self.burst_mode = Bits(bin="1")
        self.burst_type = Bits(bin="01")
        self.phy_payload = Bits(hex="401A02A73D785634121503ACB46271")
        self.coded_payload_ul1 = Bits(hex="401A02A73D785634121503ACB4627101826E0C")
        self.coded_payload_ul2 = Bits(hex="7A1B9F29CB709268422DEADF70E9552E2F32E4")
        self.coded_payload_ul3 = Bits(hex="6DC5EF66400CB4A93AFDB57E2DBD7990097F54")
        self.data_ul1 = Bits(hex="22500904966F2114F90204FC23AC1E76106312")
        self.data_ul2 = Bits(hex="03715E9B88076A4C69198C677B2AF679A6A7AF")
        self.data_ul3 = Bits(hex="1E34C4CD5BBBC31A4ED91F1A6615D77BCA7B94")
        self.data_a_ul1 = Bits(hex="22500904966F2114F902")
        self.data_a_ul2 = Bits(hex="03715E9B88076A4C6919")
        self.data_a_ul3 = Bits(hex="1E34C4CD5BBBC31A4ED9")
        self.data_b_ul1 = Bits(hex="04FC23AC1E76106312")
        self.data_b_ul2 = Bits(hex="8C677B2AF679A6A7AF")
        self.data_b_ul3 = Bits(hex="1F1A6615D77BCA7B94")
        self.preamble = Bits(hex="66666666")
        self.sync = Bits(hex="8153884C")
        self.cl = Bits(hex="0528E4")
        self.midamble = Bits(hex="DF46428F20B9BD70DF46428F")
        self.coded_header = Bits(hex="03D2DD302ABBB402770EE4C7")
        self.radio_burst_ul1 = Bits(hex="666666668153884C0528E422500904966F2114F902DF46428F20B9BD70DF46428F03D2DD302ABBB402770EE4C704FC23AC1E76106312")
        self.radio_burst_ul2 = Bits(hex="666666668153884C0528E403715E9B88076A4C6919DF46428F20B9BD70DF46428F03D2DD302ABBB402770EE4C78C677B2AF679A6A7AF")
        self.radio_burst_ul3 = Bits(hex="666666668153884C0528E41E34C4CD5BBBC31A4ED9DF46428F20B9BD70DF46428F03D2DD302ABBB402770EE4C71F1A6615D77BCA7B94")
        self.radio_burst_after_precoding_ul1 = Bits(hex="55555555C1FA4C6A07BC9633780D86DD58B19E8583B0E563C8B0E563C8B0E563C8823BB3A83FE66E034C8996A48682327A114D18529B")
        self.radio_burst_after_precoding_ul2 = Bits(hex="55555555C1FA4C6A07BC9602C9F1D64C04DF6A5D9530E563C8B0E563C8B0E563C8823BB3A83FE66E034C8996A44A54C6BF8D4575F478")
        self.radio_burst_after_precoding_ul3 = Bits(hex="55555555C1FA4C6A07BC96112EA6ABF666229769B530E563C8B0E563C8B0E563C8823BB3A83FE66E034C8996A49097551F3CC62F465E")



class FullDownlinkSingleBurstRate78TestVector:
    def __init__(self):
        self.version = Bits(bin="00")
        self.phy_payload_length = Bits(bin="00001111")
        self.timing_input_value = Bits(bin="1111111")
        self.burst_mode = Bits(bin="0")
        self.burst_type = Bits(bin="00")
        self.phy_payload = Bits(hex="4C0104A73D785634121503650C99BA")
        self.coded_payload = Bits(hex="4C0104A73D785634121503650C99BA003440FC")
        self.data = Bits(hex="02541B861E254158D4379468E1241C17184A12")
        self.preamble = Bits(hex="55555555")
        self.sync = Bits(hex="C1FA4C6A")
        self.coded_header = Bits(hex="03FF8DC029FD22024B40BA92")
        self.radio_burst = Bits(hex="55555555C1FA4C6A03FF8DC029FD22024B40BA9202541B861E254158D4379468E1241C17184A12")



class FullDownlinkSingleBurstRate12TestVector:
    def __init__(self):
        self.version = Bits(bin="00")
        self.phy_payload_length = Bits(bin="00001111")
        self.timing_input_value = Bits(bin="0111110")
        self.burst_mode = Bits(bin="0")
        self.burst_type = Bits(bin="01")
        self.phy_payload = Bits(hex="4C0104A73D785634121503650C99BA")
        self.coded_payload = Bits(hex="4C0104A73D785634121503650C99BA72E9C976AC7DDAD68C377B22872E3E58")
        self.data = Bits(hex="5976296214070CF8F7341AA054230D712DB87A1E4F26C81B869AC5F4179F7A")
        self.preamble = Bits(hex="55555555")
        self.sync = Bits(hex="C1FA4C6A")
        self.coded_header = Bits(hex="03DF1C902A23DF027D698B3C")
        self.radio_burst = Bits(hex="55555555C1FA4C6A03DF1C902A23DF027D698B3C5976296214070CF8F7341AA054230D712DB87A1E4F26C81B869AC5F4179F7A")



class FullDownlinkSingleBurstRate13TestVector:
    def __init__(self):
        self.version = Bits(bin="00")
        self.phy_payload_length = Bits(bin="00001111")
        self.timing_input_value = Bits(bin="0001001")
        self.burst_mode = Bits(bin="0")
        self.burst_type = Bits(bin="10")
        self.phy_payload = Bits(hex="4C0104A73D785634121503650C99BA")
        self.coded_payload = Bits(hex="4C0104A73D785634121503650C99BA72E9C976AC7DDAD68C377B22872E3E5866B6F044BB34DEECCC8D614F47D277F8")
        self.data = Bits(hex="3DC4BE4DB03F427815026D325532944330AE6F8152CF8D18B6697C7F3A839F5DBD0161D3AF8192123FB69E587057AF")
        self.preamble = Bits(hex="55555555")
        self.sync = Bits(hex="C1FA4C6A")
        self.coded_header = Bits(hex="03C4AF402B113F02698A1BEB")
        self.radio_burst = Bits(hex="55555555C1FA4C6A03C4AF402B113F02698A1BEB3DC4BE4DB03F427815026D325532944330AE6F8152CF8D18B6697C7F3A839F5DBD0161D3AF8192123FB69E587057AF")



class FullDownlinkMultiBurstTestVector:
    def __init__(self):
        self.version = Bits(bin="00")
        self.phy_payload_length = Bits(bin="00001111")
        self.timing_input_value = Bits(bin="1101101")
        self.burst_mode = Bits(bin="1")
        self.burst_type = Bits(bin="00")
        self.phy_payload = Bits(hex="4C0104A73D785634121503650C99BA")
        self.coded_payload_dl1 = Bits(hex="4C0104A73D785634121503650C99BA003440FC")
        self.coded_payload_dl2 = Bits(hex="72E9C976AC7DDAD68C377B22872E3E6A93FB34")
        self.coded_payload_dl3 = Bits(hex="66B6F044BB34DEECCC8D614F47D277C12D4844")
        self.data_dl1 = Bits(hex="02541B861E254158D4379468E1241C17184A12")
        self.data_dl2 = Bits(hex="2BBA6B3C572D9F0974A664AB47BB4792FAF4BE")
        self.data_dl3 = Bits(hex="397F999213CDB35549AB3E03002174DDF4D393")
        self.preamble = Bits(hex="55555555")
        self.sync = Bits(hex="C1FA4C6A")
        self.coded_header = Bits(hex="03F6C3902910A60247285386")
        self.radio_burst_dl1 = Bits(hex="55555555C1FA4C6A03F6C3902910A6024728538602541B861E254158D4379468E1241C17184A12")
        self.radio_burst_dl2 = Bits(hex="55555555C1FA4C6A03F6C3902910A602472853862BBA6B3C572D9F0974A664AB47BB4792FAF4BE")
        self.radio_burst_dl3 = Bits(hex="55555555C1FA4C6A03F6C3902910A60247285386397F999213CDB35549AB3E03002174DDF4D393")
