class TimeIntervalCounter(object):
    """The Time Interval Counter class reads interval counter data, gets raw or
    average as needed."""
    # def __init__(self):
    #     pass

    # class time_interval_counter():  # reads interval counter data, gets raw or average as needed
    def __init__(self, P):
        self.scale = 1e9 # scale relative to nanoseconds
        self.P = P
        self.good = 1 
        self.rt = ring() # create a ring buffer to hold data
        self.rt.add_element(self.P.get('counter')) # read first counter value to initialize array
        self.rj = ring() # ring to hold jitter data
        self.rj.add_element(self.P.get('counter_jitter'))
        self.range = 0 # range of data
    def get_time(self):
        self.good = 0  # assume bad unless we fall through all the traps
        self.range = 0; # until we overwrite
        tol = self.P.get('counter_jitter_high')
        tmin = self.P.get('counter_low')
        tmax = self.P.get('counter_high')
        time = self.P.get('counter')  # read counter time
        if time == self.rt.get_last_element: # no new data
            return 0 # no new data
        if (time > tmax) or (time < tmin):
            return 0 # data out of range
        jit = self.P.get('counter_jitter')
        if jit > tol:
            return 0  # jitter too high
        # if we got here, we have a good reading
        self.rt.add_element(time) # add time to ring
        self.rj.add_element(jit)  # add jitter to ring
        self.good = 1
        if self.rt.full:
            self.range = self.scale * (max(self.rt.get_array()) - min(self.rt.get_array()))  # range of measurements
        else:
            self.range = 0  # don't have a full buffer yet
        return time * self.scale