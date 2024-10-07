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



class DownlinkPositiveDetectionTest:

    def __init__(self, threshold, eb_n0):
        self.correlator = DownlinkSyncwordCorrelator()

        self.threshold = threshold
        self.dev = noiseDeviation(eb_n0)
    
    def sample(self):
        self.correlator.buffer = realNoise(self.dev, len(self.correlator.buffer))

        burst = structs.BurstModeDownlink()
        bitstream = burst.syncword.getBitstream()

        signal = binaryToNrz(bitstream)
        noise = realNoise(self.dev, len(signal))
        signal_rx = signal + noise

        correlation = numpy.abs(self.correlator.correlate(signal_rx))
        if not correlation[-1] >= self.threshold:
            return False
        
        return True
    
    def test(self, n):
        return sum([int(self.sample()) for _ in range(n)]) / n



class DownlinkNegativeDetectionTest:

    def __init__(self, threshold, eb_n0):
        self.correlator = DownlinkSyncwordCorrelator()

        self.threshold = threshold
        self.dev = noiseDeviation(eb_n0)
    
    def test(self, n):
        self.correlator.buffer = realNoise(self.dev, len(self.correlator.buffer))

        noise = realNoise(self.dev, n)

        correlation = numpy.abs(self.correlator.correlate(noise))
        matches = numpy.argwhere(correlation >= self.threshold)[:, 0]
        detections = len(matches)
        
        return detections / n



def plotDetection(eb_n0_arr, threshold_arr_pos, threshold_arr_neg, n):
    positive_rates_arr = numpy.empty([len(threshold_arr_pos), len(eb_n0_arr)])
    for z, threshold in enumerate(threshold_arr_pos):
        positive_rates = positive_rates_arr[z]
        for x, eb_n0 in enumerate(eb_n0_arr):
            positive_rates[x] = DownlinkPositiveDetectionTest(threshold, eb_n0).test(n)
    
    negative_rate_arr = numpy.empty(len(threshold_arr_neg))
    for z, threshold in enumerate(threshold_arr_neg):
        negative_rate_arr[z] = DownlinkNegativeDetectionTest(threshold, 0).test(n)
    
    fig, axes = pyplot.subplots(1, 2)
    plotMultiple(axes[0], eb_n0_arr, 1-positive_rates_arr, "Verjetnost zgrešitve sinhronizacijske besede\npri navzdolnji povezavi", r"$E_b/N_0 [dB]$", r"Verjetnost", True)
    plotSingle(axes[1], [f"{th:.2f}" for th in threshold_arr_neg], negative_rate_arr, "Frekvenca lažne zaznave sinhronizacijske besede\npri navzdolnji povezavi", r"Pragovna vrednost", r"Normirana frekvenca", True)
    axes[0].legend([f"{th:.2f}" for th in threshold_arr_pos], title="Pragovna vrednost")

    pyplot.show()



plotDetection(numpy.linspace(-10, 10, 21), numpy.linspace(0.4, 0.6, 3), numpy.linspace(0.4, 0.6, 5), 5000)