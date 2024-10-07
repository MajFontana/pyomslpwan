import numpy

from pyomslpwan.lib.coding import binaryToNrz



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