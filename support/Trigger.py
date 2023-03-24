""" The Trigger object encapsulates fetching parameters for an event system
trigger, handling unit conversions. Most of the systems now all use EVR/TPR in
ns, and so the ticks functionality is no longer needed, but is included for
backwards compatibility.

Justin May
"""

class Trigger(object):
    """ A trigger reference

    The Trigger class encapsulates functions for converting time values
    between units.
    """

    def __init__ (self, P):  
        """ Initialize a trigger connection based on the provided PV.
        
        Arguments:
            P : PV object
        """
        
        self.P = P
        if self.P.config.trig_in_ticks:
            self.scale =1000.0/119.0  # 119MHz, 8 ns ticks; support for EVR systems
        else:
            self.scale = 1 # trigger is in ns units, covers TPR systems
        self.time = self.scale * self.P.get('laser_trigger')    
   
    def get_ns(self):
        """ Retrieve TDES."""
        tmp = self.P.get('laser_trigger')
        self.time = self.scale * tmp
        return self.time
        
    def set_ns(self,t):
        """ Set TDES.
        
        Arguments:
            t : trigger time to set
        """
        
        self.time = t/self.scale
        #self.P.pvlist['laser_trigger'].put(self.time)
        self.P.put('laser_trigger', self.time)

    def get_width(self):
        """ Retrieve TWID."""
        return self.P.get('laser_trigger_width')

    def set_width(self,wid):
        """ Set TWID.
        
        Arguments:
            wid : trigger width to set
        """

        self.P.put('laser_trigger_width', wid)