import numpy
import math

from pyomslpwan.lib.channel import IqFrequencyDemodulator



class Slicer:

    def decision(self, x):
        return x > 0

    def map(self, b):
        return b * 2 - 1



class Ted:

    def __init__(self, slicer):
        self.inputs = [0, 0]
        self.decision = [0, 0]
        self.error = 0
        self.slicer = slicer
    
    def input(self, x):
        self.inputs.insert(0, x)
        self.inputs.pop(-1)
        self.decision.insert(0, self.slicer.map(self.slicer.decision(x)))
        self.decision.pop(-1)
        self.error = self.decision[1] * self.inputs[0] - self.decision[0] * self.inputs[1]
    
    def clear(self):
        self.inputs = [0, 0]
        self.decision = [0, 0]
        self.error = 0



class Clock:

    def __init__(self, loop_bw, max_period, min_period, nominal_period, damping, ted_gain):
        self.nominal_period = nominal_period

        self.avg_period = nominal_period
        self.min_avg_period = min_period
        self.max_avg_period = max_period
        self.inst_period = nominal_period
        self.phase = 0
        self.zeta = damping
        self.omega_n_norm = loop_bw
        self.ted_gain = ted_gain

        omega_n_T = self.omega_n_norm
        zeta_omega_n_T = self.zeta * omega_n_T
        k0 = 2 / self.ted_gain
        k1 = math.exp(-zeta_omega_n_T)
        sinh_zeta_omega_n_T = math.sinh(zeta_omega_n_T)

        if self.zeta > 1:
            omega_d_T = omega_n_T * math.sqrt(self.zeta * self.zeta - 1)
            cosx_omega_d_T = math.cosh(omega_d_T)
        elif self.zeta == 1:
            omega_d_T = 0
            cosx_omega_d_T = 1
        else:
            omega_d_T = omega_n_T * math.sqrt(1 - self.zeta * self.zeta)
            cosx_omega_d_T = math.cos(omega_d_T)

        self.alpha = k0 * k1 * sinh_zeta_omega_n_T
        self.beta = k0 * (1 - k1 * (sinh_zeta_omega_n_T + cosx_omega_d_T))

    def advance_loop(self, error):
        self.avg_period = self.avg_period + self.beta * error
        self.avg_period = max(min(self.avg_period, self.max_avg_period), self.min_avg_period)
        self.inst_period = self.avg_period + self.alpha * error
        if self.inst_period <= 0:
            self.inst_period = self.avg_period
        self.phase += self.inst_period
        limit = self.avg_period / 2
        self.phase = self.phase % math.copysign(limit, self.phase)
    
    def clear(self):
        self.phase = 0
        self.avg_period = self.nominal_period
        self.inst_period = self.nominal_period



class InterpolatingResampler:

    def __init__(self):
        self.phase = 0
        self.phase_n = 0
        self.phase_wrapped = 0

        from interpolator_taps import taps, NTAPS, NSTEPS
        self.taps = taps
        self.NTAPS = NTAPS
        self.NSTEPS = NSTEPS

        self.filters = []
        for i in range(NSTEPS + 1):
            t = numpy.array(self.taps[i])
            self.filters.append(t)
        
        self.ntaps = NTAPS

    def interpolate(self, input, mu):
        imu = round(mu * self.NSTEPS)
        # TODO: mu check
        r = numpy.dot(self.filters[imu], input[:self.NTAPS])
        return r

    def next_phase(self, increment):
        phase = self.phase_wrapped + increment
        n = math.floor(phase)
        phase_wrapped = phase - n
        phase_n = int(n)
        return phase, phase_n, phase_wrapped

    def advance_phase(self, increment):
        self.phase, self.phase_n, self.phase_wrapped = self.next_phase(increment)
    
    def sync_reset(self, phase):
        self.phase = phase
        n = math.floor(self.phase)
        self.phase_wrapped = self.phase - n
        self.phase_n = n
    
    def clear(self):
        self.phase = 0
        self.phase_n = 0
        self.phase_wrapped = 0



class SymbolSync:

    def __init__(self, sps, loop_bw, damping_factor, ted_gain, max_deviation):
        self.ted = Ted(Slicer())
        self.clock = Clock(loop_bw, sps + max_deviation, sps - max_deviation, sps, damping_factor, ted_gain)
        self.interp = InterpolatingResampler()
        self.synced_interp = InterpolatingResampler()

        self.interp.sync_reset(sps)
        self.synced_interp.sync_reset(sps)

        self.filter_delay = (self.interp.ntaps + 1) / 2

    def work(self, signal, input_items):
        ni = len(input_items) - self.interp.ntaps
        output_items = []
        synced = []
        ii = 0
        synced_ii = 0
        oo = 0
        while True:
            interp_output = self.interp.interpolate(input_items[ii:], self.interp.phase_wrapped)
            output_items.append(interp_output)
            synced_interp_output = self.synced_interp.interpolate(signal[synced_ii + 4:], self.synced_interp.phase_wrapped)
            synced.append(synced_interp_output)
            self.ted.input(interp_output)
            self.clock.advance_loop(self.ted.error)
            _, look_ahead_phase_n, _ = self.interp.next_phase(self.clock.inst_period)
            if ii + 4 + look_ahead_phase_n >= ni:
                # TODO: revert
                break
            self.interp.advance_phase(self.clock.inst_period)
            self.synced_interp.advance_phase(self.clock.inst_period)
            oo += 1
            ii += self.interp.phase_n
            synced_ii += self.synced_interp.phase_n
        return numpy.array(synced), numpy.array(output_items)
    
    def clear(self):
        self.ted.clear()
        self.clock.clear()
        self.interp.clear()
        self.synced_interp.clear()



class GfskDemod:

    def __init__(self, samples_per_symbol, gain_mu, omega_relative_limit, freq_error, sensitivity):
        omega = samples_per_symbol * (1 + freq_error)
        gain_omega = 0.25 * gain_mu * gain_mu
        damping = 1
        loop_bw = -math.log((gain_mu + gain_omega) / -2 + 1)
        max_dev = omega_relative_limit * samples_per_symbol
        sensitivity = sensitivity / samples_per_symbol

        self.fmdemod = IqFrequencyDemodulator(sensitivity)
        self.clock_recovery = SymbolSync(omega, loop_bw, damping, 1, max_dev)
        self.slicer = Slicer()

        self.sps = samples_per_symbol

    def demodulate(self, signal):
        demod = self.fmdemod.demodulate(signal)
        synced, synced_demod = self.clock_recovery.work(signal, demod)
        data = self.slicer.decision(synced_demod)
        return demod, synced, synced_demod, data
    
    def clear(self):
        self.clock_recovery.clear()



class GmskDemod(GfskDemod):

    def __init__(self, *args):
        sensitivity = numpy.pi / 2
        super().__init__(*args, sensitivity)