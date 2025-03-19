import numpy
from matplotlib import pyplot, animation
from scipy import signal

import matplotlib
matplotlib.use("tkagg")

from pyomslpwan.lib.coding import binaryToNrz
from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator
from pyomslpwan.src.uplink.pdu import UplinkFrame
from pyomslpwan.lib.channel import GmskModulator, IqFrequencyModulator, constructLaurentPulsesGmsk
from pyomslpwan.src.structs import BURST_MODE_SINGLE_BURST, BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3
from pyomslpwan.simulation.noise import noiseDeviation, complexNoise



PAYLOAD_SIZE = 255
BURST_MODE = BURST_MODE_SINGLE_BURST
BURST_TYPE = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3

BT = 0.5
SPS = 16
L = 3
BAUD = 10e3
SAMP_RATE = BAUD * SPS

PADDING = SPS * 2000

MAX_OFFSET = 20e3
MAX_DRIFT = 200



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



# https://www.researchgate.net/publication/290776860_Preprocessing_AIS_Signals_for_Demodulation_in_Co-Channel_Interference
class MskFftFed(SampleProcessor):

    def __init__(self, baud, fft_size, fft_interval, top_size, sample_rate):
        self.fft_size = fft_size
        self.fft_interval = fft_interval
        self.window = [0 for _ in range(fft_size + 1)]

        symbol_interval = 1 / baud
        bin_size = sample_rate / fft_size
        self.peak_spacing = round(1 / (symbol_interval * bin_size))
        self.sample_rate = sample_rate
        
        self.top_size = top_size

        self.index = 0
        self.error = 0

    def iteration(self, sample):
        self.window.pop(0)
        self.window.append(sample)
        self.index += 1

        if (self.index % self.fft_interval) == 0:
            squared = numpy.array(self.window) ** 2
            fft = numpy.fft.fftshift(numpy.fft.fft(squared[:-1]))
            fft_delayed = numpy.fft.fftshift(numpy.fft.fft(squared[1:]))
            cross_power = fft_delayed * fft.conj()
            cross_power_magnitude = numpy.abs(cross_power)

            top_cpm_indices = numpy.argsort(cross_power_magnitude)[::-1][:self.top_size]
            top_cpm_index_pairs = numpy.stack(numpy.meshgrid(top_cpm_indices, top_cpm_indices), axis=-1).reshape(self.top_size ** 2, 2)
            #if self.index >= PADDING and self.index % SPS == 0:
            #    pyplot.plot(cross_power_magnitude)
            #    pyplot.show()
            bin_spacings = numpy.abs(top_cpm_index_pairs[:, 1] - top_cpm_index_pairs[:, 0])
            matching_cpm_index_pairs = top_cpm_index_pairs[bin_spacings == self.peak_spacing, :]

            if len(matching_cpm_index_pairs) > 0:
                matching_pair_indices = numpy.arange(matching_cpm_index_pairs.shape[0])
                cpm_peak_pairs = cross_power_magnitude[matching_cpm_index_pairs]
                cpm_pair_average = numpy.average(cpm_peak_pairs, axis=-1)
                max_peak_indices = top_cpm_index_pairs[numpy.argmax(cpm_pair_average)]
                max_peak_cp = cross_power[max_peak_indices]

                self.error = (numpy.angle(max_peak_cp[0]) + numpy.angle(max_peak_cp[1])) / (8 * numpy.pi / self.sample_rate)

        return self.error # detector gain = 1



