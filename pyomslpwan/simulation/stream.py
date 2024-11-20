import numpy
from scipy.signal import butter, lfilter

from pyomslpwan.src.coding import *
from pyomslpwan.src.channel import *

SYMBOL_RATE = 10

# https://stackoverflow.com/questions/25191620/creating-lowpass-filter-in-scipy-understanding-methods-and-units
# Kačič, Zdravko. (1994). Digitalno procesiranje signalov.

def butter_lowpass(cutoff, fs, order=5):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def rationalResample(samples, I, D):
    interpolated = numpy.zeros(len(samples) * I, dtype=samples.dtype)
    interpolated[::I] = samples
    filtered = butter_lowpass_filter(interpolated, min(1/D, 1/I), I, order=5)
    decimated = filtered[::D]
    return decimated

def upsample(samples, R):
    return numpy.repeat(samples, R)

N = 10

bitstream = numpy.random.randint(0, 2, N)
precoded = Precoder().encode(bitstream)
modulated = UplinkMskModulator().modulate(precoded)
upsampled = rationalResample(modulated, 5, 3)

print(upsampled)

