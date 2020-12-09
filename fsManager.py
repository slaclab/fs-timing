#fs_Manager.py
""" Manager for to tie pcav measurements to cable stabilizer and fiber oven.  

This script, and class, implement a simplified version of the control process
that takes the pcav measurements, averages them, and sends drift corrections to
the cable stabilizer system. The fiber oven then corrects for the change in the
cable stabilizer phase.

Dependencies:
- numpy
- matplotlib
- scipy
- watchdog3
- epics (pyepics)

"""

import time
from numpy import *
from matplotlib import *
from scipy import signal
import watchdog3
#from psp.Pv import Pv # uncomment for older compatibility
import epics
import sys
import random
import argparse
from collections import deque
import asyncio
import json
import pdb

class fs_manager():
    """Manages pcav feedback to cable stabilizer, monitors fiber oven."""
    def __init__(self,debug=False):
        self.debug = debug
        self.config = config(debug=self.debug)
        self.config.loadConfig()
        self.pcavdata = []
        for ii in range(0,4):
            self.pcavdata.append(deque([],maxlen=50)) # these vectors hold the recent pcav data for filtering
        self.pcavproc = numpy.zeros(4) # the processed output of the signal processing
        self.soscoeff = signal.iirdesign(wp=0.3,ws=0.5,gpass=0.1,gstop=40.0,output='sos') # basic elliptic low pass
        self.phoffset = {"hxr":0.0,"sxr":0.0}
        self.flywheelcomplete = False
        self.hxrfeedbackenabled = False
        self.sxrfeedbackenabled = False
        self.hxrgain = 0.0
        self.sxrgain = 0.0

    async def fssleep(self):
        await asyncio.sleep(1.0)

    async def updateCablePhaseShifters(self):
        """ Write new values to the phase shifters based on the processed data
        and what is enabled (enabled: TODO)."""
        if self.flywheelcomplete:
            await self.loadCabStabGains()
            if self.hxrfeedbackenabled:
                hxrcorrection = (numpy.mean([self.pcavproc[0],self.pcavproc[1]])- self.phoffset["hxr"])*1.0e-12*360.0*476.0e6*self.hxrgain
                self.writeCablePhaseShifter(beamline="hxr",value=hxrcorrection)
            if self.sxrfeedbackenabled:
                sxrcorrection = (numpy.mean([self.pcavproc[2],self.pcavproc[3]])- self.phoffset["sxr"])*1.0e-12*360.0*476.0e6*self.sxrgain
                self.writeCablePhaseShifter(beamline="sxr",value=sxrcorrection)
        return 0

    def writeCablePhaseShifter(self, beamline, value):
        """ Write a correction term to the selected cable stabilizer."""
        if not self.debug:
            if beamline=="hxr":
                self.config.pvs["fehphaseshifterPV"].put(value)
            elif beamline=="sxr":
                self.config.pvs["nehphaseshifterPV"].put(value)
        else:
            if beamline=="hxr":
                print("fehphase would write: %E" % value)
            elif beamline=="sxr":
                print("nehphase would write: %E" % value)
        return 0
            
    async def updatePcavValues(self):
        """ Grab new phase cavity values and update the feedbacks.

        This is the primary feedback function for this system. We lowpass filter the pcav data for each beamline, and wrap a simple
        feedback around the average.
        """
        self.pcavdata[0].append(self.config.pvs["pcav1PV"].get())
        self.pcavdata[1].append(self.config.pvs["pcav2PV"].get())
        self.pcavdata[2].append(self.config.pvs["pcav3PV"].get())
        self.pcavdata[3].append(self.config.pvs["pcav4PV"].get())
        self.pcavproc[0] = numpy.mean(signal.sosfilt(self.soscoeff,self.pcavdata[0]))
        self.pcavproc[1] = numpy.mean(signal.sosfilt(self.soscoeff,self.pcavdata[1]))
        self.pcavproc[2] = numpy.mean(signal.sosfilt(self.soscoeff,self.pcavdata[2]))
        self.pcavproc[3] = numpy.mean(signal.sosfilt(self.soscoeff,self.pcavdata[3]))
        if self.pcavdata[0].__len__() > 49 and not self.flywheelcomplete:
            self.flywheelcomplete = True
        await self.updateCablePhaseShifters()
        return 0
        

    async def disableFeedbackForBeamline(self, beamline):
        """ Turn off cable stabilizer feedbacks for beamline.
        """
        if beamline == "hxr":
            self.hxrfeedbackenabled = False
            self.config.pvs["fehFBEnable"].put(0)
        elif beamline == "sxr":
            self.sxrfeedbackenabled = False
            self.config.pvs["nehFBEnable"].put(0)
        return 0

    async def enableFeedbackForBeamline(self,beamline):
        """ Turn on cable stabilizer feedbacks for beamline.
        """
        if beamline == "hxr":
            self.hxrfeedbackenabled = True
            self.config.pvs["fehFBEnable"].put(1)
        elif beamline == "sxr":
            self.sxrfeedbackenabled = True
            self.config.pvs["nehFBEnable"].put(1)

    async def loadPreviousPcavValue(self,pcavdeque):
        """ Manage cases of a restart of various components of the system.

        Not yet implemented.
        """
        pass

    async def zeroPcavOffsets(self):
        """ Write current offsets to center both cable stabilizers at current position"""
        await self.zeroPcavOffsetForBeamline('hxr')
        await self.zeroPcavOffsetForBeamline('sxr')
        return 0

    async def zeroPcavOffsetForBeamline(self,beamline):
        """ Write current offsets to center the cable stabilizer for a
        beamline."""
        if self.debug:
            print("zeroing pcav offsets for %s" % beamline.upper())
        if beamline=="hxr":
            self.phoffset["hxr"]= numpy.mean([self.config.pvs["pcav1PV"].get(),self.config.pvs["pcav2PV"].get()])
        elif beamline=="sxr":
            self.phoffset["sxr"]= numpy.mean([self.config.pvs["pcav3PV"].get(),self.config.pvs["pcav4PV"].get()])
        return 0
        # update dc offset to phase shifter delta correction term
        # save these offsets to local values

    async def loadPcavOffsets(self):
        """ Load pcav offsets from previous values, if needed."""
        pass

    async def loadCabStabGains(self):
        """ Update the feedback gains from the PVs. """
        self.hxrgain = self.config.pvs["fehFBGain"].get()
        self.sxrgain = self.config.pvs["nehFBGain"].get()
        self.hxrfeedbackenabled = self.config.pvs["fehFBEnable"].get()
        self.sxrfeedbackenabled = self.config.pvs["nehFBEnable"].get()

