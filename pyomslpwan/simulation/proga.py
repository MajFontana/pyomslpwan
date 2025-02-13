import numpy
from matplotlib import pyplot

import matplotlib
matplotlib.use("tkagg")

from pyomslpwan.lib.channel import GmskModulator, IqFrequencyModulator, GMSKSynchronizer
from pyomslpwan.src.structs import *
from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator, BurstModeUplinkParser
from pyomslpwan.src.uplink.pdu import UplinkFrame, UplinkBurst
from pyomslpwan.src.uplink.stream import UplinkReceiver
from pyomslpwan.lib.coding import binaryToNrz, nrzToBinary
from pyomslpwan.simulation.noise import noiseDeviation, complexNoise
from pyomslpwan.simulation.plotting import plotSingle



RAND_SEED = 1
GAUSS_SPAN = 3
GAUSS_SPS = 8

BAUD = 10e3 #125e3
SAMP_RATE = BAUD * GAUSS_SPS

MAX_OFFSET = 20e3
MAX_DRIFT = 200

FREQ_COEF = 1 / GAUSS_SPS / 100
TIME_COEF = 0



uplink_generator = BurstModeUplinkGenerator()
uplink_receiver = UplinkReceiver(0.5, 0.3)
uplink_parser = BurstModeUplinkParser()
uplink_modulator = GmskModulator(0.5, GAUSS_SPAN, GAUSS_SPS)
uplink_synchronizer = GMSKSynchronizer(GAUSS_SPS, FREQ_COEF, TIME_COEF)



import numpy as np
from scipy.signal import resample_poly
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

def windowed_sinc_interp(x, t_orig, t_new, kernel_width=4, window_func=None):
    """
    Interpolates a bandlimited signal using windowed sinc interpolation.
    
    Parameters:
        x (array_like): Original samples (can be complex).
        t_orig (array_like): Time instants corresponding to x (assumed uniform).
        t_new (array_like): Desired time instants for interpolation.
        kernel_width (float): Number of sample periods (to each side) to use in the interpolation (default: 4).
        window_func (callable, optional): A window function applied to the normalized distances.
            It should accept an array of distances (in units of sample periods) and return an array of weights.
            If None, a Hann window is used.
            
    Returns:
        y (ndarray): Interpolated values at times t_new.
    """
    t_orig = np.asarray(t_orig)
    t_new = np.asarray(t_new)
    x = np.asarray(x)
    
    # Compute the effective sampling period (assumes uniform t_orig)
    T = np.median(np.diff(t_orig))
    y = np.zeros(len(t_new), dtype=x.dtype)

    # Define a default Hann window if none is provided.
    if window_func is None:
        def window_func(d):
            # d: normalized distances in sample periods.
            # Use a Hann window that is nonzero for |d| < kernel_width.
            d = np.asarray(d)
            w = np.zeros_like(d)
            mask = np.abs(d) < kernel_width
            w[mask] = 0.5 * (1 + np.cos(np.pi * d[mask] / kernel_width))
            return w

    # For each new time instant, compute the interpolation.
    for i, t in enumerate(t_new):
        # Only consider original samples within kernel_width * T of t.
        idx = np.where(np.abs(t - t_orig) < kernel_width * T)[0]
        if len(idx) == 0:
            # Should not happen if t_new lies within the range of t_orig;
            # fall back to nearest sample.
            idx = np.array([np.argmin(np.abs(t - t_orig))])
        # Normalized distances (in units of T)
        d = (t - t_orig[idx]) / T
        # np.sinc is defined as sin(pi*x)/(pi*x)
        sinc_weights = np.sinc(d)
        # Apply the window function
        w = window_func(d)
        weights = sinc_weights * w
        # Normalize weights so they sum to 1 (optional but can help with amplitude accuracy)
        if np.sum(weights) != 0:
            weights /= np.sum(weights)
        y[i] = np.dot(x[idx], weights)
    return y

