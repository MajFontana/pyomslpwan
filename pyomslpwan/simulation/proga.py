import numpy
from matplotlib import pyplot

import matplotlib
matplotlib.use("tkagg")

from pyomslpwan.lib.channel import GmskModulator, IqFrequencyDemodulator
from pyomslpwan.lib.synchronization import GmskDemod
from pyomslpwan.src.structs import *
from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator, BurstModeUplinkParser
from pyomslpwan.src.uplink.pdu import UplinkFrame, UplinkBurst
from pyomslpwan.src.uplink.stream import UplinkReceiver
from pyomslpwan.lib.coding import binaryToNrz, nrzToBinary
from pyomslpwan.simulation.noise import noiseDeviation, complexNoise



RAND_SEED = 1
GAUSS_SPAN = 3
GAUSS_SPS = 8



uplink_generator = BurstModeUplinkGenerator()
uplink_receiver = UplinkReceiver(0.5, 0.3)
uplink_parser = BurstModeUplinkParser()
uplink_modulator = GmskModulator(0.5, GAUSS_SPAN, GAUSS_SPS)
uplink_demodulator = GmskDemod(GAUSS_SPS, 0.175, 0.005, 0)



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
    txlen = len(iq_tx)
    padlen = int(txlen * 0.2)
    offset = int(padlen * numpy.random.uniform(0.2, 0.8))
    padded = numpy.zeros((txlen) + padlen, dtype=complex)
    padded[offset:offset + txlen] = iq_tx
    k = 10 ** (-2)
    dev = noiseDeviation(ebn0)
    noise = complexNoise(dev, len(padded))
    padded += noise
    return padded



def transmitUplink(burst):
    bitstream = burst.bitstream
    uplink_modulator.clear()
    iq = uplink_modulator.modulate(bitstream, True)
    # Is there also a channel lowpass to deal with transition from 0 to unit amplitude?
    return iq

def receiveUplink(iq):
    # TODO: matching filter
    uplink_demodulator.clear()
    _, synced, nrz, sliced = uplink_demodulator.demodulate(iq)
    bn = "".join(list(map(str, map(int, sliced))))
    uplink_receiver.clear()
    uplink_receiver.feed(iq[::8])
    bursts = uplink_receiver.bursts
    return bursts, bn

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
        bn = "".join(list(map(str, map(int, burst.bitstream))))
        bn = bn[32:]
        #pyplot.plot(IqFrequencyDemodulator(numpy.pi / 2 / GAUSS_SPS).demodulate(iq))
        #pyplot.show()
        iq_rx = channel(iq, ebn0)
        bursts_rx_indiv, bnr = receiveUplink(iq_rx)
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
    TRIALS = 100
    EBN0 = list(range(-8, 8+1, 1))

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

    pyplot.plot(EBN0, measurements, marker="o")
    pyplot.show()