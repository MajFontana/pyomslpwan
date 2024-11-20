import time
import numpy
import zmq
import threading

from pyomslpwan.src.uplink.stream import BurstModeUplinkTransmitter
from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator
from pyomslpwan.src.structs import *
from pyomslpwan.lib.coding import binaryToNrz



PORT = 12345



def generate():
    class Struct:
        pass

    generator = BurstModeUplinkGenerator()
    transmitter = BurstModeUplinkTransmitter(16000)

    def send():
        tt = 0
        while True:
            t = transmitter.time
            while tt < t + 0.2:
                frame = Struct()
                bits = generator.createSingleBurst(0, b"Hello world!", BURST_TYPE_DOWNLINK_SINGLE_BURST_FEC_RATE_7_8).getBitstream()
                frame.bitstream = binaryToNrz(bits)
                frame.time = tt
                transmitter.pushBurst(frame)
                tt += 0.1
            time.sleep(0.01)

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://127.0.0.1:%i" % PORT)

    threading.Thread(target=send).start()

    while True:
        n_requested = int.from_bytes(socket.recv(), "little")
        data = transmitter.readSamples(n_requested).astype(numpy.float32).tobytes()
        socket.send(data)
        print(n_requested, len(data))
        time.sleep(len(data) / 32000 * 2)

generate()