import RsWaveform
import datetime



def generateIqTar(signal, sample_rate, title, output_path):
    iqtar = RsWaveform.IqTar()
    iqtar.data[0] = signal
    iqtar.meta[0] = {
        'clock': float(sample_rate),
        'scalingfactor': 1.0,
        'datatype': 'float32',
        'format': 'complex',
        'name': title,
        "datetime": datetime.datetime.now(),
    }
    iqtar.save(output_path)



if __name__ == "__main__":
    from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator
    from pyomslpwan.src.uplink.pdu import UplinkFrame
    from pyomslpwan.src.structs import *
    from pyomslpwan.lib.channel import GmskModulator
    from pyomslpwan.lib.coding import binaryToNrz

    seed = 0
    burst_mode = BURST_MODE_SINGLE_BURST
    burst_type = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3
    size = 255
    bt = 0.5
    span = 3
    sps = 8
    baud = 125000
    title = "GMSK_BT-0.5_OMS-LPWAN"

    print("Generating ...")

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

    path = datetime.datetime.now().isoformat() + "-" + title + ".iq.tar"
    samp_rate = baud * sps
    generateIqTar(modulated, samp_rate, title, path)
    print("File successfully generated")

    iqtar = RsWaveform.IqTar(file=path)
    data = iqtar.data[0]
    assert (data == modulated).all()
    assert iqtar.meta[0]["datatype"] == "float32"
    assert iqtar.meta[0]["format"] == "complex"
    assert iqtar.meta[0]["clock"] == samp_rate
    assert iqtar.meta[0]["scalingfactor"] == 1.0
    print("File successfully read")