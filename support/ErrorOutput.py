""" This class defines a utility object for managing the reporting of error
messages generated elsewhere in the code. It is configured upon creation to log
messages to one or both of the local process output and an epics error pv (a
char string). It uses a sliding scale where 0 == silent, 1 ~= sparse, 2 ==
debugging.

Author: J. May"""

class error_output():
    ''' Utility class for logging error output within Epics and local debugging'''
    def __init__(self, pv, epicsLogLvl=0,localLogLvl=0): # writes to this string pv (already connected)
        self.pv = pv  # Local connection to error reporting pv
        self.pv.put(value= 'OK', timeout=1.0)
        self.maxlen = 25 # maxumum error string length
        # The following set how much reporting to do either locally or to epics
        # 0: no reporting (silent mode); > 0: sliding scale of severity. Most of
        # the related code here does not go above 2
        self.localLogLvl = localLogLvl
        self.epicsLogLvl = epicsLogLvl
  
    def write_error(self, error):
        """ Write the error requested to the terminal and the epics error pv
        depending on the configured severity level selection.
        """
        if error:
            n = len(error['value'])
            if error['lvl'] <= self.localLogLvl:
                print(error['value'])
            if error['lvl'] <= self.epicsLogLvl:
                if n > self.maxlen:
                    error['value'] = error['value'][0:self.maxlen]
                self.pv.put(value = error['value'], timeout = 1.0)
        
