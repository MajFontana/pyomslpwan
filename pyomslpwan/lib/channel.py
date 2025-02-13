import numpy
from collections import deque
import numba

from pyomslpwan.lib.coding import binaryToNrz



NUMBA_PARAMS = dict(cache=True)



def gaussdesign(bt, span, sps):
    n = span * sps
    t_range = (n - 1) / sps / 2
    t = numpy.linspace(-t_range, t_range, n)
    delta = numpy.sqrt(numpy.log(2)) / (2 * numpy.pi * bt)
    h = numpy.exp(-t ** 2 / (2 * delta ** 2)) / (numpy.sqrt(2 * numpy.pi) * delta)
    return h



class Correlator:

    def __init__(self, pattern):
        self.size = len(pattern)
        self.buffer = numpy.zeros(self.size - 1, dtype=complex)
        self.pattern = pattern
        self.pattern_rms = numpy.sqrt((numpy.abs(self.pattern) ** 2).sum())
    
    def correlate(self, samples): # consider scipy.signal.correlate / convolve
        padded_samples = numpy.concatenate([self.buffer, samples])

        window_squared = numpy.lib.stride_tricks.sliding_window_view(numpy.abs(padded_samples) ** 2, self.size)
        window_rms = numpy.sqrt(window_squared.sum(axis=1))

        normalized_correlation = numpy.correlate(padded_samples, self.pattern) / (window_rms * self.pattern_rms)

        self.buffer = padded_samples[-(self.size - 1):]
        return normalized_correlation
    
    def clear(self):
        self.buffer[:] = 0



class SyncwordSynchronizer:

    def __init__(self, syncword, syncword_offset, threshold):
        self.correlator = Correlator(syncword)
        self.threshold = threshold
        self.syncword_offset = syncword_offset

        self.min_buffer_size = self.syncword_offset + self.correlator.size - 1
        self.buffer = numpy.zeros(self.min_buffer_size, dtype=complex)
        self.position = 0

        self.streams = []
    
    def clear(self):
        self.correlator.clear()

        self.buffer = numpy.zeros(self.min_buffer_size, dtype=complex)
        self.position = 0
        self.streams = []
    
    def trimBuffer(self):
        if len(self.streams) != 0:
            index = self.streams[0]["position"] - self.position
            stream_size = len(self.buffer) - index
            keep_size = max(stream_size, self.min_buffer_size)
        else:
            keep_size = self.min_buffer_size
        trim_index = len(self.buffer) - keep_size
        self.buffer = self.buffer[trim_index:]
        self.position += trim_index
    
    def feed(self, samples):
        correlation = self.correlator.correlate(samples)
        from matplotlib import pyplot
        #pyplot.plot(numpy.absolute(correlation))
        #pyplot.show()

        sync_indices = numpy.argwhere(numpy.abs(correlation) > self.threshold)[:, 0]
        #print(sync_indices)
        for index in sync_indices:
            sync_position = self.position + len(self.buffer) + index - (self.correlator.size - 1)
            start_position = sync_position - self.syncword_offset

            phase_shift = correlation[index] / numpy.abs(correlation[index])
            self.streams.append({"position": start_position, "phase_shift": phase_shift})

        self.buffer = numpy.concatenate([self.buffer, samples])
        self.trimBuffer()
    
    def getBuffer(self):
        stream = self.streams[0]
        index = stream["position"] - self.position
        samples = self.buffer[index:] / stream["phase_shift"]
        return samples
    
    def getSize(self):
        if len(self.streams) == 0:
            return 0
        else:
            index = self.streams[0]["position"] - self.position
            return len(self.buffer) - index
    
    def nextMatch(self):
        self.streams.pop(0)
        self.trimBuffer()



class MskModulator:

    def __init__(self, initial_phase, zero_clockwise):
        self.initial_phase = initial_phase
        self.phase = self.initial_phase
        if zero_clockwise:
            self.phase_shift_coefficient = 1j
        else:
            self.phase_shift_coefficient = -1j
    
    def clear(self):
        self.phase = self.initial_phase

    def modulate(self, bitstream):
        phase_shifts = binaryToNrz(bitstream) * self.phase_shift_coefficient
        modulated = self.phase * numpy.cumprod(phase_shifts)
        self.phase = modulated[-1]
        return modulated



