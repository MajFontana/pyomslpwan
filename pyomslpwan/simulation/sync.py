import numpy
import math
from scipy import signal
from matplotlib import pyplot
import jellyfish

import matplotlib
matplotlib.use("tkagg")

from pyomslpwan.lib.synchronization import *



if __name__ == "__main__":
    from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator
    from pyomslpwan.src.uplink.pdu import UplinkFrame
    from pyomslpwan.src.structs import *
    from pyomslpwan.lib.channel import GmskModulator, IqFrequencyModulator, IqFrequencyDemodulator
    from pyomslpwan.lib.coding import binaryToNrz

    seed = 0
    burst_mode = BURST_MODE_SINGLE_BURST
    burst_type = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3
    size = 255
    bt = 0.5
    span = 3
    sps = 8
    baud = 125000
    interp = 128

    numpy.random.seed(0)

    demodulator = GmskDemod(sps, 0.175, 0.005, 0)

    frame = UplinkFrame()
    frame.coded_header.burst_mode = burst_mode
    frame.coded_header.burst_type = burst_type = 0
    frame.coded_header.timing_input_value = numpy.random.randint(0, 128)
    frame.coded_payload.phy_payload = numpy.random.randint(0, 256, size,  dtype=numpy.uint8).tobytes()
    BurstModeUplinkGenerator().generateFrame(frame)
    bitstream = frame.uplink_0.bitstream#[:64]
    nrz = binaryToNrz(bitstream)
    print(f"Bitstream size: {len(nrz)}")

    modulated = GmskModulator(bt, span, sps).modulate(nrz, padded=True).astype(numpy.complex64)
    print(f"Modulated size: {len(modulated)}")
    
    t = numpy.linspace(0, len(nrz), len(modulated))
    a = (20 / 125) / sps
    f = (0.2/125) / (2 * numpy.pi) / sps
    off = a *  numpy.sin(f * 2 * numpy.pi * t)
    osc = IqFrequencyModulator().modulate(2 * numpy.pi * off)
    shifted = modulated * osc

    #demod = IqFrequencyDemodulator().demodulate(modulated)
    #pyplot.plot(demod[40 * 8:80 * 8])
    #pyplot.show()

    #print("".join(map(str, bitstream.astype(int))))
    #samp_rate = baud * spsprint("".join(map(str, bitstream.astype(int))))
    #resamp = signal.resample_poly(demod, interp, 1)
    #print(f"Resampled size: {len(resamp)} ({len(resamp) / len(demod)})")

    demod, synced, data = demodulator.demodulate(shifted)
    pyplot.plot(demod)
    pyplot.show()
    pyplot.plot(synced)
    pyplot.show()
    pyplot.plot(numpy.array(demodulator.clock_recovery.error))
    pyplot.show()

    bin_in = "".join(map(str, bitstream.astype(int)))
    bin_out = "".join(map(str, data.astype(int)))

    print(bin_in)
    print(bin_out)
    print(jellyfish.levenshtein_distance(bin_in, bin_out))