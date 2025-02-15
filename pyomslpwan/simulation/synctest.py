import numpy
from matplotlib import pyplot, ticker
from scipy import signal

from pyomslpwan.simulation.noise import noiseDeviation, complexNoise
from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator
from pyomslpwan.src.uplink.pdu import UplinkFrame
from pyomslpwan.lib.channel import GmskModulator, IqFrequencyModulator
from pyomslpwan.src.structs import BURST_MODE_SINGLE_BURST, BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3

import matplotlib
matplotlib.use("tkagg")



PAYLOAD_SIZE = 255
BURST_MODE = BURST_MODE_SINGLE_BURST
BURST_TYPE = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3

BT = 0.5
SPS = 8
L = 3

FREQ = 868.3e6
SAMP_RATE = 2e9
BAUD = 10e3 #125e3



def generateFrame(timing_input_value, payload, burst_mode, burst_type):
    uplink_generator = BurstModeUplinkGenerator()
    frame = UplinkFrame()
    frame.coded_header.timing_input_value = timing_input_value
    frame.coded_header.burst_mode = burst_mode
    frame.coded_header.burst_type = burst_type
    frame.coded_payload.phy_payload = payload
    uplink_generator.generateFrame(frame)
    return frame

def modulate(bitstream):
    uplink_modulator = GmskModulator(BT, L, SPS)
    iq = uplink_modulator.modulate(bitstream, True)
    return iq

def plotAngle(t, angle):
    pyplot.plot(t, angle)
    ax = pyplot.gca()
    ax.yaxis.set_major_locator(ticker.MultipleLocator(numpy.pi / 2))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(SPS))
    ax.grid(which="major", linewidth=0.5)

