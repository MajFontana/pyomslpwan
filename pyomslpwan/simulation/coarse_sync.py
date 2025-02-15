import numpy
from matplotlib import pyplot
from scipy import signal

import matplotlib
matplotlib.use("tkagg")

from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator
from pyomslpwan.src.uplink.pdu import UplinkFrame
from pyomslpwan.lib.channel import GmskModulator
from pyomslpwan.src.structs import BURST_MODE_SINGLE_BURST, BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3



PAYLOAD_SIZE = 255
BURST_MODE = BURST_MODE_SINGLE_BURST
BURST_TYPE = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3

BT = 0.5
SPS = 8
L = 3
BAUD = 10e3
SAMP_RATE = BAUD * SPS

PADDING = SPS * 10



def generateFrame(timing_input_value, payload, burst_mode, burst_type):
    uplink_generator = BurstModeUplinkGenerator()
    frame = UplinkFrame()
    frame.coded_header.timing_input_value = timing_input_value
    frame.coded_header.burst_mode = burst_mode
    frame.coded_header.burst_type = burst_type
    frame.coded_payload.phy_payload = payload
    uplink_generator.generateFrame(frame)
    return frame



class SampleProcessor:

    def process(self, samples):
        output = numpy.array(list(map(self.iteration, samples)))
        return output



# https://john-gentile.com/kb/dsp/PI_filter.html
class PIFilter:

    def __init__(self, bandwidth, nco_gain, detector_gain, symbol_period, sample_rate, damping=0.707):
        angular_bandwidth = bandwidth * 2 * numpy.pi
        alpha = 1 - 2 * damping ** 2
        natural_frequency = angular_bandwidth / numpy.sqrt(alpha + numpy.sqrt(alpha ** 2 + 1))
        tau_1 = nco_gain * detector_gain / natural_frequency ** 2
        tau_2 = 2 * damping / natural_frequency
        self.k_p = symbol_period * tau_2 / tau_1
        self.k_i = 1 / tau_1
        self.integral = 0
    
    def iteration(self, value):
        self.integral += self.k_i * value
        derivative = self.k_p * value
        filtered = self.integral + derivative
        return filtered



class Nco:

    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.phase = 0
    
    def iteration(self, frequency):
        sample = numpy.exp(1j * self.phase)
        delta_phi = frequency * 2 * numpy.pi / self.sample_rate
        self.phase = (self.phase + delta_phi) % (2 * numpy.pi)
        return sample



# https://wirelesspi.com/band-edge-filters-for-carrier-and-timing-synchronization/
class BandEdgeFll(SampleProcessor):

    def __init__(self, matched_filter, sps):
        matched_filter_dft = numpy.fft.fftshift(numpy.fft.fft(matched_filter)) / len(matched_filter)
        frequency_matched_filter_dft = numpy.gradient(matched_filter_dft, SAMP_RATE / (len(matched_filter) - 1))
        self.matched_filter = matched_filter
        self.frequency_matched_filter = numpy.fft.ifft(numpy.fft.ifftshift(frequency_matched_filter_dft * len(matched_filter)))
        self.window = [0 for _ in range(len(matched_filter))]
        # suggested to be between baud/20 and baud/200
        # https://john-gentile.com/kb/dsp/PI_filter.html
        bandwidth = 1 / 100
        nco_gain = 2 * numpy.pi / sps
        detector_gain = numpy.pi / 2
        self.loop_filter = PIFilter(bandwidth, nco_gain, detector_gain, 1, sps)
        self.nco = Nco(sps)
        self.nco_output = 1
    
    def iteration(self, sample):
        corrected = sample * self.nco_output

        self.window.pop(0)
        self.window.append(corrected)

        matched_output = numpy.dot(self.window, self.matched_filter)
        frequency_matched_output = numpy.dot(self.window, self.matched_filter)

        error = (matched_output * numpy.conj(frequency_matched_output)).imag

        filter_output = self.loop_filter.iteration(error)

        self.nco_output = self.nco.iteration(filter_output)

        return matched_output



numpy.random.seed(0)

angdev = numpy.pi / 2
dev = angdev / (2 * numpy.pi)