# https://www.researchgate.net/publication/290776860_Preprocessing_AIS_Signals_for_Demodulation_in_Co-Channel_Interference
class MskFftSearch():

    def __init__(self, baud, fft_size, fft_interval, top_size, sample_rate):
        self.fft_size = fft_size
        self.fft_interval = fft_interval
        self.window = []

        symbol_interval = 1 / baud
        bin_size = sample_rate / fft_size
        self.peak_spacing = round(1 / (symbol_interval * bin_size))
        self.sample_rate = sample_rate
        
        self.top_size = top_size

        self.index = 0

    def iteration(self, sample):
        self.window.append(sample)
        self.index += 1
        if len(self.window) > self.fft_size:
            self.window.pop(0)
        else:
            return None

        if (self.index % self.fft_interval) != 0:
            return None
        
        squared = numpy.array(self.window) ** 2
        fft = numpy.fft.fftshift(numpy.fft.fft(squared[:-1]))
        fft_delayed = numpy.fft.fftshift(numpy.fft.fft(squared[1:]))
        cross_power = fft_delayed * fft.conj()
        cross_power_magnitude = numpy.abs(cross_power)
        self.cpm = cross_power_magnitude

        top_cpm_indices = numpy.argsort(cross_power_magnitude)[::-1][:self.top_size]
        top_cpm_index_pairs = numpy.stack(numpy.meshgrid(top_cpm_indices, top_cpm_indices), axis=-1).reshape(self.top_size ** 2, 2)
        bin_spacings = numpy.abs(top_cpm_index_pairs[:, 1] - top_cpm_index_pairs[:, 0])
        matching_cpm_index_pairs = top_cpm_index_pairs[bin_spacings == self.peak_spacing, :]

        if len(matching_cpm_index_pairs) == 0:
            return None

        cpm_peak_pairs = cross_power_magnitude[matching_cpm_index_pairs]
        cpm_pair_average = numpy.average(cpm_peak_pairs, axis=-1)
        max_peak_indices = matching_cpm_index_pairs[numpy.argmax(cpm_pair_average), :]
        max_peak_cp = cross_power[max_peak_indices]

        offset = (numpy.angle(max_peak_cp[0]) + numpy.angle(max_peak_cp[1])) / (8 * numpy.pi / self.sample_rate)

        return offset



class Nco(SampleProcessor):

    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.phase = 0
    
    def iteration(self, frequency): # NCO gain = 1
        sample = numpy.exp(1j * self.phase)
        delta_phi = frequency * 2 * numpy.pi / self.sample_rate
        self.phase = (self.phase + delta_phi) % (2 * numpy.pi)
        return sample



# https://john-gentile.com/kb/dsp/PI_filter.html
# https://dsp.stackexchange.com/questions/75492/how-to-set-parameters-of-the-pi-controller-inside-the-pll
class PiFilter(SampleProcessor):

    def __init__(self, tau_1, tau_2, sample_rate):
        sample_period = 1 / sample_rate
        self.k_p = sample_period * tau_2 / tau_1
        self.k_i = 1 / tau_1

        self.integral = 0
    
    def iteration(self, value):
        self.integral += self.k_i * value
        derivative = self.k_p * value
        filtered = self.integral + derivative
        return filtered
    
    @staticmethod
    def constructForLoopFilter(sample_rate, bandwidth, nco_gain=1, detector_gain=1, damping=0.707): # Bandwidth suggested to be between baud/20 and baud/200
        bandwidth_radians = bandwidth * 2 * numpy.pi
        alpha = 1 - 2 * damping ** 2
        natural_frequency = bandwidth_radians / numpy.sqrt(alpha + numpy.sqrt(alpha ** 2 + 1))
        tau_1 = nco_gain * detector_gain / natural_frequency ** 2
        tau_2 = 2 * damping / natural_frequency
        return PiFilter(tau_1, tau_2, sample_rate)



class Fll(SampleProcessor):

    def __init__(self, fed, loop_filter, nco):
        self.fed = fed
        self.loop_filter = loop_filter
        self.nco = nco
        
        self.frequency = 0
    
    def iteration(self, sample):
        reference = self.nco.iteration(self.frequency)
        corrected = sample * reference.conj()
        error = self.fed.iteration(corrected)
        self.frequency = self.loop_filter.iteration(error)
        #print(error, self.frequency)
        return corrected



class Delay(SampleProcessor):

    def __init__(self, delay_length):
        self.memory = [0 for _ in range(delay_length)]
    
    def iteration(self, sample):
        delayed = self.memory.pop(0)
        self.memory.append(sample)
        return delayed


