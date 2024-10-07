import numpy
from matplotlib import pyplot



from pyomslpwan.simulation.plotting import *
from pyomslpwan.src.uplink.frame import *
from pyomslpwan.src.uplink.pdu import *
import pyomslpwan.src.structs as structs
from pyomslpwan.lib.channel import *
from pyomslpwan.lib.fields import *
from pyomslpwan.src.channel import *
from pyomslpwan.simulation.noise import *
from pyomslpwan.lib.coding import *



class UplinkPayloadFecTestSingle:
    
    def __init__(self, eb_n0, phy_payload_length, burst_type):
        self.fec_codec = CommonFecEncodingScheme()
        self.interleaver = CommonInterleavingScheme()
        self.precoder = Precoder()

        self.modulator = UplinkMskModulator()
        self.demodulator = UplinkPrecodedMskDemodulator()

        self.burst_type = burst_type
        self.phy_payload_length = phy_payload_length
        self.dev = noiseDeviation(eb_n0)
    
    def sample(self):
        self.modulator.clear()
        self.demodulator.clear()

        phy_payload = numpy.random.randint(0, 256, self.phy_payload_length,  dtype=numpy.uint8).tobytes()

        data = generateCodedPayloadSingleBurst(self.fec_codec, self.interleaver, phy_payload, self.burst_type)
        bitstream = self.precoder.encode(data)

        signal = self.modulator.modulate(bitstream)
        noise = complexNoise(self.dev, len(signal))
        signal_rx = signal + noise
        
        data_rx = self.demodulator.demodulate(signal_rx)
        phy_payload_rx = parseCodedPayloadSingleBurst(self.fec_codec, self.interleaver, data_rx, self.phy_payload_length, self.burst_type)

        payload_bits = numpy.unpackbits(numpy.frombuffer(phy_payload, dtype=numpy.uint8))
        payload_bits_rx = numpy.unpackbits(numpy.frombuffer(phy_payload_rx, dtype=numpy.uint8))
        n_errors = numpy.sum(payload_bits ^ payload_bits_rx)
        
        return n_errors / (self.phy_payload_length * 8)
    
    def test(self, n):
        return sum([self.sample() for _ in range(n)]) / n



class UplinkPayloadFecTestMulti:
    
    def __init__(self, eb_n0, phy_payload_length, received_count):
        self.fec_codec = CommonFecEncodingScheme()
        self.interleaver = CommonInterleavingScheme()
        self.precoder = Precoder()

        self.modulator = UplinkMskModulator()
        self.demodulator = UplinkPrecodedMskDemodulator()

        self.received_count = received_count
        self.phy_payload_length = phy_payload_length
        self.dev = noiseDeviation(eb_n0)
    
    def sample(self):
        phy_payload = numpy.random.randint(0, 256, self.phy_payload_length,  dtype=numpy.uint8).tobytes()

        datas = generateCodedPayloadMultiBurst(self.fec_codec, self.interleaver, phy_payload)
        datas_rx = [None] * 3

        received_indices = numpy.array(range(3))
        numpy.random.shuffle(received_indices)
        received_indices = received_indices[:self.received_count]

        for index in received_indices:
            self.modulator.clear()
            self.demodulator.clear()

            data = datas[index]

            bitstream = self.precoder.encode(data)

            signal = self.modulator.modulate(bitstream)
            noise = complexNoise(self.dev, len(signal))
            signal_rx = signal + noise
        
            data_rx = self.demodulator.demodulate(signal_rx)
            datas_rx[index] = data_rx

        phy_payload_rx = parseCodedPayloadMultiBurst(self.fec_codec, self.interleaver, datas_rx, self.phy_payload_length)

        payload_bits = numpy.unpackbits(numpy.frombuffer(phy_payload, dtype=numpy.uint8))
        payload_bits_rx = numpy.unpackbits(numpy.frombuffer(phy_payload_rx, dtype=numpy.uint8))
        n_errors = numpy.sum(payload_bits ^ payload_bits_rx)
        
        return n_errors / (self.phy_payload_length * 8)
    
    def test(self, n):
        return sum([self.sample() for _ in range(n)]) / n



class UplinkFecTestDirect:
    
    def __init__(self, eb_n0, size, generator_index):
        self.fec_codec = CommonFecEncodingScheme().codec
        self.interleaver = CommonInterleavingScheme()
        self.precoder = Precoder()

        self.modulator = UplinkMskModulator()
        self.demodulator = UplinkPrecodedMskDemodulator()

        self.size = size
        self.generator_index = generator_index
        self.dev = noiseDeviation(eb_n0)
    
    def sample(self):
        data = numpy.random.randint(0, 2, self.size, dtype=bool)
        fec_input = []

        if self.generator_index < 4:
            codeds = self.fec_codec.encode(data)

            for coded in codeds:
                self.modulator.clear()
                self.demodulator.clear()

                interleaved = self.interleaver.interleave(coded)

                bitstream = self.precoder.encode(interleaved)

                signal = self.modulator.modulate(bitstream)
                noise = complexNoise(self.dev, len(signal))
                signal_rx = signal + noise
            
                interleaved_rx = self.demodulator.demodulate(signal_rx)
                coded_rx = self.interleaver.deinterleave(interleaved_rx)
                fec_input.append(coded_rx)
            if self.generator_index == 0:
                fec_input[2] = numpy.zeros_like(fec_input[0])
                fec_input[3] = numpy.zeros_like(fec_input[0])
            elif self.generator_index == 1:
                fec_input[0] = numpy.zeros_like(fec_input[0])
                fec_input[3] = numpy.zeros_like(fec_input[0])
            elif self.generator_index == 2:
                fec_input[1] = numpy.zeros_like(fec_input[0])
                fec_input[2] = numpy.zeros_like(fec_input[0])
                fec_input[3] = numpy.zeros_like(fec_input[0])
            elif self.generator_index == 3:
                fec_input[0] = numpy.zeros_like(fec_input[0])
                fec_input[2] = numpy.zeros_like(fec_input[0])
                fec_input[3] = numpy.zeros_like(fec_input[0])
            data_rx = self.fec_codec.decode(fec_input, soft=True)
        
        else:
            self.modulator.clear()
            self.demodulator.clear()

            coded = data
            interleaved = self.interleaver.interleave(coded)
            bitstream = self.precoder.encode(interleaved)
            
            signal = self.modulator.modulate(bitstream)
            noise = realNoise(self.dev, len(signal))
            signal_rx = signal + noise

            interleaved_rx = self.demodulator.demodulate(signal_rx)
            coded_rx = self.interleaver.deinterleave(interleaved_rx)
            data_rx = nrzToBinary(coded_rx)

        n_errors = numpy.sum(data ^ data_rx)
        
        return n_errors / len(data)
    
    def test(self, n):
        return sum([self.sample() for _ in range(n)]) / n



