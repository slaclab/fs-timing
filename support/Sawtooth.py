import time
import math
import sys

import numpy as np

class Sawtooth(object):
    """ A description of a sawtooth function.
    
    Utility function for initializing and working with a sawtooth function as
    part of the calibration logic for the laser locker. Generates a sawtooth
    waveform and a vector of OK / notok points for where the fit should be
    good. Separated from monolithic OG code.
    
    """
    
    def __init__(self, t0, t_trig, delay, offset, period):
        """ Generate sawtooth.

        Generates a sawtooth based on and used with the Gen 1 (SIM-based)
        calibration procedure used on Vitara and similar lasers. In general
        unit-less, values here are typically in ns. If you work through the
        math, you'll see this does make a sawtooth, but it's a bit of a
        roundabout way to do it as opposed to say, using Scipy.signals

        Arguments: 
            t0 : an array of inputs that represent the phase shift time
            t_trig : the EVR trigger time
            delay : the cable length after the trigger 
            offset : the delay from the photodiode to the time interval counter
        """
        
        trig_out = t_trig + delay
        laser_t0 = t0 + offset
        tx = trig_out - laser_t0
        nlaser = np.ceil(tx / period)
        self.t = t0 + offset + nlaser * period
        tr = self.t - trig_out
        self.r = (0.5 + np.copysign(.5, tr - 0.2 * period)) * (0.5 + np.copysign(.5, .8 * period - tr))