import numpy as np

class PLL:
    """
    (Generated by DeepSeek)
    A Phase-Locked Loop (PLL) class to synchronize a VCO with an input complex sinusoid.
    
    Parameters:
    - damping_factor (float): Damping factor (ζ), typically 0.707 for critical damping.
    - loop_bandwidth (float): Loop bandwidth (Bn) in Hz, affecting lock speed and noise rejection.
    - sample_interval (float): Time step (dt) between samples in seconds.
    - initial_freq (float): Initial frequency estimate in Hz.
    - initial_phase (float): Initial phase estimate in radians.
    - ratio (float): Frequency multiplier/divider ratio (output_freq = input_freq * ratio).
    """
    
    def __init__(self, damping_factor=0.707, loop_bandwidth=10.0, sample_interval=1.0,
                 initial_freq=0.0, initial_phase=0.0, ratio=1.0):
        self.zeta = damping_factor
        self.Bn = loop_bandwidth
        self.dt = sample_interval
        self.freq = initial_freq
        self.phase = initial_phase
        self.ratio = ratio

        # Compute natural frequency in Hz (corrected formula)
        denom = self.zeta + 1/(4*self.zeta)
        self.wn_hz = (2 * np.pi * self.Bn) / denom  # Natural frequency in Hz

        # Loop filter coefficients (derived from wn_hz)
        self.Kp = (2 * self.zeta * self.wn_hz) * self.dt
        self.Ki = (self.wn_hz ** 2) * self.dt

        # Integral term for the loop filter
        self.integral = 0.0

    def update(self, sample):
        """
        Update the PLL with a new input sample and return the synchronized VCO output.
        
        Parameters:
        - sample (complex): Input complex sinusoid sample.
        
        Returns:
        - complex: VCO output synchronized to the input tone.
        """
        # Generate VCO output (with phase adjusted for frequency ratio)
        vco_output = numpy.exp(1j * self.phase)

        # Compute phase error (accounting for frequency ratio)
        target_phase = self.phase / self.ratio  # Phase comparator adjustment
        error = numpy.angle(sample * numpy.conj(numpy.exp(1j * target_phase)))

        # Update loop filter integral
        self.integral += self.Ki * error

        # Compute control signal (frequency adjustment)
        control_signal = self.Kp * error + self.integral

        # Update frequency and phase
        self.freq = control_signal * self.ratio  # Scale frequency by ratio
        self.phase += 2 * numpy.pi * self.freq * self.dt
        self.phase %= 2 * numpy.pi  # Wrap phase

        return vco_output, error

    def process_samples(self, samples):
        """
        Process an array of samples and return synchronized VCO outputs.
        
        Parameters:
        - samples (array_like): Input complex sinusoid samples.
        
        Returns:
        - ndarray: Array of VCO outputs synchronized to the input tone.
        """
        outputs = numpy.zeros_like(samples, dtype=complex)
        errors = numpy.zeros_like(samples, dtype=float)
        for i, sample in enumerate(samples):
            outputs[i], errors[i] = self.update(sample)
        return outputs, errors



#numpy.random.seed(0)

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

offset_omega = MAX_DRIFT / MAX_OFFSET # gives max slope of MAX_DRIFT/s
offset_phi = numpy.random.random() * 2 * numpy.pi
offset = MAX_OFFSET * numpy.cos(offset_omega * t + offset_phi)
complex_sine = IqFrequencyModulator(2 * numpy.pi / SAMP_RATE).modulate(offset)
channel *= complex_sine

ebn0 = 80
noisedev = noiseDeviation(ebn0)
noise = complexNoise(noisedev, len(channel))
channel += noise

true_offset = offset

fftsize = 128
searcher = MskFftSearch(BAUD, SPS * fftsize, SPS * fftsize, 2, SAMP_RATE)
delayer = Delay(SPS * fftsize * 2)
i = 0
while True:
    sample = channel[0]
    channel = channel[1:]
    offset = searcher.iteration(sample)
    delayer.iteration(sample)
    if offset is not None:
        print(f"True offset: {round(true_offset[i - SPS * fftsize])} Hz")
        break
    i += 1
