import numpy
from scipy import signal
from matplotlib import pyplot

import matplotlib
matplotlib.use("tkagg")

if __name__ == "__main__":
    from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator
    from pyomslpwan.src.uplink.pdu import UplinkFrame
    from pyomslpwan.src.structs import *
    from pyomslpwan.lib.channel import GmskModulator, IqFrequencyDemodulator
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

    frame = UplinkFrame()
    frame.coded_header.burst_mode = burst_mode
    frame.coded_header.burst_type = burst_type = 0
    frame.coded_header.timing_input_value = numpy.random.randint(0, 128)
    frame.coded_payload.phy_payload = numpy.random.randint(0, 256, size,  dtype=numpy.uint8).tobytes()
    BurstModeUplinkGenerator().generateFrame(frame)
    bitstream = frame.uplink_0.bitstream
    nrz = binaryToNrz(bitstream)
    print(f"Bitstream size: {len(nrz)}")

    modulated = GmskModulator(bt, span, sps).modulate(nrz, padded=True).astype(numpy.complex64)
    print(f"Modulated size: {len(modulated)}")
    
    #off = 0.2
    #t = numpy.linspace(0, len(nrz), len(modulated))
    #osc = numpy.sin(off * 2 * numpy.pi * t) + 1j * numpy.cos(off * 2 * numpy.pi * t)
    #shifted = modulated * osc

    demod = IqFrequencyDemodulator().demodulate(modulated)
    pyplot.plot(demod[40 * 8:80 * 8])
    pyplot.show()

    samp_rate = baud * sps

    resamp = signal.resample_poly(demod, interp, 1)
    print(f"Resampled size: {len(resamp)} ({len(resamp) / len(demod)})")

    prev_sample = 0
    prev_decision = 0

    avg_period = 0
    phase = 0

    for i in range(len(resamp)):
        sample = resamp[i]
        decision = sample > 0

        error = decision * prev_sample - prev_decision * sample

        avg_period = avg_period + beta * error
        inst_period = avg_period + alpha * error
        if inst_period <= 0:
            inst_period = avg_period
        phase = (phase + inst_period) % (2 * numpy.pi)

        prev_sample = sample
        prev_decision = decision

    resamp_delay = resamp[:-interp * sps]
    resamp_now = resamp[interp * sps:]
    
    decision = resamp > 0
    decision_delay = decision[  :-interp * sps]
    decision_now = decision[interp * sps:]
    
    error = resamp_now * decision_delay - decision_now * resamp_delay

    pyplot.plot(error[:8 * 128 * 16])
    pyplot.show()