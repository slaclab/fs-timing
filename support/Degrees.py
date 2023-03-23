class degrees_s():
    """Utility class for handling conversion between numerical systems.
    
    Currently, the code uses the same legacy pvs which include S-Band in their
    names and descriptions. It is important to remember that these are actually
    scaled to the desired frequency which is set in the configuration files.

    This frequency is determined per installation, typically based on what makes
    the most sense for the non-expert user. For an normal conducting machine on
    the accelerator side, 
    """

    def __init__(self, P,freq):
        """ Initialize a degrees conversion opject with PV assignments and conversion.

        Arguments:
        P -- the PV maintenace object
        freq -- the fundamental reference frequency chosen for a given system
        """

        self.P = P
        self.freq = freq # in GHz
        self.last_time = self.P.get('time') # last time entered in contol
        self.last_deg = self.P.get('deg_Sband') # last degrees sband
        self.last_ns_offset = self.P.get('ns_offset')
        self.last_deg_offset = self.P.get('deg_offset')
        
    def run(self):
        """ Check which changed last. NS given priority.

        This function compares current values for target time and offset time
        (converted to degrees) against their previous values, and which ever has
        changed 'last' (ie. likely only one has changed since the last record
        update), and updates the others based on that value. In the case that
        there is a collision, target time takes precedence per the if/else
        structure.
        """
        ns = self.P.get('time')
        deg = self.P.get('deg_Sband')
        ns_offset = self.P.get('ns_offset')
        deg_offset = self.P.get('deg_offset')
        if ns != self.last_time or ns_offset != self.last_ns_offset: # nanoseconds have changed
            deg_new = -1.0*(ns - ns_offset) * self.freq * 360 - deg_offset
            self.last_time = ns
            self.last_ns_offset = ns_offset
            self.last_deg = deg_new
            self.P.put('deg_Sband', deg_new) #write the degrees back
           
        elif deg != self.last_deg or deg_offset != self.last_deg_offset:  #changed degrees
            ns_new = -1.0*(deg + deg_offset)/(self.freq * 360) + ns_offset
            self.last_time = ns_new
            self.last_deg = deg
            self.last_deg_offset = deg_offset
            self.P.put('time', ns_new) 

        else:
            pass
