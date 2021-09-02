# import time
# import math
# from pylab import *
# import watchdog
# from psp.Pv import Pv
# import sys
# import random  # random number generator for secondary calibration
# from scipy.optimize import leastsq # for secondary calibration
# from femtoconfig import Config

class Ring(object):
    """Simple ring buffer. Extracted from original code."""

    def __init__(self, sz=12):  # sz is size of ring
        self.sz = sz  # hold size of ring
        self.a = array(range(sz))
        self.a = self.a * 0.0  # create an array of zeros
        self.ptr = -1 # points to last data, start negative
        self.full = False # set to true when the ring is full
        
    def add_element(self, x):  # adds element to ring
        self.ptr = mod(self.ptr+1,self.sz)        
        self.a[self.ptr] = x # set this element
        if self.ptr == 7:
            self.full = True

    def get_last_element(self):
        return self.a[self.ptr]       
        
    def get_array(self):
        return self.a