print(f"Signal found at {round(offset)} Hz")

channel = delayer.process(channel)
t = numpy.linspace(0, (len(channel) - 1) / SAMP_RATE, len(channel))
channel *= numpy.exp(-1j * 2 * numpy.pi * offset * t)

#pyplot.plot(searcher.cpm)
#pyplot.show()

#pyplot.plot(numpy.array(searcher.window).real)
#pyplot.plot(numpy.array(searcher.window).imag)
#pyplot.show()

"""
fed = MskFftFed(BAUD, SPS * 16, 1, 0.1, SAMP_RATE)
loop_filter = PiFilter.constructForLoopFilter(SAMP_RATE, BAUD / 100 * 1e-5)
nco = Nco(SAMP_RATE)
fll = Fll(fed, loop_filter, nco)

coarse = fll.process(channel)

pyplot.plot(numpy.gradient(numpy.unwrap(numpy.angle(coarse)), 1 / SAMP_RATE) / (2 * numpy.pi))
pyplot.show()
"""

"""
from pyomslpwan.lib.channel import GMSKSynchronizer

sync = GMSKSynchronizer(SPS, 0.001, 0 * 1)
ferr, perr, _, _, _, synced = sync.synchronize(channel)

#pyplot.plot(numpy.repeat(numpy.gradient(numpy.unwrap(numpy.angle(synced))) > 0, SPS))
pyplot.plot(numpy.gradient(numpy.unwrap(ferr)))
#pyplot.plot(numpy.unwrap(numpy.angle(modulated)))
pyplot.show()
"""

from pyomslpwan.lib.channel import design_complex_bpf, design_lpf

lowpass = design_lpf(14e3, 1e3, SAMP_RATE)
channel = signal.lfilter(lowpass, 1, channel)

#sig = channel[PADDING + 32 * SPS:PADDING + 32 * SPS + 100 * SPS:SPS]
#pyplot.scatter(sig.real, sig.imag)
#pyplot.show()

"""
trans_pulse = GmskModulator(BT, L, SPS).modulate(numpy.array([0,0,1,1]), True)[2*SPS + SPS//2 - 1:4*SPS - SPS//2]
const_pulse = GmskModulator(BT, L, SPS).modulate(numpy.array([0,0,0,0]), True)[2*SPS + SPS//2 - 1:4*SPS - SPS//2]
cor1 = numpy.correlate(channel, trans_pulse)
cor2 = numpy.correlate(channel, numpy.conj(trans_pulse))
cor3 = numpy.correlate(channel, const_pulse)
cor4 = numpy.correlate(channel, numpy.conj(const_pulse))
cor1mag = numpy.absolute(cor1)
cor2mag = numpy.absolute(cor2)
cor3mag = numpy.absolute(cor3)
cor4mag = numpy.absolute(cor4)
corA = numpy.maximum(cor1mag, cor2mag)
corB = numpy.maximum(cor3mag, cor4mag)
cor = corA - corB
lowpass = design_lpf(1.1, 0.1, SPS)
cor = signal.lfilter(lowpass, 1, cor).real
cor = numpy.maximum(cor, 0)
pyplot.plot(numpy.gradient(cor))
pyplot.show()
"""

