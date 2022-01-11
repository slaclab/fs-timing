class error_output():
    ''' Utility class for logging error output within Epics and local debugging.'''
    def __init__(self, pv, epicsLogLvl=0,localLogLvl=0): # writes to this string pv (already connected)
        self.pv = pv  # just to keep it here
        self.pv.put(value= 'OK', timeout=1.0)
        self.maxlen = 25 # maxumum error string length
        self.localLogLvl = localLogLvl
        self.epicsLogLvl = epicsLogLvl
  
    def write_error(self, error):
        print(error)
        if error:
            n = len(error['value'])
            if error['lvl'] >= self.localLogLvl:
                print(error['value'])
            if error['lvl'] >= self.epicsLogLvl:
                if n > self.maxlen:
                    error['value'] = error['value'][0:self.maxlen]
                self.pv.put(value = error['value'], timeout = 1.0)
        