def two_step_resample(x, t_orig, t_new, oversampling_factor=10, kind='cubic'):
    """
    Resamples a uniformly sampled signal at arbitrary time instants by first oversampling
    using a Fourier‐based method (resample_poly) and then interpolating on the fine grid.
    
    Parameters:
        x (array_like): Original samples (can be complex).
        t_orig (array_like): Original time instants corresponding to x (assumed uniform).
        t_new (array_like): Desired time instants for interpolation.
        oversampling_factor (int): Factor by which to upsample the signal (default: 10).
        kind (str): Type of interpolation to use in interp1d (e.g., 'linear', 'cubic'; default: 'cubic').
        
    Returns:
        y (ndarray): Interpolated values at times t_new.
    """
    t_orig = np.asarray(t_orig)
    t_new = np.asarray(t_new)
    x = np.asarray(x)
    
    # Compute original sampling period.
    T = np.median(np.diff(t_orig))
    t_start, t_end = t_orig[0], t_orig[-1]
    # Create a uniformly spaced time grid at the oversampled rate.
    T_new = T / oversampling_factor
    t_uniform = np.arange(t_start, t_end + T_new, T_new)
    
    # Upsample using resample_poly (this performs bandlimited interpolation).
    x_upsampled = resample_poly(x, up=oversampling_factor, down=1)
    
    # Due to filter delays, the length of x_upsampled may differ slightly from t_uniform.
    # Trim to the minimum common length.
    min_len = min(len(t_uniform), len(x_upsampled))
    t_uniform = t_uniform[:min_len]
    x_upsampled = x_upsampled[:min_len]
    
    # Now use interp1d to interpolate the oversampled signal at the desired times.
    interpolator = interp1d(t_uniform, x_upsampled, kind=kind, fill_value="extrapolate")
    y = interpolator(t_new)
    return y



def generateFrameUplink(timing_input_value, payload, burst_mode, burst_type):
    frame = UplinkBurst()
    frame.coded_header.timing_input_value = timing_input_value
    frame.coded_header.burst_mode = burst_mode
    frame.coded_header.burst_type = burst_type
    frame.coded_payload.phy_payload = payload

    uplink_generator.generateFrame(frame)
    return frame

def compareHeaders(header1, header2):
    return header1.timing_input_value == header2.timing_input_value\
        and header1.burst_mode == header2.burst_mode\
        and header1.burst_type == header2.burst_type\
        and header1.phy_payload_length == header2.phy_payload_length



def channel(iq_tx, ebn0):
    impaired = iq_tx

    # Add randomized padding to give room to demodulator
    # and to randomize the initial phase of PLLs
    txlen = len(iq_tx)
    padlen = int(txlen * 0.2)
    offset = int(padlen * numpy.random.uniform(0.2, 0.8))
    padded = numpy.zeros((txlen) + padlen, dtype=complex)
    padded[offset:offset + txlen] = impaired
    impaired = padded

    # Add a changingfrequency offset following a sine pattern
    # with a random initial phase
    t = numpy.linspace(0, (len(impaired) - 1) / SAMP_RATE, len(impaired))
    offset_omega = MAX_DRIFT / MAX_OFFSET # gives max slope of MAX_DRIFT/s
    offset_phi = numpy.random.random() * 2 * numpy.pi
    offset = MAX_OFFSET * numpy.sin(offset_omega * t + offset_phi)
    
    complex_sine = IqFrequencyModulator(1 / SAMP_RATE).modulate(2 * numpy.pi * offset)
    shifted = impaired * complex_sine
    impaired = shifted
    

    # Add AWG noise
    dev = noiseDeviation(ebn0)
    noise = complexNoise(dev, len(impaired))
    impaired += noise 

    return impaired



def transmitUplink(burst):
    bitstream = burst.bitstream
    uplink_modulator.clear()
    iq = uplink_modulator.modulate(bitstream, True)
    # Is there also a channel lowpass to deal with transition from 0 to unit amplitude?
    return iq