def design_complex_bpf(low_edge, high_edge, transition_width, sampling_rate):
    """
    (Generated by DeepSeek)
    Design complex taps for an FIR bandpass filter with specified parameters.

    Parameters:
    low_edge (float): Lower edge of the passband in Hz.
    high_edge (float): Upper edge of the passband in Hz.
    transition_width (float): Width of the transition band in Hz.
    sampling_rate (float): Sampling rate in Hz.

    Returns:
    numpy.ndarray: Complex filter taps.
    """
    Fs = sampling_rate
    f0 = 0.5 * (low_edge + high_edge)  # Center frequency
    BW = high_edge - low_edge  # Bandwidth of the passband

    # Normalized transition width (relative to Nyquist frequency)
    delta = transition_width / (Fs / 2.0)

    # Determine the number of taps and Kaiser parameter for desired attenuation (60 dB)
    atten_dB = 60.0
    numtaps, beta = signal.kaiserord(atten_dB, delta)

    # Ensure the number of taps is odd for symmetry (better lowpass design)
    if numtaps % 2 == 0:
        numtaps += 1

    # Design the lowpass filter with cutoff at BW/2
    cutoff = BW / 2.0
    taps_lowpass = signal.firwin(numtaps, cutoff, window=('kaiser', beta), fs=Fs, pass_zero='lowpass')

    # Calculate time offsets for each tap, centered around the middle
    n = numpy.arange(numtaps)
    t = (n - (numtaps - 1) // 2) / Fs  # Time relative to center

    # Modulate the lowpass filter to the center frequency f0
    complex_exponential = numpy.exp(1j * 2 * numpy.pi * f0 * t)
    taps_complex = taps_lowpass * complex_exponential

    return taps_complex

def design_lpf(corner, transition_width, sampling_rate):
    Fs = sampling_rate
    f0 = 0  # Center frequency
    BW = 2 * corner  # Bandwidth of the passband

    # Normalized transition width (relative to Nyquist frequency)
    delta = transition_width / (Fs / 2.0)

    # Determine the number of taps and Kaiser parameter for desired attenuation (60 dB)
    atten_dB = 60.0
    numtaps, beta = signal.kaiserord(atten_dB, delta)

    # Ensure the number of taps is odd for symmetry (better lowpass design)
    if numtaps % 2 == 0:
        numtaps += 1

    # Design the lowpass filter with cutoff at BW/2
    cutoff = BW / 2.0
    taps_lowpass = signal.firwin(numtaps, cutoff, window=('kaiser', beta), fs=Fs, pass_zero='lowpass')

    # Calculate time offsets for each tap, centered around the middle
    n = numpy.arange(numtaps)
    t = (n - (numtaps - 1) // 2) / Fs  # Time relative to center

    # Modulate the lowpass filter to the center frequency f0
    complex_exponential = numpy.exp(1j * 2 * numpy.pi * f0 * t)
    taps_complex = taps_lowpass * complex_exponential

    return taps_complex

def pll(signal, k_p, k_i, center_freq, samp_rate):
    output = numpy.empty_like(signal)
    integral = 0
    nco_phase = 0
    nco_out = 1
    for i, x in enumerate(signal):
        delta = x * numpy.conjugate(nco_out)
        error = numpy.angle(delta)
        integral += error * k_i
        control = error * k_p + integral
        freq = center_freq + control
        phase_delta = freq * 2 * numpy.pi / samp_rate
        nco_phase = (nco_phase + phase_delta) % numpy.pi
        nco_out = numpy.e ** (1j * nco_phase)
        output[i] = nco_out
    return output

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

import numpy as np
from collections import deque

class GMSKSynchronizer:
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
        self.interp_buffer = deque(maxlen=4)  # For cubic interpolation
        self.prev_sample = None  # Previous interpolated sample for Gardner TED
        
    def _cubic_interp(self, mu):
        # Interpolate using cubic polynomial with self.interp_buffer (4 samples)
        mu2 = mu * mu
        mu3 = mu2 * mu
        a0 = -0.5*mu3 + 1.0*mu2 - 0.5*mu
        a1 = 1.5*mu3 - 2.5*mu2 + 1.0
        a2 = -1.5*mu3 + 2.0*mu2 + 0.5*mu
        a3 = 0.5*mu3 - 0.5*mu2
        return (a0 * self.interp_buffer[0] + a1 * self.interp_buffer[1] +
                a2 * self.interp_buffer[2] + a3 * self.interp_buffer[3])
    
    def synchronize(self, iq_samples):
        synchronized = []
        phase_wrap = 0.0  # Track phase wraps for frequency adjustment
        
        for sample in iq_samples:
            # Frequency correction: mix with NCO
            corrected = sample * np.exp(-1j * self.phase)
            # Frequency error detection (simplified for GMSK)
            error_freq = np.angle(corrected)  # Assumes real-axis alignment; adjust as needed
            # Update PLL
            self.freq += self.beta_freq * error_freq
            self.phase += self.freq + self.alpha_freq * error_freq
            # Keep phase within [0, 2π)
            self.phase %= (2 * np.pi)
            
            # Timing recovery
            self.interp_buffer.append(corrected)
            if len(self.interp_buffer) < 4:
                continue  # Wait for enough samples
            
            # Interpolate at current mu
            interp_sample = self._cubic_interp(self.mu)
            
            # Gardner Timing Error Detection (works best with SPS=2)
            if self.prev_sample is not None:
                error_timing = np.real((interp_sample - self.prev_sample) * np.conj(self.interp_buffer[2]))
                # Update timing loop
                self.timing_error += self.beta_time * error_timing
                self.mu += self.alpha_time * error_timing + (1.0 / self.sps)
                self.mu %= 1.0  # Keep mu within [0,1)
                
                # Check if a symbol should be output
                if self.mu + (1.0 / self.sps) >= 1.0:
                    synchronized.append(interp_sample)
            
            self.prev_sample = interp_sample
        
        return np.array(synchronized)

class CoarseCorrector:

    def __init__(self, avg_size):
        self.avg_size = avg_size
    
    def correct(self, x):
        delta = numpy.insert(x[1:] * numpy.conj(x[:-1]), 0, 0)
        angle = numpy.angle(delta)
        average = numpy.convolve(angle, numpy.ones(self.avg_size))[self.avg_size // 2:self.avg_size // 2 + len(angle)]
        correct_angle = numpy.cumsum(-average)
        csin = numpy.exp(1j * correct_angle)
        y = x * csin
        return y



numpy.random.seed(0)

angdev = numpy.pi / 2
dev = angdev / (2 * numpy.pi)

timing_input_value = numpy.random.randint(0, 128)
payload = numpy.random.randint(0, 256, PAYLOAD_SIZE,  dtype=numpy.uint8).tobytes()
frame = generateFrame(timing_input_value, payload, BURST_MODE, BURST_TYPE)
burst = frame.uplink_0
bitstream = burst.bitstream

padding = SPS * 10
modulated = modulate(bitstream)
padded = numpy.zeros(len(modulated) + 2 * padding, dtype=complex)
padded[padding:len(modulated) + padding] = modulated
t = numpy.linspace(0, (len(padded) - 1) / SPS, len(padded))
true_t = t / BAUD
dt = 1 / SPS
true_dt = dt / BAUD

a = 20e3
omega = 200/a # gives max slope of 200/s
eb_n0 = 3
offset = a * numpy.cos(omega * true_t)
csin = IqFrequencyModulator(true_dt).modulate(2 * numpy.pi * offset)
shifted = padded * csin
noise = complexNoise(noiseDeviation(eb_n0), len(padded))
impaired = shifted + noise

coarse = CoarseCorrector(SPS * 32).correct(impaired)

"""
squared = impaired ** 2
bandpass_1 = design_complex_bpf(-2 * dev * 1.1, -2 * dev * 0.9, 2 * 0.1, SPS)
bandpass_2 = design_complex_bpf(2 * dev * 0.9, 2 * dev * 1.1, 2 * 0.1, SPS)
peak_1 = signal.lfilter(bandpass_1, 1, squared)
peak_2 = signal.lfilter(bandpass_2, 1, squared)

pll1, error1 = PLL(damping_factor=0.707,
                loop_bandwidth=0.1,
                sample_interval=1 / SPS,
                initial_freq=-dev,
                initial_phase=0,
                ratio=1 / 2).process_samples(peak_1)
pll2, error2 = PLL(damping_factor=0.707,
                loop_bandwidth=0.1,
                sample_interval=1 / SPS,
                initial_freq=dev,
                initial_phase=0,
                ratio=1 / 2).process_samples(peak_2)
mixed = pll1 * pll2
lowpass = design_lpf(1/SPS/2, 1/SPS/2, SPS)
pilot = signal.lfilter(lowpass, 1, mixed)
synced = impaired * numpy.conj(pilot)
"""

"""
fft_1 = numpy.fft.fft(peak_1[padding + 32 * SPS:-padding])
fft_2 = numpy.fft.fft(peak_2[padding + 32 * SPS:-padding])
fftfreq = numpy.fft.fftfreq(len(fft_1), 1 / SPS)
pyplot.plot(fftfreq, numpy.abs(fft_1))
pyplot.plot(fftfreq, numpy.abs(fft_2))
"""

"""
fft = numpy.fft.fft(pilot[padding + 32 * SPS:-padding])
fftfreq = numpy.fft.fftfreq(len(fft), 1 / SPS)
pyplot.plot(fftfreq, numpy.abs(fft))
pyplot.show()
"""

#pyplot.plot(angle[padding + 32 * SPS:-padding])
#pyplot.plot(numpy.angle(nco)[padding + 32 * SPS:-padding])
#pyplot.plot(numpy.angle(padded[padding + 32 * SPS:padding + 600 * SPS]))
#pyplot.plot(numpy.angle(pll1)[padding + 32 * SPS:padding + 600 * SPS])
#pyplot.plot(numpy.angle(pll2)[padding + 32 * SPS:padding + 600 * SPS])
#pyplot.plot(numpy.unwrap(numpy.angle(synced)[padding + 32 * SPS:padding + 600 * SPS]))
#pyplot.plot(numpy.angle(csin)[padding + 32 * SPS:padding + 600 * SPS])
#pyplot.plot(numpy.angle(pilot)[padding + 32 * SPS:padding + 600 * SPS])
#pyplot.plot((error1 * 100)[padding + 32 * SPS:padding + 600 * SPS])
#pyplot.plot((error2 * 100)[padding + 32 * SPS:padding + 600 * SPS])
#pyplot.show()

N = 100
sync = GMSKSynchronizer(SPS, 0.0000001, 0.0000001)
synced = sync.synchronize(impaired)
plotAngle(t[:SPS * N], numpy.unwrap(numpy.angle(padded)[:SPS * N]))
plotAngle(t[:SPS * N], numpy.unwrap(numpy.angle(padded + noise)[:SPS * N]))
plotAngle(t[:SPS * N:SPS], numpy.unwrap(numpy.angle(synced[:N])))
#pyplot.plot(t[:SPS * N], offset[:SPS * N])
pyplot.show()