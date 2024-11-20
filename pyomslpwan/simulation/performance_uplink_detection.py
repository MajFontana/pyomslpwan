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



class UplinkPositiveDetectionTestSyncword:

    def __init__(self, threshold, eb_n0):
        self.crc_codec = CodedLengthCrc()
        self.precoder = Precoder()

        self.modulator = UplinkMskModulator()
        self.demodulator = UplinkPrecodedMskDemodulator()
        self.correlator = UplinkSyncwordCorrelator()

        self.threshold = threshold
        self.dev = noiseDeviation(eb_n0)
    
    def sample(self):
        self.modulator.clear()
        self.demodulator.clear()
        self.correlator.buffer = complexNoise(self.dev, len(self.correlator.buffer))

        length_data_a = int(numpy.random.randint(4, 384 + 1))

        burst = structs.BurstModeUplink()
        burst.coded_length.copyFrom(generateCodedLength(self.crc_codec, length_data_a))
        bitstream = self.precoder.encode(FieldGroup([burst.syncword, burst.coded_length]).getBitstream())

        signal = self.modulator.modulate(bitstream)
        noise = complexNoise(self.dev, len(signal))
        signal_rx = signal + noise

        sync_signal_rx = signal_rx[:burst.syncword.getSize()]
        correlation = numpy.abs(self.correlator.correlate(sync_signal_rx))
        if not correlation[-1] >= self.threshold:
            return False
        
        cl_signal_rx = signal_rx[burst.syncword.getSize():]
        coded_length_rx = structs.CodedLength()
        coded_length_rx.setNrzStream(self.demodulator.demodulate(cl_signal_rx))
        try:
            length_data_a_rx = parseCodedLength(self.crc_codec, coded_length_rx)
        except AssertionError:
            return False
        
        if length_data_a_rx != length_data_a:
            return False
        
        return True
    
    def test(self, n):
        return sum([int(self.sample()) for _ in range(n)]) / n



class UplinkNegativeDetectionTestSyncword:

    def __init__(self, threshold, eb_n0):
        self.crc_codec = CodedLengthCrc()

        self.demodulator = UplinkPrecodedMskDemodulator()
        self.correlator = UplinkSyncwordCorrelator()

        self.threshold = threshold
        self.dev = noiseDeviation(eb_n0)
    
    def test(self, n):
        self.correlator.buffer = complexNoise(self.dev, len(self.correlator.buffer))

        detections = 0

        coded_length = structs.CodedLength()

        noise = complexNoise(self.dev, n + coded_length.getSize())

        correlation = numpy.abs(self.correlator.correlate(noise[:n]))
        matches = numpy.argwhere(correlation >= self.threshold)[:, 0]
        for index in matches:
            self.demodulator.clear()

            cl_signal_rx = noise[index:index + coded_length.getSize()]
            coded_length_rx = structs.CodedLength()
            coded_length_rx.setNrzStream(self.demodulator.demodulate(cl_signal_rx))
            try:
                parseCodedLength(self.crc_codec, coded_length_rx)
            except AssertionError:
                continue
            
            detections += 1
        
        return detections / n



class UplinkPositiveDetectionTestMidamble:

    def __init__(self, threshold, eb_n0):
        self.precoder = Precoder()

        self.modulator = UplinkMskModulator()
        self.correlator = UplinkMidambleCorrelator()

        self.threshold = threshold
        self.dev = noiseDeviation(eb_n0)
    
    def sample(self):
        self.correlator.buffer = complexNoise(self.dev, len(self.correlator.buffer))
        self.modulator.clear()

        midamble = structs.BurstModeUplink().midamble
        bitstream = self.precoder.encode(midamble.getBitstream())

        signal = self.modulator.modulate(bitstream)
        noise = complexNoise(self.dev, len(signal))
        signal_rx = signal + noise

        correlation = numpy.abs(self.correlator.correlate(signal_rx))
        if not correlation[-1] >= self.threshold:
            return False
        
        return True
    
    def test(self, n):
        return sum([int(self.sample()) for _ in range(n)]) / n



