#pcav2ttdrift.py
""" Alt. version of drift compensation for laser lockers based on PCAVs.

This script adapts the structure of time_tool.py, adding to the time-tool logic
a box-car average of the pcav data to drive a feed-forward loop on the
lockers. This uses the same matlab pv that is defined in femto.py and
time_tool.py for drift compensation. It is possible that the desired drift
compensation approach should include both time tool data and pcav data, the
former being for fast corrections and the latter to account for the minute time
scale drifts that quickly move the laser outside of the time-tool window. In the
event both drift compensation values are needed, then both input hooks should be
set to True, and the drift average will be added to the time tool values that
pass the original time-tool tests.

This version of the code has been developed to work with new release on the laser feedback summary panel that is used on the photon side.

This was tested on 3/22/2021.

This is a Python 2 function.
"""
import time
from pylab import *
import watchdog # the local watchdog implementation used throughout the laser locker codebase
from psp.Pv import Pv
import sys
import random  # random number generator for secondary calibration
from scipy.optimize import leastsq # for secondary calibration
import argparse # adding for utility and parsing the toggle states for which system to use
from collections import deque
import pdb

class time_tool():
    def __init__ (self, sys='NULL',debug=False): 
        """ These definitions do not change from the original. Each will have a
            machine definition tag (used to instantiate a given system), and
            process delay (to set the relative frame rate of the code), a
            definition of which set of phase cavities to feedback on, the pvs
            for the corresponding xray/optical cross-correlator and the main
            notepad pvs used in processing the feedbacks."""
        if sys == 'XPP':  # set up xpp system ; JM(2/21) - technically deprecated
            print('starting XPP pcav2ttdrift')
            self.delay = 0.1 
            pvname = 'XPP:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS3:VIT:matlab:'  # start of matlab names
            stagename = 'XPP:LAS:MMN:16'  # delay stage for time tool
            ipmname = 'XPP:SB2:BMMON:SUM' # intensity profile monitor PV
            pixscale = 1.0e-6
            pcavset = "HXR"
        elif sys == 'CXI':  # set up cxi system
            print('starting CXI pcav2ttdrift')
            self.delay = 0.1 
            pvname = 'CXI:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS5:VIT:matlab:'  # start of matlab names
            stagename = 'CXI:LAS:MMN:04'  # delay stage for time tool
            ipmname = 'CXI:DG2:BMMON:SUM' # intensity profile monitor PV         
            pixscale = 1.0e-6
            pcavset = "HXR"
        elif sys == 'XCS':  # set up xcs system
            print('starting XCS pcav2ttdrift')
            self.delay = 0.1 
            pvname = 'XCS:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS4:VIT:matlab:'  # start of matlab names
            stagename = 'XCS:LAS:MMN:01'  # delay stage for time tool
            ipmname = 'XCS:SB1:BMMON:SUM' # intensity profile monitor PV
            pixscale = 1.0e-6
            pcavset = "HXR"
        elif sys == 'FS11':  # set up FS11 system
            print('starting FS11 pcav2ttdrift')
            self.delay = 0.1 
            pvname = 'XPP:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS11:VIT:matlab:'  # start of matlab names
            stagename = 'XPP:LAS:MMN:01'  # delay stage for time tool
            ipmname = 'XPP:SB2:BMMON:SUM' # intensity profile monitor PV
            pixscale = 1.0e-6
            pcavset = "HXR"
        elif sys == 'FS14':  # set up FS14 system
            print('starting FS14 pcav2ttdrift')
            self.delay = 0.1 
            pvname = 'TMO:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'LAS:FS14:VIT:matlab:'  # start of matlab names
            stagename = 'LM1K4:COM_MP2_DLY1'  # delay stage for time tool
            ipmname = 'EM2K0:XGMD:HPS:milliJoulesPerPulse' # intensity profile monitor PV
            pixscale = 2.0e-6
            pcavset = "SXR"
        elif sys == 'dev':
            print('starting pcav2ttdrift for testing with development proto ioc')
            self.delay = 0.1 
            pvname = 'DEV:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'DEV:VIT:matlab:'  # start of matlab names
            stagename = 'DEV:DELAYSTAGE'  # delay stage for time tool
            ipmname = 'DEV:PULSEENERGY' # intensity profile monitor PV
            pixscale = 2.0e-6
            pcavset = "SXR"
        else:
            print(sys + '  not found, exiting')
            exit()
        
        self.debug = debug
        """ This code orinally had command-line hooks that set which modes it
        used in feedback. These have been moved to control system inputs, what
        remains is the capability to run without actually issuing commands."""
        if debug:
            print("..running in debug mode")
        if pcavset == "HXR":
            pcavpv=['SIOC:UNDH:PT01:0:TIME0','SIOC:UNDH:PT01:0:TIME1'] # PVs for the output time for the two HXR, NC Linac cavities
        elif pcavset == "SXR":
            pcavpv=['SIOC:UNDS:PT01:0:TIME0','SIOC:UNDS:PT01:0:TIME1'] # PVs for the output time for the two SXR beamline, NC Linac cavities
        
        self.ttpv = Pv(pvname)
        self.ttpv.connect(timeout=1.0) # connect to pv
        self.stagepv = Pv(stagename)
        self.stagepv.connect(timeout=1.0)
        self.ipmpv = Pv(ipmname)
        self.ipmpv.connect(timeout=1.0)
        self.pcava=Pv(pcavpv[0]) # first of whichever phase cavities are used
        self.pcava.connect(timeout=1.0)
        self.pcavb=Pv(pcavpv[1]) # second phase cavity
        self.pcavb.connect(timeout=1.0)
        self.matlab_pv = dict()  # will hold list of pvs
        self.values = dict() # will hold the numbers from the time tool
        self.pcavdata = dict() # will hold values from the phase cavities
        self.pcavbuffer = deque() # the rolling buffer used to store the pcav values, to simply the process of averaging
        self.dccalc = 0 # initialize the timetool correction, but will be replaced with actual values
        self.pcavcalc=0 # initialize the phase cavity correction, but will be replaced with actual values
        self.limits = dict() # will hold limits from matlab pvs
        self.old_values = dict() # will hold the old values read from matlab
        # LIST OF INTERNAL PVS
        # 'watchdog' (20) - watchdog counter tracking operation of code; writing a 0 will stop code (restart in an auto-restart env)
        # 'pix' (21) - pixel (ie. time) value coming from ATM analysis
        # 'fs' (22) - probably the pixels converted to fs? (JM)
        # 'amp' (23) - JM: ATM amp? should then map to the TTAMP?
        # 'amp_second' (24) - JM: unsure
        # 'ref' (25) - JM: unused
        # 'FWHM' (26) - JM: unused
        # 'Stage' (27) - used to tell if the stage is moving
        # 'ipm' (28)
        # 'dcsignal' (29) - outbound correction signal
        # 'pcavcomp' (30) - JM: the internal pcav correction component
        # 'usett' (31) - enable/disable for using timetool
        # 'usepc' (32) - enable/disable for using phase cavities
        # 'reqZeroPcav' (33) - callback pv for zeroing the offsets from the phase cavities during operation
        # 'pcavoffset' (34) - offset value for phase cavity correction
        # 'pcavscale' (35) - scaling for the pcav correction
        self.nm = ['watchdog', 'pix', 'fs', 'amp', 'amp_second', 'ref', 'FWHM', 'Stage', 'ipm','dcsignal','pcavcomp','usett','usepc','reqZeroPcav','pcavoffset','pcavscale']
        for nn in range(0,self.nm.__len__()): # loop over pvs to create'
            base = matlab_prefix + str(nn+matlab_start) # base pv name
            self.matlab_pv[self.nm[nn]] = [Pv(base), Pv(base+'.LOW'), Pv(base+'.HIGH'), Pv(base+'.DESC')]  # pv with normal, low and high
            for x in range(0,4):
                self.matlab_pv[self.nm[nn]][x].connect(timeout=1.0)  # connnect to all the various PVs.     
            for x in range(0,3):
                self.matlab_pv[self.nm[nn]][x].get(ctrl=True, timeout=1.0)
            self.matlab_pv[self.nm[nn]][3].put(value = self.nm[nn], timeout = 1.0)
        self.usett = self.matlab_pv['usett'][0].get()
        self.usepcav = self.matlab_pv['usepc'][0].get()
        if self.usett:
            print("Using time tool drift compensation")
        if self.usepcav:
            print("Using phase cavity drift compensation")
        self.W = watchdog.watchdog(self.matlab_pv[self.nm[0]][0]) # initialize watcdog
        """ if self.usepcav: bug fix, moved this outside; means that the system
        will always connect to the pcavs, no matter the state. However, if
        running this code, by definition, you're dealing with an experiment
        laser, so the edge case is unimportant to optimize for. """
        self.pcava.get(ctrl=True, timeout=1.0)
        self.pcavb.get(ctrl=True, timeout=1.0)
        if self.matlab_pv['pcavoffset'][0].get() == 0: # consider 0 to be uninitialized
            self.matlab_pv['pcavoffset'][0].put(value=(self.pcava.value+self.pcavb.value)/2.0,timeout=2.0)
            self.matlab_pv['pcavoffset'][0].get()
        self.pcavinitial = self.matlab_pv['pcavoffset'][0].value
        self.old_values['pcavcomp'] = 0
        self.matlab_pv['pcavcomp'][0].put(value=0, timeout=1.0)
        if self.matlab_pv['pcavscale'][0].get() == 0: # consider 0 to be uninitialized
            self.matlab_pv['pcavscale'][0].put(value=-0.0008439,timeout=2.0)
            self.matlab_pv['pcavscale'][0].get()
        self.pcavscale = self.matlab_pv['pcavscale'][0].value
        
    def read_write(self):
        """ main feedback loop proc"""
        self.checkState()
        self.pcavscale = self.matlab_pv['pcavscale'][0].get()
        # first update the time tool and pcav values; this is synchronous, so making a poor attempt at lockstepping the two by separating reads and updates
        if self.usett:
            self.ttpv.get(ctrl=True, timeout=1.0) # get TT array data
            self.stagepv.get(ctrl=True, timeout=1.0) # get TT stage position
            self.ipmpv.get(ctrl=True, timeout=1.0) # get intensity profile
            for n in range(1,9):
                self.old_values[self.nm[n]] = self.matlab_pv[self.nm[n]][0].value # old PV values
                if n in range(1,6):
                    self.matlab_pv[self.nm[n]][0].put(value = self.ttpv.value[n-1], timeout = 1.0)  # write to matlab PVs 
                for x in range(0,3):
                    self.matlab_pv[self.nm[n]][x].get(ctrl=True, timeout=1.0)  # get all the matlab pvs
            self.matlab_pv[self.nm[7]][0].put(value = self.stagepv.value, timeout = 1.0)  # read stage position
            self.matlab_pv[self.nm[8]][0].put(value = self.ipmpv.value, timeout = 1.0) # read/write intensity profile
        if self.usepcav:
            self.pcava.get(ctrl=True, timeout=1.0)
            self.pcavb.get(ctrl=True, timeout=1.0)
            self.matlab_pv['pcavcomp'][0].get(ctrl=True, timeout=1.0)
            self.old_values['pcavcomp'] = self.matlab_pv['pcavcomp'][0].value # old PV values
        # now process the time tool logic to determine whether to include a correction
        if self.usett:
            if (self.ipmpv.value > self.matlab_pv['ipm'][1].value) and (self.ipmpv.value < self.matlab_pv['ipm'][2].value): # conditionals based on pv alarms
                if ( self.matlab_pv['amp'][0].value > self.matlab_pv['amp'][1].value ) and ( self.matlab_pv['amp'][0].value < self.matlab_pv['amp'][2].value ): # ...
                    if ( self.matlab_pv['pix'][0].value <> self.old_values['pix'] ) and ( self.matlab_pv['Stage'][0].value == self.old_values['Stage'] ): # is data new, is the stage not moving
                        self.dccalc = self.matlab_pv['pix'][0].value*pixscale # prep tt component
                        # ^ if !usett, but accumulate is on, the correction will stay where it last was, as opposed to zero'ing the tt component ("resetting the laser")
        """ .. and then the same for the pcavs; if you want to change the
        feedback to something more complex, this is the place to put it, either
        by doing more complex math, or changing the buffer length to adjust how
        much averaging the system does"""
        if self.usepcav:
            # at a buffer length of 600, this is a rolling average of around 1 minute of data (depending on self.delay and the relative response times from PVs)
            if self.pcavbuffer.__len__() >= 600:
                self.pcavbuffer.popleft() # this could technically just have been left to the deque if max length was defined
            self.pcavbuffer.append((self.pcava.value+self.pcavb.value)/2.0)
            # self.pcavcalc = mean(self.pcavbuffer)-self.old_values['pcavcomp']
            self.pcavcalc = (mean(self.pcavbuffer)-self.pcavinitial)*self.pcavscale
            self.matlab_pv['pcavcomp'][0].put(value = mean(self.pcavbuffer), timeout=1.0)
        if self.debug:
            print('tt + pcav: %f'%self.dccalc+self.pcavcalc)
        else:
            # hand off the correction to femto.py via the dcsignal pv
            self.matlab_pv['dcsignal'][0].put(value = self.dccalc+self.pcavcalc, timeout = 1.0)

    def checkState(self):
        """ Check whether state control pvs have been triggered. JM(3/25): ends
        up this could just be handled by a push-button state in EDM (that's how
        Christina wrote it) but this works for pydm."""
        self.usett = self.matlab_pv['usett'][0].get()
        self.usepcav = self.matlab_pv['usepc'][0].get()
        if self.matlab_pv["reqZeroPcav"][0].get() != 0:
            # a pcav zero has been requested
            self.matlab_pv["reqZeroPcav"][0].put(value=0,timeout = 1.0) # toggle the control back off
            self.pcavinitial = (self.pcava.value+self.pcavb.value)/2.0 # until some indication it's needed, just writing the current value, not the processed history average
            self.matlab_pv['pcavoffset'][0].put(value=self.pcavinitial,timeout=2.0)


def run():  # just a loop to keep recording  
    if len(sys.argv) < 2:
        T = time_tool()  # initialize
    else:
        T = time_tool(args.system,debug=args.debug)
    while T.W.error == 0:
        T.W.check() # check / update watchdog counter
        pause(T.delay)
        try:
            T.read_write()  # collects the data 
        except:
            del T
            print('crashed, restarting')
            T = time_tool(args.system,debug=args.debug) # create again
            if T.W.error:
                return        
    pass  

if __name__ == "__main__":
    #parser
    parser = argparse.ArgumentParser(description = 'Alt. version of drift compensation for laser lockers based on PCAVs.')
    parser.add_argument('system', type=str, help="Identifier for the target hutch")
    parser.add_argument("-D", "--debug", action="store_true",help="Print desired moves, but do not execute")
    args = parser.parse_args()
    run()