timing_input_value = numpy.random.randint(0, 128)
payload = numpy.random.randint(0, 256, PAYLOAD_SIZE,  dtype=numpy.uint8).tobytes()

frame = generateFrame(timing_input_value, payload, BURST_MODE, BURST_TYPE)
burst = frame.uplink_0
bitstream = burst.bitstream

modulated = GmskModulator(BT, L, SPS).modulate(bitstream, True)

channel = numpy.zeros(len(modulated) + 2 * PADDING, dtype=complex)
channel[PADDING:len(modulated) + PADDING] = modulated
t = numpy.linspace(0, (len(channel) - 1) / SAMP_RATE, len(channel))

offset = 20e3
phasor = numpy.exp(1j * 2 * numpy.pi * offset * numpy.pi * t)
channel *= phasor

iq_pulse = GmskModulator(BT, L, SPS).modulate(numpy.ones(1), True)
matched_filter = numpy.gradient(numpy.unwrap(numpy.angle(iq_pulse)), 1)

fll = BandEdgeFll(matched_filter, SPS)
corrected = fll.process(channel)

pyplot.plot(numpy.diff(numpy.unwrap(numpy.angle(corrected))))
pyplot.show()

"""
matched_filter_dft = numpy.fft.fftshift(numpy.fft.fft(matched_filter)) / len(matched_filter)
frequency_matched_filter_dft = numpy.gradient(matched_filter_dft, SAMP_RATE / (len(matched_filter) - 1))

pyplot.plot(frequency_matched_filter_dft.real)
pyplot.plot(frequency_matched_filter_dft.imag)
pyplot.show()

spd1 = numpy.abs(matched_filter_dft) ** 2
spd2 = numpy.abs(frequency_matched_filter_dft) ** 2
fftfreq = numpy.fft.fftshift(numpy.fft.fftfreq(len(spd1), 1 / SAMP_RATE))
pyplot.plot(fftfreq, spd1)
pyplot.plot(fftfreq, spd2)
pyplot.yscale("log")
pyplot.grid(True)
pyplot.show()

frequency_matched_filter = numpy.fft.ifft(numpy.fft.ifftshift(frequency_matched_filter_dft * len(matched_filter)))
pyplot.plot(frequency_matched_filter.real)
pyplot.plot(frequency_matched_filter.imag)
pyplot.show()

a = numpy.convolve(channel, matched_filter)
b = numpy.convolve(channel, frequency_matched_filter)
error = (a * numpy.conj(b)).imag
#pyplot.plot(a)
#pyplot.plot(b)
pyplot.plot(error[8000:-8000])
pyplot.show()

pad = numpy.zeros(SPS * 1000)
padded = numpy.concatenate([pad, matched_filter, pad])
fft = numpy.fft.fftshift(numpy.fft.fft(padded)) / len(padded)
spd = numpy.abs(fft) ** 2
fftfreq = numpy.fft.fftshift(numpy.fft.fftfreq(len(fft), 1 / SAMP_RATE))
pyplot.plot(fftfreq, spd)
pyplot.yscale("log")
pyplot.grid(True)
pyplot.show()

pad = numpy.zeros(SPS * 1000)
padded = numpy.concatenate([pad, frequency_matched_filter, pad])
fft = numpy.fft.fftshift(numpy.fft.fft(padded)) / len(padded)
spd = numpy.abs(fft) ** 2
fftfreq = numpy.fft.fftshift(numpy.fft.fftfreq(len(fft), 1 / SAMP_RATE))
pyplot.plot(fftfreq, spd)
pyplot.yscale("log")
pyplot.grid(True)
pyplot.show()
"""

"""
window = channel[PADDING:PADDING + 32 * SPS]
window_shape = signal.windows.hann(32 * SPS)
window *= window_shape

fft = numpy.fft.fftshift(numpy.fft.fft(window)) / len(window)
spd = numpy.abs(fft) ** 2
fftfreq = numpy.fft.fftshift(numpy.fft.fftfreq(len(fft), 1 / SAMP_RATE))
pyplot.plot(fftfreq, numpy.abs(fft))
pyplot.yscale("log")
pyplot.grid(True)
pyplot.show()
"""