class PrecodedMskDemodulator:

    def __init__(self, initial_phase, zero_clockwise):
        self.initial_phase = initial_phase
        if zero_clockwise:
            self.phase_shift_coefficient = 1j
        else:
            self.phase_shift_coefficient = -1j
        self.phase = self.initial_phase * self.phase_shift_coefficient
    
    def clear(self):
        self.phase = self.initial_phase * self.phase_shift_coefficient

    def demodulate(self, modulated):
        phase = self.phase * numpy.insert(numpy.cumprod(numpy.full(len(modulated), -self.phase_shift_coefficient)), 0, 1)
        nrz = numpy.real(modulated / phase[:-1])
        self.phase = phase[-1]
        return nrz



class PulseUpsampler:

    def __init__(self, interpolation):
        self.interpolation = interpolation

    def upsample(self, samples):
        pulses = numpy.zeros(len(samples) * self.interpolation)
        pulses[::self.interpolation] = samples
        return pulses



class GaussianFilter:

    def __init__(self, bandwidth_time_product, kernel_span, samples_per_symbol):
        self.upsampler = PulseUpsampler(samples_per_symbol)
        self.kernel = gaussdesign(bandwidth_time_product, kernel_span, samples_per_symbol)
        self.state = numpy.zeros(len(self.kernel) - 1)
    
    def filter(self, samples, padded=False):
        upsampled = self.upsampler.upsample(samples)
        input_with_history = numpy.concatenate([self.state, upsampled])
        if padded:
            input_with_history = numpy.concatenate([input_with_history, numpy.zeros_like(self.state)])
        self.state = input_with_history[-len(self.kernel):]
        filtered = numpy.convolve(input_with_history, self.kernel, "valid")
        return filtered
    
    def clear(self):
        self.state = numpy.zeros(len(self.kernel) - 1)



class IqFrequencyModulator:

    def __init__(self, sensitivity):
        self.initial_phase = 0
        self.sensitivity = sensitivity

    def modulate(self, argument):
        argument = numpy.insert(argument * self.sensitivity, 0, self.initial_phase)
        angle = numpy.cumsum(argument) % (2 * numpy.pi)
        iq = numpy.exp(1j * angle)
        return iq[1:]



class IqFrequencyDemodulator:

    def __init__(self, sensitivity):
        self.sensitivity = sensitivity
        self.previous_sample = 0

    def demodulate(self, iq):
        iq = numpy.insert(iq, 0, self.previous_sample)
        delta = iq[1:] * iq[:-1].conjugate()
        angle = numpy.arctan2(delta.imag, delta.real)
        angle /= self.sensitivity
        return angle



class GfskModulator:

    def __init__(self, bandwidth_time_product, kernel_span, samples_per_symbol, sensitivity):
        self.filter = GaussianFilter(bandwidth_time_product, kernel_span, samples_per_symbol)
        self.sensitivity = sensitivity / samples_per_symbol #/ numpy.sum(self.filter.kernel) 
        self.modulator = IqFrequencyModulator(self.sensitivity)
    
    def modulate(self, bits, padded=False):
        nrz = binaryToNrz(bits)
        filtered = self.filter.filter(nrz, padded)
        modulated = self.modulator.modulate(filtered)
        return modulated
    
    def clear(self):
        self.filter.clear()



class GmskModulator(GfskModulator):

    def __init__(self, *args):
        sensitivity = numpy.pi / 2
        super().__init__(*args, sensitivity)




@numba.njit(**NUMBA_PARAMS)
def _cubic_interp(interp_buffer, mu):
    # Interpolate using cubic polynomial with self.interp_buffer (4 samples)
    mu2 = mu * mu
    mu3 = mu2 * mu
    a0 = -0.5*mu3 + 1.0*mu2 - 0.5*mu
    a1 = 1.5*mu3 - 2.5*mu2 + 1.0
    a2 = -1.5*mu3 + 2.0*mu2 + 0.5*mu
    a3 = 0.5*mu3 - 0.5*mu2
    return (a0 * interp_buffer[0] + a1 * interp_buffer[1] +
            a2 * interp_buffer[2] + a3 * interp_buffer[3])