"""
class TransitionPED:

    def __init__(self, BT, L, SPS):
        window_size = SPS
        side_size = int(numpy.ceil((L - 1) / 2)) + int(numpy.ceil(window_size / 2))
        self.window = [0 for _ in range(window_size)]

        zeros = numpy.zeros(side_size)
        ones = numpy.ones(side_size)
        transition = numpy.concatenate([zeros, ones])
        no_transition = numpy.concatenate([zeros, zeros])

        transition_pulse = GmskModulator(BT, L, SPS).modulate(transition, True)
        no_transition_pulse = GmskModulator(BT, L, SPS).modulate(no_transition, True)

        center = len(transition_pulse) // 2 + 1
        self.transition_pulse = transition_pulse[center - window_size // 2:center + window_size // 2]
        self.no_transition_pulse = no_transition_pulse[center - window_size // 2:center + window_size // 2]

        self.transition_lowpass = design_lpf(1.1, 0.1, SPS)
        self.transition_lowpass_state = numpy.zeros(len(self.transition_lowpass) - 1)
    
        self.last_estimate = 0

    def iteration(self, sample):
        window.pop(0)
        window.append(sample)

        transition_correlation_1 = numpy.abs(self.transition_pulse * window)
        transition_correlation_2 = numpy.abs(self.transition_pulse.conj() * window)
        transition_correlation = numpy.maximum(transition_correlation_1, transition_correlation_2)

        no_transition_correlation_1 = numpy.abs(self.no_transition_pulse * window)
        no_transition_correlation_2 = numpy.abs(self.no_transition_pulse.conj() * window)
        no_transition_correlation = numpy.maximum(no_transition_correlation_1, no_transition_correlation_2)

        correlation_difference = transition_correlation - no_transition_correlation
        filtered_correlation, self.transition_lowpass_state = signal.lfilter(
            self.transition_lowpass,
            1,
            correlation_difference,
            zi=self.transition_lowpass_state)
        transition_estimate = numpy.maximum(0, filtered_correlation)

        gradient = transition_estimate - self.last_estimate
        self.last_estimate = transition_estimate
        return gradient

class TransitionPLL(SampleProcessor):

    def __init__(self, sample_rate, bandwidth, BT, L, SPS):
        detector_gain = 1
        self.nco = Nco(sample_rate)
        self.loop_filter = PiFilter.constructForLoopFilter(sample_rate, bandwidth, detector_gain=detector_gain)
        self.ped = TransitionPED(BT, L, SPS)
        self.frequence = 0
        self.prev_cycle = 1

    def iteration(self, sample):
        phasor = self.nco.iteration(self.frequence)
        corrected = sample * phasor.conj()
        cycle = phasor ** 3
        if self.prev_cycle.imag < 0 and cycle.imag >= 0:
            self.prev_cycle = cycle
            error = self.ped.iteration(corrected)
        else:
            error = 0
        self.frequency = self.loop_filter.iteration(error)
        return corrected

p = TransitionPLL(SAMP_RATE, 0.01, BT, L, SPS)
sync = p.process(channel)[PADDING + SPS * 32:PADDING + SPS * 32 + 32 * SPS]

pyplot.scatter(sync.real, sync.imag)
pyplot.show()
"""

# https://hal.science/hal-01514643/document
class GmskPhaseRecovery2:

    def __init__(self, BT, L, SPS, bandwidth):
        self.C0 = constructLaurentPulsesGmsk(BT, L, SPS)[0]
        self.window = [0 for _ in range(16)]
        self.phase = 0

    def process(self, samples):
        filtered = signal.lfilter(self.C0[::-1], 1, samples) / SPS
        #filtered *= numpy.exp(1j * numpy.pi / 4)
        sampled = filtered[::SPS]
        sampled_prev = sampled[:-1]
        sampled = sampled[1:]
        output_corrected = []
        output_error = []
        
        coef = 1
        for orig, sample, sample_prev in zip(samples[1::SPS], sampled, sampled_prev):
            reference = numpy.exp(1j * self.phase)
            corrected = sample * reference.conj()
            corrected_prev = sample_prev * reference.conj()
            error = coef * (corrected.real * corrected.imag - corrected_prev.real * corrected_prev.imag)
            coef *= -1

            self.window.pop(0)
            self.window.append(error)
            smooth = numpy.average(self.window)

            self.phase += smooth * 0.001

            output_corrected.append(orig)# * reference.conj())#smooth)
            output_error.append(self.phase % (2 * numpy.pi))
        
        return numpy.array(output_corrected), numpy.array(output_error)

