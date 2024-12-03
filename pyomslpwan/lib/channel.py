import numpy
import streamz

from pyomslpwan.lib.coding import binaryToNrz



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



class StreamzCorrelator:

    def __init__(self, pattern):
        self.size = len(pattern)
        self.buffer = None
        self.pattern = pattern
        self.pattern_rms = numpy.sqrt((numpy.abs(self.pattern) ** 2).sum())
    
    def correlate(self, window):
        window_squared = numpy.abs(window) ** 2
        window_rms = numpy.sqrt(window_squared.sum())

        normalized_correlation = (window * self.pattern).sum() / (window_rms * self.pattern_rms)

        return normalized_correlation
    
    def correlation(self, stream: streamz.Stream):
        self.buffer = stream.sliding_window(self.size)
        new_stream = self.buffer.map(self.correlate)
        return new_stream
    
    def clear(self):
        self.buffer._buffer.clear()



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

        sync_indices = numpy.argwhere(numpy.abs(correlation) > self.threshold)[:, 0]
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
        self.phase = self.initial_phase
        if zero_clockwise:
            self.phase_shift_coefficient = 1j
        else:
            self.phase_shift_coefficient = -1j
    
    def clear(self):
        self.phase = self.initial_phase

    def demodulate(self, modulated):
        phase_offset = self.phase * self.phase_shift_coefficient
        phase = phase_offset * numpy.insert(numpy.cumprod(numpy.full(len(modulated) - 1, -self.phase_shift_coefficient)), 0, 1)
        nrz = numpy.real(modulated / phase)
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
        self.state = input_with_history[:-len(self.kernel)]
        filtered = numpy.convolve(input_with_history, self.kernel, "valid")
        return filtered



class IqFrequencyModulator:

    def __init__(self):
        self.initial_phase = 0

    def modulate(self, argument):
        argument = numpy.insert(argument, 0, self.initial_phase)
        angle = numpy.cumsum(argument) % (2 * numpy.pi)
        iq = numpy.exp(1j * angle)
        return iq



class IqFrequencyDemodulator:

    def __init__(self):
        self.previous_sample = 0

    def modulate(self, iq):
        iq = numpy.insert(iq, 0, self.previous_sample)
        delta = iq[1:] * iq[:-1].conjugate()
        angle = numpy.arctan2(delta.real, de)
        return iq



class GmskModulator:

    def __init__(self, bandwidth_time_product, kernel_span, samples_per_symbol):
        self.filter = GaussianFilter(bandwidth_time_product, kernel_span, samples_per_symbol)
        self.sensitivity = (numpy.pi / 2) / sum(self.filter.kernel)
        self.modulator = IqFrequencyModulator()
    
    def modulate(self, bits, padded=False):
        filtered = self.filter.filter(bits, padded) * self.sensitivity
        modulated = self.modulator.modulate(filtered)
        return modulated



class FskDemodulator:

    def __init__(self, bandwidth_time_product, kernel_span, samples_per_symbol):
        self.filter = GaussianFilter(bandwidth_time_product, kernel_span, samples_per_symbol)
        self.sensitivity = (numpy.pi / 2) / sum(self.filter.kernel)
        self.modulator = IqFrequencyModulator()
    
    def modulate(self, bits, padded=False):
        filtered = self.filter.filter(bits, padded) * self.sensitivity
        modulated = self.modulator.modulate(filtered)
        return modulated