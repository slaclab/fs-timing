class error_output():
    ''' Utility class for logging error output within Epics.'''
    def __init__(self, pv): # writes to this string pv (already connected)
        self.pv = pv  # just to keep it here
        self.pv.put(value= 'OK', timeout=1.0)
        self.maxlen = 25 # maxumum error string length
  
    def write_error(self, txt):
        n = len(txt)
        if n > self.maxlen:
            txt = txt[0:self.maxlen]
        self.pv.put(value = txt, timeout = 1.0)