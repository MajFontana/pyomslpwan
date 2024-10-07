import numpy
from matplotlib import pyplot
import random
import itertools
from ..lib.coding import binaryToNrz
from ..downlink.link import WMbusMModeDownlink, WMbusMModeDownlinkParser
from ..src.structs import *



def simulate_channel(signal, eb_n0):
    dev = numpy.sqrt(1 / (2 * eb_n0))
    noise = numpy.random.normal(0, dev, signal.shape)
    received = signal + noise
    return received



def fec_test_sample(message_size, fec_rate, eb_n0):
    subid = random.randint(0, 255)
    message = numpy.random.randint(0, 256, message_size,  dtype=numpy.uint8).tobytes()

    bitstream = wmbusm.createSingleBurst(subid, message, fec_rate).getBitstream()
    signal = numpy.zeros(6296)
    signal[:len(bitstream)] = binaryToNrz(bitstream)
    received = simulate_channel(signal, eb_n0)

    try:
        header_index = 64
        header_size = 96
        header = wmbusm.parseHeader(received[header_index:header_index + header_size], soft=True)

        data_size = wmbusm.calculateDataLength(header)
        data_index = header_index + header_size
        coded_payload = wmbusm.parseData(header, received[data_index:data_index + data_size], soft=True)

        subid_r = header.device_sub_id.getBits().uint
        length_r = header.phy_payload_length.getBits().uint
        mode_r = header.burst_mode.getBits().uint
        type_r = header.burst_type.getBits().uint
        assert subid_r == subid
        assert mode_r == BURST_MODE_SINGLE_BURST
        assert type_r == fec_rate
        assert length_r == len(message)
    except (AssertionError, NotImplementedError):
        return None

    message_r = coded_payload.phy_payload.getBits().bytes
    errors = (numpy.unpackbits(numpy.frombuffer(message, dtype=numpy.uint8)) ^ numpy.unpackbits(numpy.frombuffer(message_r, dtype=numpy.uint8))).sum()
    ber = errors / (len(message) * 8)
    return ber



def detection_test_sample(threshold, eb_n0):
    signal = numpy.zeros(6296 * 2)
    signal[6296:6296 + 32] = parser.correlator.pattern
    received = simulate_channel(signal, eb_n0)

    parser.clear()
    matches, messages = parser.feed(received, threshold)
    loss = 6296 not in matches

    messages = list(filter(lambda x: x[0] != 6296, messages))
    false_positive_rate = len(messages) / len(signal)

    return loss, false_positive_rate



def fec_test(sample_count, message_size, fec_rate, eb_n0):
    ber_arr = []
    loss_count = 0

    for i in range(sample_count):
        ber = fec_test_sample(message_size, fec_rate, 10 ** (eb_n0 / 10))
        if ber is not None:
            ber_arr.append(ber)
        else:
            loss_count += 1
    
    if ber_arr:
        error_rate = numpy.array(ber_arr).mean()
    else:
        error_rate = numpy.nan
    loss_rate = loss_count / sample_count
    return (error_rate, loss_rate)



def detection_test(sample_count, threshold, eb_n0):
    fpr_arr = []
    loss_count = 0

    for i in range(sample_count):
        loss, fpr = detection_test_sample(threshold, 10 ** (eb_n0 / 10))
        loss_count += int(loss)
        fpr_arr.append(fpr)
    
    false_positive_rate = numpy.array(fpr_arr).mean()
    false_negative_rate = loss_count / sample_count
    return (false_positive_rate, false_negative_rate)



def plot_detection():
    SAMPLE_SIZE = 10
    EBN0_RANGE = [-5, 10]
    EBN0_COUNT = 16
    THRESHOLD_RANGE = [0.5, 0.9]
    THRESHOLD_COUNT = 5

    eb_n0_arr = numpy.linspace(*EBN0_RANGE, EBN0_COUNT)
    threshold_arr = numpy.linspace(*THRESHOLD_RANGE, THRESHOLD_COUNT)

    fpr_arr = numpy.empty((EBN0_COUNT, THRESHOLD_COUNT))
    fnr_arr = numpy.empty((EBN0_COUNT, THRESHOLD_COUNT))

    fig, ax = pyplot.subplots(1, 2)

    for x, eb_n0 in enumerate(eb_n0_arr):
        for y, threshold in enumerate(threshold_arr):
            fpr, fnr = detection_test(SAMPLE_SIZE, threshold, eb_n0)
            fpr_arr[x, y] = fpr
            fnr_arr[x, y] = fnr

    marker = itertools.cycle(("o", "v", "s", "x", "^")) 
    for y, _ in enumerate(threshold_arr):
        m = next(marker)
        ax[0].plot(eb_n0_arr, fpr_arr[:, y], marker=m)
        ax[1].plot(eb_n0_arr, fnr_arr[:, y], marker=m)
        
    ax[0].set_title("False positive rate")
    ax[0].set_xlabel(r"$E_b/N_0 [dB]$")
    ax[0].set_yscale("log")
    ax[0].grid(True)

    ax[1].set_title("False negative rate")
    ax[1].set_xlabel(r"$E_b/N_0 [dB]$")
    ax[1].set_yscale("log")
    ax[1].grid(True)

    fig.legend([f"{th:.2f}" for th in threshold_arr], title="Threshold")

    pyplot.show()



def plot_fec():
    SAMPLE_SIZE = 10
    EBN0_RANGE = [-10, 10]
    EBN0_COUNT = 21
    MESSAGE_SIZE = 255

    eb_n0_arr = numpy.linspace(*EBN0_RANGE, EBN0_COUNT)
    fecrate_arr = numpy.array([0, 1, 2], dtype=int)

    err_arr = numpy.empty((EBN0_COUNT, 3))
    loss_arr = numpy.zeros(EBN0_COUNT)

    fig, ax = pyplot.subplots(1, 2)

    for x, eb_n0 in enumerate(eb_n0_arr):
        for y, fecrate in enumerate(fecrate_arr):
            err, loss = fec_test(SAMPLE_SIZE, MESSAGE_SIZE, int(fecrate), eb_n0)
            err_arr[x, y] = err
            loss_arr[x] += loss
    loss_arr /= 3

    marker = itertools.cycle(("o", "v", "s", "x", "^")) 
    for y, _ in enumerate(fecrate_arr):
        m = next(marker)
        ax[0].plot(eb_n0_arr, err_arr[:, y], marker=m)
    ax[1].plot(eb_n0_arr, loss_arr)
        
    ax[0].set_title("BER")
    ax[0].set_xlabel(r"$E_b/N_0 [dB]$")
    ax[0].set_yscale("log")
    ax[0].grid(True)

    ax[1].set_title("Frame loss")
    ax[1].set_xlabel(r"$E_b/N_0 [dB]$")
    ax[1].set_yscale("log")
    ax[1].grid(True)

    fig.legend(["7/8", "1/2", "1/3"], title="FEC rate")

    pyplot.show()



random.seed(0)
numpy.random.seed(0)

wmbusm = WMbusMModeDownlink()
parser = WMbusMModeDownlinkParser(soft=True)