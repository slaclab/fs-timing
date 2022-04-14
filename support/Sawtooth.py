import time
import math
import numpy as np
# from pylab import *
# import watchdog
# from psp.Pv import Pv
import sys
# import random  # random number generator for secondary calibration
# from scipy.optimize import leastsq # for secondary calibration

class Sawtooth(object):
    """Utility function for initializing and working with a sawtooth function as
    part of the calibration logic for the laser locker. Generates a sawtooth
    waveform and a vector of OK / notok points for where the fit should be
    good. Separated from monolithic OG code."""
    
    def __init__(self, t0, t_trig, delay, offset, period):
        """ 
        t0 is an array of inputs that represent the phase shift time
        t_trig is the EVR trigger time
        delay is the cable length after the trigger
        offset is the dealay from the photodiode to the time interval counter
        """
        trig_out = t_trig + delay
        laser_t0 = t0 + offset
        tx = trig_out - laser_t0
        nlaser = np.ceil(tx / period)
        self.t = t0 + offset + nlaser * period
        tr = self.t - trig_out
        self.r = (0.5 + np.copysign(.5, tr - 0.2 * period)) * (0.5 + np.copysign(.5, .8 * period - tr))