def receiveUplink(iq):
    # TODO: matching filter
    uplink_synchronizer = GMSKSynchronizer(GAUSS_SPS, FREQ_COEF, TIME_COEF)
    f_error, p_error, f_correct, a1, a2, synchronized = uplink_synchronizer.synchronize(iq)
    pyplot.plot(numpy.unwrap(numpy.angle(f_correct)))
    #pyplot.plot(p_error)
    pyplot.show()
    uplink_receiver.clear()
    uplink_receiver.feed(iq[::8])
    bursts = uplink_receiver.bursts
    return bursts

def simulateUplink(frame, ebn0):
    #print("Simulating transmission of a frame ...")
    #input("".join(list(map(str, frame.uplink_0.bitstream))))
    if burst_mode == BURST_MODE_SINGLE_BURST:
        bursts = [frame.uplink_0]
    else:
        bursts = [frame.uplink_1, frame.uplink_2, frame.uplink_3]

    bursts_rx = []
    for burst in bursts:
        #print("Simulating transmission of a burst ...")
        iq = transmitUplink(burst)
        #bn = "".join(list(map(str, map(int, burst.bitstream))))
        #bn = bn[32:]
        #pyplot.plot(IqFrequencyDemodulator(numpy.pi / 2 / GAUSS_SPS).demodulate(iq))
        #pyplot.show()
        iq_rx = channel(iq, ebn0)
        bursts_rx_indiv = receiveUplink(iq_rx)
        #print("No. of detected bursts:", len(bursts_rx_indiv))
        #index = bnr.find("11000001111110100100110001101010")
        #if index >= 0:
        #    bnr = bnr[bnr.find("11000001111110100100110001101010"):]
        #    bnr = bnr[:len(bn)]
        #    import jellyfish
        #    print("Intact syncword detected, Levenshtein distance:", jellyfish.levenshtein_distance(bn, bnr))
       
        for burst_rx in bursts_rx_indiv:
            if compareHeaders(frame.coded_header, burst_rx.coded_header):
                bursts_rx.append(burst_rx)
                continue
        bursts_rx.append(None)
    
    if not any(map(lambda b: b is not None, bursts_rx)):
        return None
    
    frame_rx = UplinkFrame()
    if burst_mode == BURST_MODE_SINGLE_BURST:
        frame_rx.uplink_0 = bursts_rx[0]
    else:
        frame_rx.uplink_1, frame_rx.uplink_2, frame_rx.uplink_3 = bursts_rx
    uplink_parser.parseFrame(frame_rx)
    return frame_rx

def testUplink(timing_input_value, payload, burst_mode, burst_type, ebn0):
    frame = generateFrameUplink(timing_input_value, payload, burst_mode, burst_type)
    frame_rx = simulateUplink(frame, ebn0)
    if frame_rx is not None:
        return frame.coded_payload.phy_payload == frame_rx.coded_payload.phy_payload
    else:
        return False



if __name__ == "__main__":
    numpy.random.seed(RAND_SEED)

    payload_size = 255
    burst_mode = BURST_MODE_SINGLE_BURST
    burst_type = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3
    TRIALS = 2
    EBN0 = numpy.fromiter(range(80, 80+1, 1), dtype=int)

    measurements = []
    for ebn0 in EBN0:
        successes = 0
        for i in range(TRIALS):
            timing_input_value = numpy.random.randint(0, 128)
            payload = numpy.random.randint(0, 256, payload_size,  dtype=numpy.uint8).tobytes()

            if testUplink(timing_input_value, payload, burst_mode, burst_type, ebn0):
                successes += 1
            
            print(f"\rSuccessful transmissions: {successes:04d}/{(i + 1):04d}", end="")
        print()
        measurements.append(successes / TRIALS)
    measurements = numpy.array(measurements)

    plotSingle(
        pyplot.gca(),
        EBN0,
        measurements * 100,
        "Verjetnost uspešnega prenosa (z naključnim +-20 kHz odmikom)",
        r"$E_b/N_0 [dB]$",
        r"Verjetnost [%]",
        log=False)
    pyplot.show()