@numba.njit(**NUMBA_PARAMS)
def _synchronize(
    phase,
    freq,
    alpha_freq,
    beta_freq,
    interp_buffer,
    prev_sample,
    mu,
    sps,
    alpha_time,
    beta_time,
    timing_error,
    iq_samples):

    a1 = [1j]
    a2 = [1j]
    f_error = [0.0]
    p_error = [0.0]
    f_correct = [1j]
    f_error.pop(0)
    p_error.pop(0)
    f_correct.pop(0)
    a1.pop(0)
    a2.pop(0)

    synchronized = [1j]
    synchronized.pop(0)
    interp_buffer.pop(-1)
    phase_wrap = 0.0  # Track phase wraps for frequency adjustment
    
    for sample in iq_samples:
        # Frequency correction: mix with NCO
        corrected = sample * numpy.exp(-1j * phase)
        a1.append(sample)
        a2.append(numpy.exp(-1j * phase))
        f_correct.append(corrected)
        # Frequency error detection (simplified for GMSK)
        error_freq = numpy.angle(corrected)  # Assumes real-axis alignment; adjust as needed
        f_error.append(error_freq)
        # Update PLL
        freq += beta_freq * error_freq
        phase += freq + alpha_freq * error_freq
        # Keep phase within [0, 2π)
        phase %= (2 * numpy.pi)
        
        # Timing recovery
        interp_buffer.append(corrected)
        if len(interp_buffer) < 4:
            continue  # Wait for enough samples
        if len(interp_buffer) == 5:
            interp_buffer.pop(0)
        
        # Interpolate at current mu
        interp_sample = _cubic_interp(interp_buffer, mu)
        
        # Gardner Timing Error Detection (works best with SPS=2)
        if prev_sample is not None:
            error_timing = numpy.real((interp_sample - prev_sample) * numpy.conj(interp_buffer[2]))
            p_error.append(error_timing)
            # Update timing loop
            timing_error += beta_time * error_timing
            mu += (alpha_time * error_timing + timing_error) + (1.0 / sps)
            mu %= 1.0  # Keep mu within [0,1)
            
            # Check if a symbol should be output
            if mu + (1.0 / sps) >= 1.0:
                synchronized.append(interp_sample)
        
        prev_sample = interp_sample
    
    return freq, phase, timing_error, mu, prev_sample, numpy.array(f_error), numpy.array(p_error), numpy.array(f_correct), numpy.array(a1), numpy.array(a2),  numpy.array(synchronized)

class GMSKSynchronizer:
    # Generated by DeepSeek
    def __init__(self, sps, loop_bandwidth_freq=0.05, loop_bandwidth_time=0.05, damping=0.707):
        self.sps = sps  # Samples per symbol
        # Frequency recovery (PLL) parameters
        self.phase = 0.0
        self.freq = 0.0
        self.damping = damping
        self.loop_bw_freq = loop_bandwidth_freq
        # Compute PLL coefficients (alpha and beta)
        theta = loop_bandwidth_freq / (damping + 1/(4*damping))
        delta = (1 + 2*damping*theta + theta**2)
        self.alpha_freq = (4 * damping * theta) / delta
        self.beta_freq = (4 * theta**2) / delta
        
        # Timing recovery parameters
        self.mu = 0.0  # Fractional interval [0, 1)
        self.loop_bw_time = loop_bandwidth_time
        theta_time = loop_bandwidth_time / (damping + 1/(4*damping))
        delta_time = (1 + 2*damping*theta_time + theta_time**2)
        self.alpha_time = (4 * damping * theta_time) / delta_time
        self.beta_time = (4 * theta_time**2) / delta_time
        self.timing_error = 0.0
        #self.interp_buffer = deque(maxlen=4)  # For cubic interpolation
        self.interp_buffer = []
        self.prev_sample = None  # Previous interpolated sample for Gardner TED
    
    def synchronize(self, iq_samples):
        self.interp_buffer.append(1j)
        self.freq, self.phase, self.timing_error, self.mu, self.prev_sample, f_error, p_error, f_correct, a1, a2, output =\
        output = _synchronize(
            self.phase,
            self.freq,
            self.alpha_freq,
            self.beta_freq,
            self.interp_buffer,
            self.prev_sample,
            self.mu,
            self.sps,
            self.alpha_time,
            self.beta_time,
            self.timing_error,
            iq_samples)
        return f_error, p_error, f_correct, a1, a2, output