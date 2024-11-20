import numpy
from matplotlib import pyplot



from pyomslpwan.simulation.plotting import *
from pyomslpwan.src.downlink.frame import *
from pyomslpwan.src.downlink.pdu import *
import pyomslpwan.src.structs as structs
from pyomslpwan.lib.channel import *
from pyomslpwan.lib.fields import *
from pyomslpwan.src.channel import *
from pyomslpwan.simulation.noise import *



class DownlinkHeaderPositiveFecTest:
    
    def __init__(self, eb_n0):
        self.crc_codec = CodedHeaderCrc()
        self.fec_codec = CommonFecEncodingScheme()

        self.dev = noiseDeviation(eb_n0)
    
    def sample(self):
        phy_payload_length = int(numpy.random.randint(5, 255 + 1))
        timing_input_value = int(numpy.random.randint(0, 127 + 1))
        burst_mode = int(numpy.random.choice(structs.BURST_MODES))
        match burst_mode:
            case structs.BURST_MODE_SINGLE_BURST:
                burst_type = int(numpy.random.choice(structs.BURST_TYPES_DOWNLINK_SINGLE_BURST))
            case structs.BURST_MODE_MULTI_BURST:
                burst_type = int(numpy.random.choice(structs.BURST_TYPES_DOWNLINK_MULTI_BURST))

        coded_header = generateCodedHeader(self.crc_codec, self.fec_codec, phy_payload_length, timing_input_value, burst_mode, burst_type)
        bitstream = coded_header.getBitstream()

        signal = binaryToNrz(bitstream)
        noise = realNoise(self.dev, len(signal))
        signal_rx = signal + noise
        
        coded_header_rx = structs.CodedHeader()
        coded_header_rx.setNrzStream(signal_rx)
        try:
            phy_payload_length_rx, timing_input_value_rx, burst_mode_rx, burst_type_rx = parseCodedHeader(self.crc_codec, self.fec_codec, coded_header_rx)
        except AssertionError:
            return False
        
        if phy_payload_length_rx != phy_payload_length:
            return False
        if timing_input_value_rx != timing_input_value:
            return False
        if burst_mode_rx != burst_mode:
            return False
        if burst_type_rx != burst_type:
            return False
        
        return True
    
    def test(self, n):
        return sum([int(self.sample()) for _ in range(n)]) / n



class DownlinkHeaderNegativeFecTest:
    
    def __init__(self, eb_n0):
        self.crc_codec = CodedHeaderCrc()
        self.fec_codec = CommonFecEncodingScheme()

        self.dev = noiseDeviation(eb_n0)
    
    def sample(self):
        coded_header_rx = structs.CodedHeader()

        noise = realNoise(self.dev, coded_header_rx.getSize())
        
        coded_header_rx.setNrzStream(noise)
        try:
            parseCodedHeader(self.crc_codec, self.fec_codec, coded_header_rx)
        except AssertionError:
            return False
        
        return True
    
    def test(self, n):
        return sum([int(self.sample()) for _ in range(n)]) / n



def plotPositiveFecHeader(eb_n0_arr, n):
    positive_rates = numpy.empty(len(eb_n0_arr))
    for x, eb_n0 in enumerate(eb_n0_arr):
        positive_rates[x] = DownlinkHeaderPositiveFecTest(eb_n0).test(n)
    
    fig, ax = pyplot.subplots(1, 1)
    plotSingle(ax, eb_n0_arr, 1-positive_rates, "Verjetnost napačno sprejete kodirane glave pri navzdolnjem prenosu", r"$E_b/N_0 [dB]$", r"Verjetnost", True)

    pyplot.show()



plotPositiveFecHeader(numpy.linspace(-10, 10, 21), 5000)
#print("{0:.2E}".format(DownlinkHeaderNegativeFecTest(0).test(50000)))