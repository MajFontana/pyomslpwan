import numpy



def realNoise(dev, size):
    return numpy.random.normal(0, dev, size)



def complexNoise(dev, size):
    return numpy.random.normal(0, dev / 2, (size, 2)).view(numpy.complex128)[:, 0]



def noiseDeviation(eb_n0):
    eb_n0_lin = 10 ** (eb_n0 / 10)
    return numpy.sqrt(1 / (2 * eb_n0_lin))