def plotFecPayloadSingle(eb_n0_arr, n):
    bers_arr_long = numpy.empty([len(structs.BURST_TYPES_UPLINK_SINGLE_BURST), len(eb_n0_arr)])
    bers_arr_short = numpy.empty([len(structs.BURST_TYPES_UPLINK_SINGLE_BURST), len(eb_n0_arr)])
    for z, burst_type in enumerate(structs.BURST_TYPES_UPLINK_SINGLE_BURST):
        bers_long = bers_arr_long[z]
        bers_short = bers_arr_short[z]
        for x, eb_n0 in enumerate(eb_n0_arr):
            bers_long[x] = UplinkPayloadFecTestSingle(eb_n0, 255, burst_type).test(n)
            bers_short[x] = UplinkPayloadFecTestSingle(eb_n0, 5, burst_type).test(n)
    
    fig, axes = pyplot.subplots(1, 2)
    plotMultiple(axes[0], eb_n0_arr, bers_arr_long, "Pogostost napake v načinu enkratne oddaje\nnavzgornje povezave (255 zlogov vsebine)", r"$E_b/N_0 [dB]$", r"BER", True)
    plotMultiple(axes[1], eb_n0_arr, bers_arr_short, "Pogostost napake v načinu enkratne oddaje\nnavzgornje povezave (5 zlogov vsebine)", r"$E_b/N_0 [dB]$", r"BER", True)
    axes[0].legend(["7/8", "1/2", "1/3"], title="stopnja FEC")
    axes[1].legend(["7/8", "1/2", "1/3"], title="stopnja FEC")

    pyplot.show()



def plotFecPayloadMulti(eb_n0_arr, n):
    bers_arr_long = numpy.empty([3, len(eb_n0_arr)])
    bers_arr_short = numpy.empty([3, len(eb_n0_arr)])
    for z, received_count in enumerate(range(1, 3 + 1)):
        bers_long = bers_arr_long[z]
        bers_short = bers_arr_short[z]
        for x, eb_n0 in enumerate(eb_n0_arr):
            bers_long[x] = UplinkPayloadFecTestMulti(eb_n0, 255, received_count).test(n)
            bers_short[x] = UplinkPayloadFecTestMulti(eb_n0, 5, received_count).test(n)
    
    fig, axes = pyplot.subplots(1, 2)
    plotMultiple(axes[0], eb_n0_arr, bers_arr_long, "Pogostost napake v načinu večkratne oddaje\nnavzgornje povezave (255 zlogov vsebine)", r"$E_b/N_0 [dB]$", r"BER", True)
    plotMultiple(axes[1], eb_n0_arr, bers_arr_short, "Pogostost napake v načinu večkratne oddaje\nnavzgornje povezave (5 zlogov vsebine)", r"$E_b/N_0 [dB]$", r"BER", True)
    axes[0].legend(["1", "2", "3"], title="Število prejetih\npodokvirjev")
    axes[1].legend(["1", "2", "3"], title="Število prejetih\npodokvirjev")

    pyplot.show()



def plotFecDirect(eb_n0_arr, n):
    bers_arr_long = numpy.empty([5, len(eb_n0_arr)])
    bers_arr_short = numpy.empty([5, len(eb_n0_arr)])
    for z, generator_index in enumerate(range(5)):
        bers_long = bers_arr_long[z]
        bers_short = bers_arr_short[z]
        for x, eb_n0 in enumerate(eb_n0_arr):
            bers_long[x] = UplinkFecTestDirect(eb_n0, 255 * 8, generator_index).test(n)
            bers_short[x] = UplinkFecTestDirect(eb_n0, 5 * 8, generator_index).test(n)
    
    fig, axes = pyplot.subplots(1, 2)
    plotMultiple(axes[0], eb_n0_arr, bers_arr_long, "Uplink FEC BER (255 byte payload)", r"$E_b/N_0 [dB]$", r"BER", True)
    plotMultiple(axes[1], eb_n0_arr, bers_arr_short, "Uplink FEC BER (5 byte payload)", r"$E_b/N_0 [dB]$", r"BER", True)
    fig.legend(["g0 & g1", "g1 & g2", "g0", "g1", "plain"], title="Configuration")

    pyplot.show()



#plotFecPayloadSingle(numpy.linspace(-20, 0, 21), 5000)
plotFecPayloadMulti(numpy.linspace(-20, 0, 21), 5000)
#plotFecDirect(numpy.linspace(-10, 10, 21), 200)