# https://hal.science/hal-01514643/document
class GmskPhaseRecovery:

    def __init__(self, BT, L, SPS, bandwidth):
        det_gain = 2 * numpy.pi * SAMP_RATE
        self.C0 = constructLaurentPulsesGmsk(BT, L, SPS)[0]
        self.nco = Nco(SAMP_RATE)
        self.loop_filter = PiFilter.constructForLoopFilter(SAMP_RATE, bandwidth, detector_gain=det_gain)
        self.frequency = 0

    def process(self, samples):
        filtered = signal.lfilter(self.C0[::-1], 1, samples) / SPS
        filtered *= numpy.exp(1j * numpy.pi / 4)
        sampled = filtered[::SPS]
        sampled_prev = sampled[:-1:]
        sampled = sampled[1::]
        output_corrected = []
        output_error = []
        
        coef = 1
        for sample, sample_prev in zip(sampled, sampled_prev):
            reference = self.nco.iteration(self.frequency)
            corrected = sample * reference.conj()
            corrected_prev = sample_prev * reference.conj()
            error = coef * (corrected.real * corrected.imag - corrected_prev.real * corrected_prev.imag)
            coef *= -1
            self.frequency = self.loop_filter.iteration(error)
            output_corrected.append(error)
            output_error.append(self.frequency)
        #output_error /= numpy.max(numpy.abs(output_error))
        
        return numpy.array(output_corrected), numpy.array(output_error)



# https://descanso.jpl.nasa.gov/monograph/series3/complete1.pdf
class GmskSync:

    def __init__(self):
        #int_wins_i = [for shift in range(K_b)]
        int_wins_q = []
        K_b = 6
        for shift in range(K_b):
            pass
            



squared = channel ** 2
a = 0.1
bandpass_1 = design_complex_bpf(-2 * dev * (1 + a), -2 * dev * (1 - a), 2 * dev* a, SPS)
bandpass_2 = design_complex_bpf(2 * dev * (1 - a), 2 * dev * (1 + a), 2 * dev * a, SPS)
peak_1 = signal.lfilter(bandpass_1, 1, squared)
peak_2 = signal.lfilter(bandpass_2, 1, squared)

nco1, err1 = PLL(damping_factor=0.707, loop_bandwidth=1.2, sample_interval=1 / SPS, initial_freq=2 * angdev, ratio=0.25).process_samples(peak_1)
nco2, err2 = PLL(damping_factor=0.707, loop_bandwidth=1.2, sample_interval=1 / SPS, initial_freq=-2 * angdev, ratio=0.25).process_samples(peak_2)

diff = nco2 * nco1
channel *= diff.conj()

pyplot.plot(numpy.gradient(numpy.unwrap(numpy.angle(diff))))
pyplot.plot(numpy.gradient(numpy.unwrap(numpy.angle(channel))))
pyplot.show()



rec = GmskPhaseRecovery2(BT, L, SPS, 100)
out, err = rec.process(channel)

pyplot.plot(numpy.repeat(numpy.gradient(numpy.unwrap(numpy.angle(out))), SPS))
pyplot.show()

#out = out[100 * SPS:6000 * SPS]
#pyplot.scatter(out.real, out.imag)
#pyplot.show()

ax1 = pyplot.gca()
ax2 = ax1.twinx()
ax1.plot(out.real)
ax1.plot(out.imag)
ax2.plot(err, color="green")
pyplot.show()




