import sys
from .simulation.performance import plot_detection, plot_fec
from .tests.radio import generate



if len(sys.argv) > 1:
    opts = sys.argv[1:]
    if opts[0] == "plot":
        if opts[1] == "fec":
            plot_fec()
        elif opts[1] == "sync":
            plot_detection()
    elif opts[0] == "radio":
        generate()