class UplinkNegativeDetectionTestMidamble:

    def __init__(self, threshold, eb_n0):
        self.correlator = UplinkMidambleCorrelator()

        self.threshold = threshold
        self.dev = noiseDeviation(eb_n0)
    
    def test(self, n):
        self.correlator.buffer = complexNoise(self.dev, len(self.correlator.buffer))

        noise = complexNoise(self.dev, n)

        correlation = numpy.abs(self.correlator.correlate(noise))
        matches = numpy.argwhere(correlation >= self.threshold)[:, 0]
        detections = len(matches)

        return detections / n



def plotDetectionSyncword(eb_n0_arr, threshold_arr_pos, threshold_arr_neg, n):
    positive_rates_arr = numpy.empty([len(threshold_arr_pos), len(eb_n0_arr)])
    for z, threshold in enumerate(threshold_arr_pos):
        positive_rates = positive_rates_arr[z]
        for x, eb_n0 in enumerate(eb_n0_arr):
            positive_rates[x] = UplinkPositiveDetectionTestSyncword(threshold, eb_n0).test(n)
    
    negative_rate_arr = numpy.empty(len(threshold_arr_neg))
    for z, threshold in enumerate(threshold_arr_neg):
        negative_rate_arr[z] = UplinkNegativeDetectionTestSyncword(threshold, 0).test(n)
    
    fig, axes = pyplot.subplots(1, 2)
    plotMultiple(axes[0], eb_n0_arr, 1-positive_rates_arr, "Verjetnost zgrešitve podokvirja navzgornje povezave\npri zaznavi s sinhronizacijsko besedo in kodirano dolžino", r"$E_b/N_0 [dB]$", r"Verjetnost", True)
    plotSingle(axes[1], [f"{th:.2f}" for th in threshold_arr_neg], negative_rate_arr, "Frekvenca lažne zaznave podokvirja\npri zaznavi s sinhronizacijsko besedo in kodirano dolžino", r"Pragovna vrednost", r"Normirana frekvenca", True)
    axes[0].legend([f"{th:.2f}" for th in threshold_arr_pos], title="Pragovna vrednost")

    pyplot.show()



def plotDetectionMidamble(eb_n0_arr, threshold_arr_pos, threshold_arr_neg, n):
    positive_rates_arr = numpy.empty([len(threshold_arr_pos), len(eb_n0_arr)])
    for z, threshold in enumerate(threshold_arr_pos):
        positive_rates = positive_rates_arr[z]
        for x, eb_n0 in enumerate(eb_n0_arr):
            positive_rates[x] = UplinkPositiveDetectionTestMidamble(threshold, eb_n0).test(n)
    
    negative_rate_arr = numpy.empty(len(threshold_arr_neg))
    for z, threshold in enumerate(threshold_arr_neg):
        negative_rate_arr[z] = UplinkNegativeDetectionTestMidamble(threshold, 0).test(n)
    
    fig, axes = pyplot.subplots(1, 2)
    plotMultiple(axes[0], eb_n0_arr, 1-positive_rates_arr, "Verjetnost zgrešitve sredinske sinhronizacijske besede\npri navzgornji povezavi", r"$E_b/N_0 [dB]$", r"Verjetnost", True)
    plotSingle(axes[1], [f"{th:.2f}" for th in threshold_arr_neg], negative_rate_arr, "Frekvenca lažne zaznave sredinske sinhronizacijske besede\npri navzgornji povezavi", r"Pragovna vrednost", r"Normirana frekvenca", True)
    axes[0].legend([f"{th:.2f}" for th in threshold_arr_pos], title="Pragovna vrednost")

    pyplot.show()



#plotDetectionSyncword(numpy.linspace(-20, 0, 21), numpy.linspace(0.3, 0.5, 3), numpy.linspace(0.3, 0.5, 5), 5000)
#plotDetectionMidamble(numpy.linspace(-20, 0, 21), numpy.linspace(0.2, 0.3, 3), numpy.linspace(0.2, 0.3, 5), 5000)