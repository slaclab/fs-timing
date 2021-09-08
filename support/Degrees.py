class degrees_s(): # manages time control in degrees S-band
    '''Utility class for handling conversion between numerical systems.'''
    # TODO: expand to include conversion between various time bases, in a way
    # that readily supports LCLS-2 numerology and timing systems as well.
    def __init__(self, P):  #P has the list of PVs
        self.P = P
        self.freq = 2.856  # in GHz
        self.last_time = self.P.get('time') # last time entered in contol
        self.last_deg = self.P.get('deg_Sband') # last degrees sband
        self.last_ns_offset = self.P.get('ns_offset')
        self.last_deg_offset = self.P.get('deg_offset')
        
    def run(self): # checks which changed last. NS given priority
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