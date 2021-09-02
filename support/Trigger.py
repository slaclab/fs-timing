class Trigger(object):
    """The Trigger class encapsulates functions for converting time values
    between units."""

    def __init__ (self, P):  # P is a pv list that includes trigger scaling information
        self.P = P
        if self.P.trig_in_ticks:
            self.scale =1000.0/119.0  # 119MHz, 8 ns ticks 
        else:
            self.scale = 1 # trigger is in ns units
        self.time = self.scale * self.P.get('laser_trigger')    
   
    def get_ns(self):
        tmp = self.P.get('laser_trigger')
        self.time = self.scale * tmp
        return self.time
        
    def set_ns(self,t):
        self.time = t/self.scale
        #self.P.pvlist['laser_trigger'].put(self.time)
        self.P.put('laser_trigger', self.time)