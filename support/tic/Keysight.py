#from .TimeIntervalCounter import TimeIntervalCounter
import numpy as np
import pdb
from ..Ring import Ring as ring

class Keysight(object):
    """ Combined function time interval and frequency counter.
    
    Instance of the time interval counter object that supports the 53220 and
    53230 models from Keysight, which do not have measurement statistics
    functions. As a result, some additional data aggregation is needed at the
    software level."""
	
    def __init__(self, P):
        """ Initialze counter object using PVS reference.
        
        Specific initialization that uses internal deque (ring) to calculate jitter.
        
        Arguments:
            P : PVS object
        """
        
        self.scale = 1e9 # scale relative to nanoseconds
        self.P = P
        self.good = 1 
        self.rt = ring() # create a ring buffer to hold data
        self.rt.add_element(self.P.get('counter')) # read first counter value to initialize array
        self.rj = ring() # ring to hold jitter data
        self.update_jitter()
        self.range = 0 # range of data
        
    def get_time(self):
        """ return time from counter."""
        #pdb.set_trace()
        self.good = 0  # assume bad unless we fall through all the traps
        self.range = 0; # until we overwrite
        #tol = self.P.get('counter_jitter_high')
        tol = 50000
        tmin = self.P.get('counter_low')
        tmax = self.P.get('counter_high')
        time = self.P.get('counter')  # read counter time
        self.update_jitter()
        if time == self.rt.get_last_element(): # no new data
            return 0 # no new data
        if (time > tmax) or (time < tmin):
            return 0 # data out of range
        if self.rj.get_last_element() > tol:
            return 0  # jitter too high
        # if we got here, we have a good reading
        self.rt.add_element(time) # add time to ring
        #self.rj.add_element(jit)  # add jitter to ring
        self.good = 1
        if self.rt.full:
            self.range = self.scale * (max(self.rt.get_array()) - min(self.rt.get_array()))  # range of measurements
        else:
            self.range = 0  # don't have a full buffer yet
        return time * self.scale
        
    def update_jitter(self):
        """ Function to update the jitter in the measurements based just on the standard deviation of the buffer."""
        #pdb.set_trace()
        self.rj.add_element(np.std(self.rt.get_array()))
