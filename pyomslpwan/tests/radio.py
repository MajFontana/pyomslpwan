import time
import numpy
import zmq
import threading

from ..uplink.stream import BurstModeUplinkTransmitter
from ..uplink.frame import BurstModeUplinkGenerator
from ..src.structs import *
from ..lib.coding import binaryToNrz



PORT = 12345



def generate():
    class Struct:
        pass

    generator = BurstModeUplinkGenerator()
    transmitter = BurstModeUplinkTransmitter(300)

    def send():
        tt = 0
        while True:
            t = transmitter.time
            while tt < t + 5:
                frame = Struct()
                bits = generator.createSingleBurst(0, b"Hello world!", BURST_TYPE_DOWNLINK_SINGLE_BURST_FEC_RATE_7_8).getBitstream()
                frame.bitstream = binaryToNrz(bits)
                frame.time = tt
                transmitter.pushBurst(frame)
                tt += 3
            time.sleep(0.01)

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://127.0.0.1:%i" % PORT)

    threading.Thread(target=send).start()

    while True:
        n_requested = int.from_bytes(socket.recv(), "little")
        data = transmitter.readSamples(n_requested).astype(numpy.int8).tobytes()
        socket.send(data)
        print(n_requested, len(data))
        time.sleep(len(data) / 300 * 0.5)