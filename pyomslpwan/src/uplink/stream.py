import numpy
import time

from pyomslpwan.src.channel import *
from pyomslpwan.src.uplink.frame import *
from pyomslpwan.src.uplink.pdu import *
from pyomslpwan.simulation.noise import *




class BurstModeUplinkTransmitter:

    def __init__(self, bitrate):
        self.bitrate = bitrate

        self.burst_queue: list[UplinkBurst] = []
        self.time = 0
        self.sample_buffer = numpy.zeros(0)

    def pushBurst(self, burst):
        self.burst_queue.append(burst) #TODO: implement out of order pushing, and deal with overlapping bursts

    def readSamples(self, n_samples):
        n_samples = min(n_samples, self.bitrate // 1)

        if n_samples > len(self.sample_buffer):
            self.sample_buffer = self.sample_buffer.copy()
            self.sample_buffer.resize(n_samples) # appends zeros

            start_time = self.time
            end_time = start_time + n_samples / self.bitrate
            self.time = end_time

            while len(self.burst_queue) > 0 and self.burst_queue[0].time < end_time:
                burst = self.burst_queue.pop(0)
                if burst.time < start_time:
                    continue

                bitstream = burst.bitstream

                delta_time = burst.time - start_time
                start_index = int(delta_time * self.bitrate)
                end_index = start_index + len(bitstream)
                if end_index > len(self.sample_buffer):
                    self.sample_buffer = self.sample_buffer.copy()
                    self.sample_buffer.resize(end_index) # appends zeros
                
                #print(start_time, end_time, delta_time, start_index, end_index, len(bitstream), len(self.sample_buffer))
                self.sample_buffer[start_index:end_index] = bitstream
        
        samples = self.sample_buffer[:n_samples]
        self.sample_buffer = self.sample_buffer[n_samples:]
        return samples



"""
class BurstModeUplinkReceiver:
    
    def __init__(self):
        pass

    def pullFrame(self):
        pass

    def writeSamples(self, samples):
        pass
"""


class BitstreamParser:

    def __init__(self):
        self.parser = BurstModeUplinkParser()
    
    def parseBitstream(self, nrz_stream, coded_header_index) -> UplinkBurst:
        burst = UplinkBurst()

        try:
            coded_header_size = burst.struct.coded_header.getSize()
            burst.struct.coded_header.setBitstream(nrz_stream[coded_header_index:coded_header_index + coded_header_size])
            
            self.parser.parseCodedHeader(burst)

            data_a_index = burst.struct.getPosition(burst.struct.data_a)
            data_a_size = burst.struct.data_a.getSize()
            burst.struct.data_a.setBitstream(nrz_stream[data_a_index:data_a_index + data_a_size])

            data_b_index = burst.struct.getPosition(burst.struct.data_b)
            data_b_size = burst.struct.data_b.getSize()
            burst.struct.data_b.setBitstream(nrz_stream[data_b_index:data_b_index + data_b_size])

            self.parser.parseData(burst)

            return burst
        
        except AssertionError:
            return None



class UplinkReceiver:

    def __init__(self, syncword_threshold, midamble_threshold):
        self.parser = BurstModeUplinkParser()
        self.syncword_synchronizer = UplinkSyncwordSynchronizer(syncword_threshold)
        self.midamble_synchronizer = UplinkMidambleSynchronizer(midamble_threshold)
        self.syncword_demodulator = UplinkPrecodedMskDemodulator()
        self.midamble_demodulator = UplinkPrecodedMskDemodulator()

        self.bursts: list[UplinkBurst] = []

        self.syncword_parser_loop = self.syncwordParserLoop()
        self.midamble_parser_loop = self.midambleParserLoop()
    
    def syncwordParserLoop(self):
        while True:
            try:
                burst = UplinkBurst()
                nrz = numpy.zeros(0)
                self.syncword_demodulator.clear()

                syncword_start = self.syncword_synchronizer.syncword_offset
                syncword_end = syncword_start + burst.struct.syncword.getSize()
                while self.syncword_synchronizer.getSize() < syncword_end:
                    yield None
                samples = self.syncword_synchronizer.getBuffer()[syncword_start:syncword_end]
                nrz = numpy.concatenate([nrz, self.syncword_demodulator.demodulate(samples)])

                coded_length_start = syncword_end
                coded_length_end = coded_length_start + burst.struct.coded_length.getSize()
                while self.syncword_synchronizer.getSize() < coded_length_end:
                    yield None
                samples = self.syncword_synchronizer.getBuffer()[coded_length_start:coded_length_end]
                nrz = numpy.concatenate([nrz, self.syncword_demodulator.demodulate(samples)])
                burst.struct.coded_length.setNrzStream(nrz[coded_length_start:coded_length_end])

                self.parser.parseCodedLength(burst)

                data_a_start = coded_length_end
                data_a_end = data_a_start + burst.struct.data_a.getSize()
                while self.syncword_synchronizer.getSize() < data_a_end:
                    yield None
                samples = self.syncword_synchronizer.getBuffer()[data_a_start:data_a_end]
                nrz = numpy.concatenate([nrz, self.syncword_demodulator.demodulate(samples)])
                burst.struct.data_a.setNrzStream(nrz[data_a_start:data_a_end])

                midamble_start = data_a_end
                midamble_end = midamble_start + burst.struct.midamble.getSize()
                while self.syncword_synchronizer.getSize() < midamble_end:
                    yield None
                samples = self.syncword_synchronizer.getBuffer()[midamble_start:midamble_end]
                nrz = numpy.concatenate([nrz, self.syncword_demodulator.demodulate(samples)])

                coded_header_start = midamble_end
                coded_header_end = coded_header_start + burst.struct.coded_header.getSize()
                while self.syncword_synchronizer.getSize() < coded_header_end:
                    yield None
                samples = self.syncword_synchronizer.getBuffer()[coded_header_start:coded_header_end]
                nrz = numpy.concatenate([nrz, self.syncword_demodulator.demodulate(samples)])
                burst.struct.coded_header.setNrzStream(nrz[coded_header_start:coded_header_end])

                self.parser.parseCodedHeader(burst)

                data_b_start = coded_header_end
                data_b_end = data_b_start + burst.struct.data_b.getSize()
                while self.syncword_synchronizer.getSize() < data_b_end:
                    yield None
                samples = self.syncword_synchronizer.getBuffer()[data_b_start:data_b_end]
                nrz = numpy.concatenate([nrz, self.syncword_demodulator.demodulate(samples)])
                burst.struct.data_b.setNrzStream(nrz[data_b_start:data_b_end])

                self.parser.parseData(burst)

                yield burst

            except AssertionError:
                pass

            self.syncword_synchronizer.nextMatch()
    
    def midambleParserLoop(self):
        while True:
            try:
                burst = UplinkBurst()
                nrz = numpy.zeros(self.midamble_synchronizer.syncword_offset)
                self.midamble_demodulator.clear()

                midamble_start = self.midamble_synchronizer.syncword_offset
                print(midamble_start)
                midamble_end = midamble_start + burst.struct.midamble.getSize()
                while self.midamble_synchronizer.getSize() < midamble_end:
                    yield None
                samples = self.midamble_synchronizer.getBuffer()[midamble_start:midamble_end]
                nrz = numpy.concatenate([nrz, self.midamble_demodulator.demodulate(samples)])
                print(nrz)

                coded_header_start = midamble_end
                coded_header_end = coded_header_start + burst.struct.coded_header.getSize()
                while self.midamble_synchronizer.getSize() < coded_header_end:
                    yield None
                samples = self.midamble_synchronizer.getBuffer()[coded_header_start:coded_header_end]
                nrz = numpy.concatenate([nrz, self.midamble_demodulator.demodulate(samples)])
                print(nrz[coded_header_start:coded_header_end])
                burst.struct.coded_header.setNrzStream(nrz[coded_header_start:coded_header_end])

                self.parser.parseCodedHeader(burst)

                beginning_size = burst.struct.syncword.getSize() + burst.struct.coded_length.getSize()
                beginning_start = self.midamble_synchronizer.syncword_offset - burst.struct.data_a.getSize() - beginning_size
                beginning_end = beginning_start + beginning_size
                nrz = numpy.zeros(beginning_start)
                self.midamble_demodulator.clear()

                samples = self.midamble_synchronizer.getBuffer()[beginning_start:beginning_end]
                nrz = numpy.concatenate([nrz, self.midamble_demodulator.demodulate(samples)])

                data_a_start = beginning_end
                data_a_end = data_a_start + burst.struct.data_a.getSize()
                samples = self.midamble_synchronizer.getBuffer()[data_a_start:data_a_end]
                nrz = numpy.concatenate([nrz, self.midamble_demodulator.demodulate(samples)])
                burst.struct.data_a.setNrzStream(nrz[data_a_start:data_a_end])

                middle_start = data_a_end
                middle_end = middle_start + burst.struct.midamble.getSize() + burst.struct.coded_header.getSize()
                samples = self.midamble_synchronizer.getBuffer()[middle_start:middle_end]
                nrz = numpy.concatenate([nrz, self.midamble_demodulator.demodulate(samples)])

                data_b_start = middle_end
                data_b_end = data_b_start + burst.struct.data_b.getSize()
                while self.midamble_synchronizer.getSize() < data_b_end:
                    yield None
                samples = self.midamble_synchronizer.getBuffer()[data_b_start:data_b_end]
                nrz = numpy.concatenate([nrz, self.midamble_demodulator.demodulate(samples)])
                burst.struct.data_b.setNrzStream(nrz[data_b_start:data_b_end])

                self.parser.parseData(burst)

                yield burst

            except AssertionError:
                    pass

            self.midamble_synchronizer.nextMatch()

    def feed(self, samples):
        self.syncword_synchronizer.feed(samples)
        self.midamble_synchronizer.feed(samples)

        while (burst := next(self.syncword_parser_loop)) is not None:
            self.bursts.append(burst)
        while (burst := next(self.midamble_parser_loop)) is not None:
            self.bursts.append(burst)
    
    def clear(self):
        self.syncword_parser_loop = self.syncwordParserLoop()
        self.midamble_parser_loop = self.midambleParserLoop()
        self.syncword_synchronizer.clear()
        self.midamble_synchronizer.clear()



frame = UplinkFrame()
frame.coded_payload.phy_payload = b"Hello world!"
frame.coded_header.timing_input_value = 64
frame.coded_header.burst_mode = BURST_MODE_SINGLE_BURST
frame.coded_header.burst_type = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3
BurstModeUplinkGenerator().generateFrame(frame)
bitstream = frame.uplink_0.bitstream
print(frame.uplink_0.struct.getPosition(frame.uplink_0.struct.midamble) + 100)

mod = UplinkMskModulator().modulate(bitstream)

noise = numpy.zeros(len(mod) + 200, dtype=complex)#complexNoise(noiseDeviation(0), len(mod) + 200)
chn = noise
chn[100:len(mod) + 100] += mod

rec = UplinkReceiver(1, 0.5)
rec.feed(chn)
for burst in rec.bursts:
    if burst.coded_header.burst_mode == BURST_MODE_SINGLE_BURST and frame.coded_header.burst_type == BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3:
        frame = UplinkFrame()
        frame.uplink_0 = burst
        BurstModeUplinkParser().parseFrame(frame)
        print(frame.coded_payload.phy_payload)

"""
par = BitstreamParser()
burst = par.parseBitstream(UplinkPrecodedMskDemodulator().demodulate(mod), frame.uplink_0.struct.getPosition(frame.uplink_0.struct.coded_header))
if burst != None:
    frame = UplinkFrame()
    frame.uplink_0 = burst
    BurstModeUplinkParser().parseFrame(frame)
    print(frame.coded_payload.phy_payload)
"""