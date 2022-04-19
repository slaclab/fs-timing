import pdb

class degrees_s():
    '''Utility class for handling conversion between numerical systems.
    Currently, the code uses the same legacy pvs which include S-Band in their
    names and descriptions. It is important to remember that these are actually
    scaled to the desired frequency which is set in the configuration files.'''

    def __init__(self, P,freq):  #P has the list of PVs
        self.P = P
        #pdb.set_trace()
        self.freq = freq # in GHz
        self.last_time = self.P.get('time') # last time entered in contol
        self.last_deg = self.P.get('deg_Sband') # last degrees sband
        self.last_ns_offset = self.P.get('ns_offset')
        self.last_deg_offset = self.P.get('deg_offset')
        
    def run(self): # checks which changed last. NS given priority
        #pdb.set_trace()
        ns = self.P.get('time')
        deg = self.P.get('deg_Sband')
        ns_offset = self.P.get('ns_offset')
        deg_offset = self.P.get('deg_offset')
        if ns != self.last_time or ns_offset != self.last_ns_offset: # nanoseconds have changed
            deg_new = (ns - ns_offset) * self.freq * 360 - deg_offset
            self.last_time = ns
            self.last_ns_offset = ns_offset
            self.last_deg = deg_new
            self.P.put('deg_Sband', deg_new) #write the degrees back
           
        elif deg != self.last_deg or deg_offset != self.last_deg_offset:  #changed degrees
            ns_new = (deg + deg_offset)/(self.freq * 360) + ns_offset
            self.last_time = ns_new
            self.last_deg = deg
            self.last_deg_offset = deg_offset
            self.P.put('time', ns_new) 

        else:
            pass