class config(object):
    def __init__(self,debug=False):
        self.pvstrlist = ["pcav1PV","pcav2PV","pcav3PV","pcav4PV","fehphaseshifterPV","nehphaseshifterPV","fiberoventempPV","watchdog","fehFBEnable","nehFBEnable","fehFBOffset","nehFBOffset","fehFBGain","nehFBGain","restorePrevious"]
        self.configIsValid = False
        self.pvs = {}
        self.debug = debug
    
    def loadConfig(self):
        with open("fsmanager_config.json",'r') as fp:
            self.inputjson = json.load(fp)
        for pvstr in self.pvstrlist:
            if pvstr not in self.inputjson["pvs"].keys():
                print("configuration file poorly formatted: %s" % pvstr)
                return
            else:
                self.pvs[pvstr] = epics.PV(self.inputjson["pvs"][pvstr])
                temp = self.pvs[pvstr].get()
                if temp is None:
                    print("could not access pv: %s" % pvstr)
                    return
        self.configIsValid = True
        if self.debug:
            print('loadConfig: completed')

async def main():
    fsmgr = fs_manager(debug=args.debug)
    watchdogCounter = watchdog3.watchdog(fsmgr.config.pvs["watchdog"])
    if watchdogCounter.error:
        return 1
    await fsmgr.zeroPcavOffsets()
    while True:
        await fsmgr.updatePcavValues()
        await fsmgr.fssleep()
        # pdb.set_trace()
        # print(fsmgr.pcavdata[0][0],fsmgr.pcavdata[2][0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Manager for to tie pcav measurements to cable stabilizer and fiber oven.')
    parser.add_argument("-D", "--debug", action="store_true",help="Print output state, but do not execute")
    parser.add_argument("-S", "--simulation", action="store_true",help="Run the manager code with simulated PVs")
    args = parser.parse_args()
    # asyncio.run(main()) # changing to python3.6
    asyncio.get_event_loop().run_until_complete(main())