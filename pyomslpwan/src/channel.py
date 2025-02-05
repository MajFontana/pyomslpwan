import numpy
import bitstring

from pyomslpwan.lib.channel import *
from pyomslpwan.src.structs import *
from pyomslpwan.src.coding import *
from pyomslpwan.lib.coding import toNrzArray, binaryToNrz



class UplinkMskModulator(MskModulator):

    def __init__(self):
        super().__init__(initial_phase=1j, zero_clockwise=True)



class UplinkPrecodedMskDemodulator(PrecodedMskDemodulator):

    def __init__(self):
        super().__init__(initial_phase=1j, zero_clockwise=True)



class DownlinkSyncwordCorrelator(Correlator):

    def __init__(self):
        syncword_size = BurstModeDownlink().syncword.getSize()
        syncword = binaryToNrz(numpy.array(bitstring.BitArray(uint=BurstModeDownlink.SYNCWORD, length=syncword_size)))
        super().__init__(pattern=syncword)



class UplinkSyncwordCorrelator(Correlator):

    def __init__(self):
        syncword_size = BurstModeUplink().syncword.getSize()
        syncword = UplinkMskModulator().modulate(Precoder().encode(numpy.array(bitstring.BitArray(uint=BurstModeUplink.SYNCWORD, length=syncword_size))))
        super().__init__(pattern=syncword)



class UplinkMidambleCorrelator(Correlator):

    def __init__(self):
        midamble_size = BurstModeUplink().midamble.getSize()
        midamble = UplinkMskModulator().modulate(Precoder().encode(numpy.array(bitstring.BitArray(uint=BurstModeUplink.MIDAMBLE, length=midamble_size))))
        super().__init__(pattern=midamble)



class UplinkSyncwordSynchronizer(SyncwordSynchronizer):
    def __init__(self, threshold):
        syncword_size = BurstModeUplink().syncword.getSize()
        syncword = Precoder().encode(numpy.array(bitstring.BitArray(uint=BurstModeUplink.SYNCWORD, length=syncword_size)))
        syncword_mod = UplinkMskModulator().modulate(syncword)
        #syncword_mod = binaryToNrz(syncword)
        super().__init__(syncword=syncword_mod, syncword_offset=0, threshold=threshold)



class UplinkMidambleSynchronizer(SyncwordSynchronizer):
    def __init__(self, threshold):
        syncword_size = BurstModeUplink().syncword.getSize()
        coded_length_size = BurstModeUplink().coded_length.getSize()
        max_data_a_size = 384 * 8

        midamble_pos = syncword_size + coded_length_size + max_data_a_size
        midamble_size = BurstModeUplink().midamble.getSize()
        syncword = Precoder().encode(numpy.array(bitstring.BitArray(uint=BurstModeUplink.MIDAMBLE, length=midamble_size)))
        syncword_mod = UplinkMskModulator().modulate(syncword)
        #syncword_mod = binaryToNrz(syncword)
        super().__init__(syncword=syncword_mod, syncword_offset=midamble_pos, threshold=threshold)



class DownlinkSyncwordSynchronizer(SyncwordSynchronizer):
    def __init__(self, threshold):
        syncword_size = BurstModeDownlink().syncword.getSize()
        syncword = toNrzArray(numpy.array(bitstring.BitArray(uint=BurstModeDownlink.SYNCWORD, length=syncword_size)))
        super().__init__(syncword=syncword, syncword_offset=0, threshold=threshold)