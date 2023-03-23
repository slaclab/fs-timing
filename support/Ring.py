""" This is a legacy implementation of a ring buffer, included for backwards
compatibility. A better implementation uses the deque object from the
collections built-in, and in fact deques are used elsewhere in the HLA.

Justin May
"""

import math

import numpy as np

class Ring(object):
    """Simple ring buffer."""

    def __init__(self, sz=12):
        """ Create a ring buffer with size
          
        Arguments:
        sz -- length of buffer
        """
        
        self.sz = sz  # hold size of ring
        self.a = np.array(range(sz))
        self.a = self.a * 0.0  # create an array of zeros
        self.ptr = -1 # points to last data, start negative
        self.full = False # set to true when the ring is full
        
    def add_element(self, x):
        """ adds element to ring.
        
        Arguments:
        x -- value to add
        """

        self.ptr = np.mod(self.ptr+1,self.sz)        
        self.a[self.ptr] = x # set this element
        if self.ptr == 7:
            self.full = True

    def get_last_element(self):
        """ Return last element in buffer."""
        return self.a[self.ptr]       
        
    def get_array(self):
        """ Return buffer."""
        return self.a