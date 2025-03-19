# OMS LPWAN frame generator and parser 

Bitstream generator and parser for OMS LPWAN frames, in progress toward a fully functional PHY transceiver. Implements burst mode only.

![Bit error rate of uplink multi-burst transmission](/pyomslpwan/docs/example-ber-uplink-multi-burst.png)

## Table of contents

* [Setup](#setup)
    * [With Nix](#with-nix)
    * [Without Nix](#without-nix)
    * [Installing pyomslpwan](#installing-pyomslpwan)
* [Testing](#testing)
* [Tools](#tools)
    * [Simulated BER and packet loss measurement](#simulated-ber-and-packet-loss-measurement)
    * [Generating Rohde & Schwarz IQ TAR files](#generating-rohde--schwarz-iq-tar-files)
* [Usage](#usage)
    * [Generating a frame](#generating-a-frame)
    * [Generating a 1 SPS MSK-modulated stream (simplified scheme used in graduate thesis)](#generating-a-1-sps-msk-modulated-stream-simplified-scheme-used-in-graduate-thesis)
    * [Generating a GMSK-modulated stream](#generating-a-gmsk-modulated-stream)
    * [Finding bursts (currently for uplink only)](#finding-bursts-currently-for-uplink-only)
    * [Demodulating and decoding a burst directly (currently for uplink only)](#demodulating-and-decoding-a-burst-directly-currently-for-uplink-only)
    * [Parsing a frame](#parsing-a-frame)
    * [Adding impairments](#adding-impairments)
* [Project structure](#project-structure)

## Setup

### With Nix

If you're using Nix, you can enter the development environment by running `nix develop` in the root directory. This will set up non-Python dependencies and also enter a venv (and create one if necessary).

> **Note:** If using Nix, you might need to add the following to the beginning of the script you're running for matplotlib to work:
```Python
import matplotlib
matplotlib.use("tkagg")
```

Proceed to [Installing pyomslpwan](#installing-pyomslpwan).

### Without Nix

> **Note:** The project does not currently require any special non-Python dependecies. Chances are they are already installed on your system by default.

Make sure you have Python installed and create a venv in the project root by running the following:

```bash
python -m venv .venv
```

Then, to enter the venv on Linux run
```bash
source .venv/bin/activate
```
On Windows run
```bat
.venv/bin/activate
```

Proceed to [Installing pyomslpwan](#installing-pyomslpwan).

### Installing pyomslpwan

Once in a venv, run the following in project root:

```bash
pip install --editable .
```

That should install pyomslpwan and all its dependencies into the venv. If the project is ever updated to depend on new Python packages, you need to run

```
pip install --upgrade .
```

> **Note:** If you're experiencing issues with importing from pyomslpwan, try installing pyomslpwan without `--editable`.
Doing so, however, you will have to update the package whenever a change is made to the source code.

## Testing

You can verify that pyomslpwan passes test vectors defined in the OMS LPWAN speicifcation by running

```bash
python -m unittest -v
```

## Tools

### Simulated BER and packet loss measurement

You can generate performance plots using the following scripts. Currently all simulation parameters
(like the number of trials, and the range of Eb/N0 values) are configured
through parameters in function calls at the bottom of the scripts.

> **Note:** For performance reasons these simulations currently do not use the consolidated generator and parser
classes from `pyomslpwan.src` (like `BurstModeUplinkGenerator` or `UplinkReceiver`), but instead use
more basic classes from `lib/` as well as separate implementations found in `lib/uplink/frame.py` and `lib/downlink/frame.py`. That requires care and attention when
updates are being made to the coding and decoding chains. For this reason these simulations also do not serve
as valid integration tests. For an integrated packet loss measurement look at `simulation/proga.py`.

#### Downlink

command | description
-|-
`python pyomslpwan/simulation/performance_downlink_detection.py` | Likelihood of a false negative and frequency of true positives when detecting the syncword with different thresholds
`python pyomslpwan/simulation/performance_downlink_fec_header.py` | Likelihood of error in decoded header
`python pyomslpwan/simulation/performance_downlink_fec_payload.py` | BER of decoded payload

#### Uplink

command | description
-|-
`python pyomslpwan/simulation/performance_uplink_detection.py` | Likelihood of a false negative and frequency of true positives when detecting the syncword with different thresholds. The same measurement is performed for the midamble
`python pyomslpwan/simulation/performance_uplink_fec_header.py` | Likelihood of error in decoded header
`python pyomslpwan/simulation/performance_uplink_fec_payload.py` | BER of decoded payload

### Generating Rohde & Schwarz IQ TAR files

An IQ TAR file containing a GMSK-modulated IQ stream of a randomized single-burst mode burst can be generated
by running the following command:

```bash
python pyomslpwan/simulation/rohde_schwarz_bitstream.py
```

The parameters of the burst and the random seed can currently be configured by
modifying the values of the variables in the script.

> **Note:** The file is created in the current working directory. In the example shown,
IQ TAR files are saved to project root. They are excluded from tracking in .gitignore.

## Usage

### Generating a frame

```Python
import numpy

from pyomslpwan.lib.coding import binaryToNrz
from pyomslpwan.src.uplink.frame import BurstModeUplinkGenerator
from pyomslpwan.src.uplink.pdu import UplinkFrame
from pyomslpwan.src.structs import BURST_MODE_SINGLE_BURST, BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3

def generateFrame(timing_input_value, payload, burst_mode, burst_type):
    frame = UplinkFrame()
    frame.coded_header.timing_input_value = timing_input_value
    frame.coded_header.burst_mode = burst_mode
    frame.coded_header.burst_type = burst_type
    frame.coded_payload.phy_payload = payload
    BurstModeUplinkGenerator().generateFrame(frame)
    return frame

PAYLOAD_SIZE = 255
BURST_MODE = BURST_MODE_SINGLE_BURST
BURST_TYPE = BURST_TYPE_UPLINK_SINGLE_BURST_FEC_RATE_1_3

timing_input_value = numpy.random.randint(0, 128)
payload = numpy.random.randint(0, 256, PAYLOAD_SIZE,  dtype=numpy.uint8).tobytes()

frame = generateFrame(timing_input_value, payload, BURST_MODE, BURST_TYPE)
burst = frame.uplink_0
bitstream = burst.bitstream # binary
nrz = binaryToNrz(bitstream) # NRZ (-1, +1)
```

### Generating a 1 SPS MSK-modulated stream (simplified scheme used in graduate thesis)
```Python
from pyomslpwan.src.channel import PrecodedMskModulator

iq_downsampled = PrecodedMskModulator().modulate(bitstream)
```

### Generating a GMSK-modulated stream

```Python
from pyomslpwan.lib.channel import GmskModulator

BT = 0.5
SPS = 16
L = 3

iq = GmskModulator(BT, L, SPS).modulate(bitstream, True)
```

### Finding bursts (currently for uplink only)

UplinkReceiver searches the IQ stream for both the syncword and the midamble using correlation, and attempts to demodulate and decode any discovered bursts.
If both correlators find a match, the bursts are duplicated. This is to be taken care of
in the upper layers.

> **Note:** With the assumption that the incoming samples are already **time- and frequency-aligned**,
UplinkReceiver performs coherent demodulation straight into the un-precoded form (as described in the OMS LPWAN specification) and thus requires **IQ samples at 1 SPS** as an input.
It is capable of correcting static phase offsets and phase ambiguity
with a data-aided (syncword) approach.

> **Note:** UplinkReceiver currently assumes MSK modulation and will not perform optimally for GMSK.

```Python
from pyomslpwan.src.uplink.stream import UplinkReceiver

SPS = 16

# UplinkReceiver does not perform synchronization or downsampling
iq_downsampled = iq[::SPS]
uplink_receiver = UplinkReceiver(syncword_threshold=0.5, midamble_threshold=0.3)
uplink_receiver.feed(iq_downsampled)
bursts = uplink_receiver.bursts
```

### Demodulating and decoding a burst directly (currently for uplink only)

Given an array of IQ samples perfectly sampled at 1 SPS, and provided that you already know
the position of the coded header within the array, you can demodulate and decode it as follows
(using the simplified coherent MSK demodulator mentioned in [Finding bursts](#finding-bursts-currently-for-uplink-only)):

```Python
from pyomslpwan.src.channel import UplinkPrecodedMskDemodulator
from pyomslpwan.src.uplink.stream import BitstreamParser

SPS = 16

# If the burst was generated with pyomslpwan, the index of the
# coded header can be looked up like this:
coded_header_index = frame.uplink_0.struct.getPosition(frame.uplink_0.struct.coded_header)

# UplinkReceiver does not perform synchronization or downsampling
iq_downsampled = iq[::SPS]
nrz = UplinkPrecodedMskDemodulator().demodulate(iq_downsampled)
# Returns an instance of pyomslpwan.src.uplink.pdu.UplinkBurst
burst = BitstreamParser().parseBitstream(nrz, coded_header_index)
```

### Parsing a frame

No proper implementation currently exists for grouping bursts into frames according to their
header parameters, time of arrival, and frequency channel. For simulation and testing
purposes the grouping is currently implemented using simplified criteria. For example,
multi-burst performance simulations compare received header parameters to known (transmitted)
parameters to measure what is effectively packet loss. An example of a simplified
parser is provided:

```Python
from pyomslpwan.src.structs import BURST_MODE_SINGLE_BURST, BURST_MODE_MULTI_BURST
from pyomslpwan.src.uplink.frame import BurstModeUplinkParser
from pyomslpwan.src.uplink.pdu import UplinkFrame

frame = UplinkFrame()
if bursts[0].coded_header.burst_mode == BURST_MODE_SINGLE_BURST:
    frame.uplink_0 = bursts[0]
elif bursts[0].coded_header.burst_mode == BURST_MODE_MULTI_BURST:
    frame.uplink_1, frame.uplink_2, frame.uplink_3 = bursts
uplink_parser.parseFrame(frame)

payload = frame.coded_payload.phy_payload
```

### Adding impairments

```Python
import numpy

from pyomslpwan.lib.channel import IqFrequencyModulator
from pyomslpwan.simulation.noise import noiseDeviation, complexNoise

SPS = 16
BAUD = 10e3 #125e3
SAMP_RATE = BAUD * SPS

# Taken from the OMS LPWAN specification, assuming no offset or drift
# at the receiver
MAX_OFFSET = 20e3
MAX_DRIFT = 200

def channel(iq, ebn0):
    impaired = iq

    # Add randomized padding to give some margin to the demodulator
    # and to better randomize the initial phases of any PLLs
    txlen = len(iq)
    padlen = int(txlen * 0.2)
    offset = int(padlen * numpy.random.uniform(0.2, 0.8))
    padded = numpy.zeros((txlen) + padlen, dtype=complex)
    padded[offset:offset + txlen] = impaired
    impaired = padded

    # Add a drifting frequency offset following a sine wave curve
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

impaired = channel(iq, -4)
```

## Project structure

pyomslpwan is a Python package. All relevant code is contained within `/pyomslpwan`. Following is the description of its internal structure:

path | description
-|-
`docs` | generated plots and graduate thesis
`main.py` | not very useful at the moment

### `lib/` - generally applicable functionality

path | description
-|-
`lib/channel.py` | signal processing techniques for modem
`lib/coding.py` | coding techniques
`lib/convolution.py` | numba optimized convolutional coding and viterbi decoding, use wrappers defined in `coding.py`
`lib/fields.py` | framework for working with protocol frames and fields
`lib/synchronization.py` | GNU Radio GMSK Demod block translated to Python, unused, will probably be removed

### `src/` - functionality specific to OMS LPWAN

path | description
-|-
`src/channel.py` | signal processing techniques required by OMS LPWAN (currently syncword / midamble correlation and synchronization, simple MSK modem for testing only)
`src/coding.py` | coding techniques defined in the OMS LPWAN specification (CommonFecEncodingScheme, CommonInterleavingScheme, Precoder, CRCs)
`src/structs.py` | frame structures and constants defined in the OMS LPWAN specification
`src/uplink`, `src/downlink` | OMS LPWAN frame generation and parsing implementations for uplink and donwlink
`src/uplink/frame.py`, `src/downlink/frame.py` | frame generation and parsing
`src/uplink/pdu.py`, `src/downlink/pdu.py` | objects for storing information during generation and parsing
`src/uplink/stream.py` | helper classes for extracting bursts from a contiuous stream of samples and generating a continuous stream from scheduled bursts (generation is a WIP, probably does not work at the moment)

### `tests/` - test code against the test vectors provided in the OMS LPWAN specification

path | description
-|-
`tests/radio.py` | GNU Radio interface test, will be removed
`tests/test_coding.py` | tests against FEC, interleaver and precoder test vectors
`tests/test_uplink.py`, `tests/test_downlink.py` | tests against full test vectors

### `simulation/` - experimental and measurement (BER, packet loss) simulations, everything not specified is either an experiment or old code

 path | description
-|-
`simulation/noise.py` | helper functions for generating noise
`simulation/plotting.py` | helper functions for plotting
`simulation/performance_downlink_detection.py`, `simulation/performance_uplink_detection.py` | isolated simulated measurement of detection probability
`simulation/performance_downlink_fec_header.py`, `simulation/performance_uplink_fec_header.py` | isolated simulated measurement of coded header recovery probability
`simulation/performance_dowwlink_payload_header.py`, `simulation/performance_uplink_payload_header.py` | isolated simulated measurement of coded payload BER
`simulation/rohde_schwarz_bitstream.py` | bitstream file generation for Rohde & Schwarz bitstream generators
`simulation/proga.py` | packet loss measurement (80/20) that includes baseband GMSK modulation and synchronization
`simulation/coarse_sync2.py` | latest synchronization experiment, succesfully implements FFT-based coarse frequency correction
|