"""
squared = channel ** 2
a = 0.1
bandpass_1 = design_complex_bpf(-2 * dev * (1 + a), -2 * dev * (1 - a), 2 * dev* a, SPS)
bandpass_2 = design_complex_bpf(2 * dev * (1 - a), 2 * dev * (1 + a), 2 * dev * a, SPS)
peak_1 = signal.lfilter(bandpass_1, 1, squared)
peak_2 = signal.lfilter(bandpass_2, 1, squared)

fft = numpy.fft.fftshift(numpy.fft.fft(channel))
fftfreq = numpy.fft.fftshift(numpy.fft.fftfreq(len(fft), 1 / SAMP_RATE))
#pyplot.plot(fftfreq, numpy.abs(fft))
#pyplot.show()

fft_1 = numpy.fft.fftshift(numpy.fft.fft(peak_1))
fft_2 =  numpy.fft.fftshift(numpy.fft.fft(peak_2))
fftfreq = numpy.fft.fftshift(numpy.fft.fftfreq(len(fft_1), 1 / SAMP_RATE))
#pyplot.plot(fftfreq, numpy.abs(fft_1))
#pyplot.plot(fftfreq, numpy.abs(fft_2) / numpy.max(numpy.abs(fft_2)))

fft = numpy.fft.fftshift(numpy.fft.fft(bandpass_2))
fftfreq = numpy.fft.fftshift(numpy.fft.fftfreq(len(fft), 1 / SAMP_RATE))
#pyplot.plot(fftfreq, numpy.abs(fft) / numpy.max(numpy.abs(fft)))
#pyplot.show()

nco1, err1 = PLL(damping_factor=0.707, loop_bandwidth=1.2, sample_interval=1 / SPS, initial_freq=2 * angdev, ratio=0.25).process_samples(peak_1)
nco2, err2 = PLL(damping_factor=0.707, loop_bandwidth=1.2, sample_interval=1 / SPS, initial_freq=-2 * angdev, ratio=0.25).process_samples(peak_2)

e = numpy.average(numpy.lib.stride_tricks.sliding_window_view(numpy.abs(err2), 40), axis=-1)
i = numpy.argmax(e < 0.05)
#pyplot.plot(e)
#pyplot.show()

fft = numpy.fft.fftshift(numpy.fft.fft(nco2[PADDING + 32 * SPS:-PADDING]))
fftfreq = numpy.fft.fftshift(numpy.fft.fftfreq(len(fft), 1 / SAMP_RATE))
#pyplot.plot(fftfreq, numpy.abs(fft) / numpy.max(numpy.abs(fft)))
#pyplot.show()

diff = nco2 * nco1
#pyplot.plot(numpy.gradient(numpy.unwrap(numpy.angle(diff)), 1 / SAMP_RATE) / (2 * numpy.pi))
#pyplot.show()
corrected = channel * diff.conj()

k = numpy.argmax(corrected > 0.01)
corrected = corrected[k::4]
diff = diff[k::4]

fig, ax = pyplot.subplots()
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.set_aspect("equal")
arrow = pyplot.arrow(0, 0, 0, 0)
#trace = pyplot.scatter([], [], linestyle="-", marker="o")
def update(frame):
    sample = diff[frame]
    arrow.set_data(dx=sample.real, dy=sample.imag)
    hist = diff[max(frame-SPS*64, 0):frame + 1]
    #trace.set_offsets(numpy.stack([hist.real, hist.imag], axis=-1))
    return (arrow,)
ani = animation.FuncAnimation(fig=fig, func=update, frames=len(corrected), interval=1000/(16*SPS))
pyplot.show()

#nco1 *= diff
#nco2 *= diff.conj()
#phase = nco1 * nco2
#corrected *= phase.conj()

#pyplot.plot(numpy.gradient(numpy.unwrap(numpy.angle(nco2))))
#pyplot.show()
#s = (nco1 + nco2)[2000 + i:i + SPS * 1024]
#pyplot.scatter(s.real, s.imag)
#pyplot.show()
#exit()

N = 6000
#pyplot.plot(numpy.gradient(numpy.unwrap(numpy.angle(corrected[2000+i:i+SPS*N]))))
#pyplot.show()

#pyplot.plot(diff.real)
#pyplot.plot(diff.imag)
#for j in range(SPS):
#    pyplot.scatter(corrected[2000+i+j:i+SPS*N:SPS].real, corrected[2000+i+j:i+SPS*N:SPS].imag)
#pyplot.plot(numpy.gradient(numpy.unwrap(numpy.angle(corrected[i:i+SPS*128]))))
#pyplot.plot(numpy.abs(nco1 + nco2))
#pyplot.plot(numpy.abs(nco1 - nco2))
#pyplot.plot(tim.real)
#    pyplot.show()
"""