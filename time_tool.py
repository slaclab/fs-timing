#time_tool.py
import time
from pylab import *
import watchdog
from psp.Pv import Pv
import sys
import random  # random number generator for secondary calibration
from scipy.optimize import leastsq # for secondary calibration
class time_tool():
    def __init__ (self, sys='NULL'): 

        if sys == 'XPP':  # set up xpp system
            print 'starting XPP'''
            self.delay = 0.1 # 1 second delay
            pvname = 'XPP:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS3:VIT:matlab:'  # start of matlab names
            stagename = 'XPP:LAS:MMN:16'  # delay stage for time tool
            ipmname = 'XPP:SB2:BMMON:SUM' # intensity profile monitor PV

        elif sys == 'CXI':  # set up cxi system
            print 'starting CXI'''
            self.delay = 0.1 # 1 second delay
            pvname = 'CXI:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS5:VIT:matlab:'  # start of matlab names
            stagename = 'CXI:LAS:MMN:04'  # delay stage for time tool
            ipmname = 'CXI:DG2:BMMON:SUM' # intensity profile monitor PV
                    
        elif sys == 'XCS':  # set up xcs system
            print 'starting XCS'
            self.delay = 0.1 # 1 second delay
            pvname = 'XCS:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS4:VIT:matlab:'  # start of matlab names
            stagename = 'XCS:LAS:MMN:01'  # delay stage for time tool
            ipmname = 'XCS:SB1:BMMON:SUM' # intensity profile monitor PV

        elif sys == 'FS11': # set up for new bay 1 laser
            print 'starting FS11'
            self.delay = 0.1
            pvname = 'XPP:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS11:VIT:matlab:'  # start of matlab names
            stagename = 'XPP:LAS:MMN:16'  # delay stage for time tool
            ipmname = 'XPP:SB2:BMMON:SUM' # intensity profile monitor PV

        elif sys == 'FS14':  # set up FS14 system
            print('starting FS14 pcav2ttdrift')
            self.delay = 0.1 # 1 second delay
            pvname = 'TMO:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS14:VIT:matlab:'  # start of matlab names
            stagename = 'LM1K4:COM_MP2_DLY1'  # delay stage for time tool
            ipmname = 'EM2K0:XGMD:HPS:milliJoulesPerPulse' # intensity profile monitor PV

        else:
            print sys + '  not found, exiting'
            exit()
        
        
        self.ttpv = Pv(pvname)
        self.ttpv.connect(timeout=1.0) # connect to pv
        self.stagepv = Pv(stagename)
        self.stagepv.connect(timeout=1.0)
	self.ipmpv = Pv(ipmname)
	self.ipmpv.connect(timeout=1.0)
        self.matlab_pv = dict()  # will hold list of pvs
        self.values = dict() # will hold the numbers from the time tool
        self.limits = dict() # will hold limits from matlab pvs
        self.old_values = dict() # will hold the old values read from matlab
        self.nm = ['watchdog', 'pix', 'fs', 'amp', 'amp_second', 'ref', 'FWHM', 'Stage', 'ipm','dcsignal'] #list of internal names
        for n in range(0,10): # loop over pvs to create
            base = matlab_prefix + str(n+matlab_start) # base pv name
            self.matlab_pv[self.nm[n]] = [Pv(base), Pv(base+'.LOW'), Pv(base+'.HIGH'), Pv(base+'.DESC')]  # pv with normal, low and high
            for x in range(0,4):
                self.matlab_pv[self.nm[n]][x].connect(timeout=1.0)  # connnect to all the various VPs.     
            for x in range(0,3):
		self.matlab_pv[self.nm[n]][x].get(ctrl=True, timeout=1.0)
            self.matlab_pv[self.nm[n]][3].put(value = self.nm[n], timeout = 1.0)
        self.W = watchdog.watchdog(self.matlab_pv[self.nm[0]][0]) # initialize watcdog   
        
    def read_write(self):   
         self.ttpv.get(ctrl=True, timeout=1.0) # get TT array data
         self.stagepv.get(ctrl=True, timeout=1.0) # get TT stage position
         self.ipmpv.get(ctrl=True, timeout=1.0) # get intensity profile
         for n in range(1,9):
             self.old_values[self.nm[n]] = self.matlab_pv[self.nm[n]][0].value # old PV values
             #self.limits[self.nm[n]] = [self.matlab_pv[self.nm[n]][1].value, self.matlab_pv[self.nm[n]][2].value] # limits
	     if n in range (1,6):
                 self.matlab_pv[self.nm[n]][0].put(value = self.ttpv.value[n-1], timeout = 1.0)  # write to matlab PVs 
             for x in range(0,3):
                 self.matlab_pv[self.nm[n]][x].get(ctrl=True, timeout=1.0)  # get all the matlab pvs
         self.matlab_pv[self.nm[7]][0].put(value = self.stagepv.value, timeout = 1.0)  # read stage position
         self.matlab_pv[self.nm[8]][0].put(value = self.ipmpv.value, timeout = 1.0) # read/write intensity profile
         #print self.ttpv.value
         #print 'stage position' # TEMP
         #print self.stagepv.value # TEMP
         #print 'intensity profile sum'
         #print self.ipmpv.value

         # need to decide whether to output to the drift correction signal
         # 1. IPM must be in range
	 if ( self.ipmpv.value > self.matlab_pv['ipm'][1].value ) and ( self.ipmpv.value < self.matlab_pv['ipm'][2].value ):
             #print 'intensity profile good'
             # 2. amp must be in range
             if ( self.matlab_pv['amp'][0].value > self.matlab_pv['amp'][1].value ) and ( self.matlab_pv['amp'][0].value < self.matlab_pv['amp'][2].value ):
                 #print 'TT edge fit good'
                 # 3. pix must be different from last pix, and stage must not be moving
                 if ( self.matlab_pv['pix'][0].value <> self.old_values['pix'] ) and ( self.matlab_pv['Stage'][0].value == self.old_values['Stage'] ):
                     #print 'Data is fresh. New pix value:'
                     #print self.matlab_pv['pix'][0].value
                     # at this point, know that data is good and need to move it over to the drift correction algo
                     self.matlab_pv['dcsignal'][0].put(value = self.matlab_pv['pix'][0].value, timeout = 1.0)
                 #else:
                     #print 'Data is stale or stage is moving'
                     #print self.old_values['pix']
                     #print self.matlab_pv['pix'][0].value
             #else:
                 #print 'TT edge fit bad'
         #else:
             #print 'intensity profile bad'


def run():  # just a loop to keep recording         
    if len(sys.argv) < 2:
        T = time_tool()  # initialize
    else:
        T = time_tool(sys.argv[1])
    while T.W.error == 0:
        T.W.check() # check / update watchdog counter
        pause(T.delay)
        try:
            T.read_write()  # collects the data 
        except:
            del T
            print 'crashed, restarting'
            T = time_tool() # create again
            if T.W.error:
                return        
    pass  

if __name__ == "__main__":
   run()
