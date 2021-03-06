#ltproto.py
""" Service for driving local simulated laser timing system pvs for testing.

This utility provides a test bench via channel access for verifying the functionality of femto.py and related systems.

External dependencies:
- caproto
- numpy

Developed on a local fsenv (not in version control). This system does not yet implement high level controls, only the interconnected generation of data.

"""

from caproto.server import pvproperty, PVGroup, ioc_arg_parser, run
from matplotlib import *
from textwrap import dedent
import numpy as np
import random
import pdb

class ltioc(PVGroup):
    """
    IOC that provides simulated (and abstracted) fs timing interfaces for testing.
    """
    beam_tjitter = 1.0e-12 # std of beam jitter (representative)
    beam_drift = 1.0e-13 # the slower beam drift (representative)
    prevValues = np.zeros(4) # array to hold previous values in case iterative processing is needed
    dfreq = 1.0/60.0 # frequency (ie. time-constant) for beam drift
    dt = 0.1
    # srcdatapath = "../fstimingrsc/URCPOsco.csv"
    # srcdata = np.genfromtxt(srcdatapath,delimiter=',',skip_header=True,unpack=True,usecols=(1,2))
    # ii = 0
    tt = pvproperty(value=1.0)
    self.pcavsetup()
    self.cabstabsetup()
    self.lasersetup()
    self.laserlockersetup()
    self.atmsetup()
    self.fiberovensetup()
    self.beamsetup()

    @tt.startup
    async def tt(self, instance, async_lib):
        await self.fehps.write(value=0.0)
        await self.nehps.write(value=0.0)
        await self.watchdog.write(value=self.watchdog.value+1)
        while True:
            tt = self.tt.value + self.dt
            # await self.pcavupdate(instance=[self.pcav1gen,self.pcav1])
            # await self.pcavupdate(instance=[self.pcav2gen,self.pcav2])
            await self.pcavrealupdate(instance=[0,self.pcav1])
            await self.pcavrealupdate(instance=[1,self.pcav2])
            await self.pcavupdate(instance=[self.pcav3gen,self.pcav3])
            await self.pcavupdate(instance=[self.pcav4gen,self.pcav4])
            await instance.write(value=tt)
            await self.phaseUpdate()
            self.ii = self.ii + 1
            if self.ii == self.srcdata[0].__len__()-1:
                self.ii = 0
            await async_lib.library.sleep(self.dt)

    def pcavsetup():
        """ Configure the following:
        - two phase cavity outputs
        - one beam phase input
        - one reference phase input
        """
        pcav1 = pvproperty(value =0.0, doc='pcav1 pv',)
        pcav1gen = random.Random()
        pcav2 = pvproperty(value =0.0, doc='pcav2 pv')
        pcav2gen = random.Random()

    def cabstabsetup():
        """ Configure the following:
        - one phase output
        - one phase control input
        """
        phasecntrl = pvproperty(value =0.0, doc='feh phase shifter')
        phaseout = pvproperty(value = 0.0, doc="feh phase") # additional PVs for calculated phase, if needed
        cntrlenable = pvproperty(value = 0.0, doc="feh enable")
        cntrloffset = pvproperty(value = -10.0, doc="feh offset")
        cntrlgain = pvproperty(value = 1.0, doc="feh gain")
        
    def lasersetup():
        """ Configure the following:
        - one laser time out
        - one laser phase
        - one target time input
        - one bypass time input (optional)
        - one trigger time input
        - one laser reference phase input
        """
        laserphase = pvproperty(value =0.0, doc='')
        refphase = pvproperty(value =0.0, doc='')
        laserouttime = pvproperty(value =0.0, doc='')
        timetool = pvproperty(value =0.0, doc='')

    def laserlockersetup():
        """ Configure the following:
        - one target time input
        """
        rfpower = pvproperty(value =0.0, doc='')
        diodepower = pvproperty(value =0.0, doc='')
        piezoamp = pvproperty(value =0.0, doc='')
        llenable = pvproperty(value =0.0, doc='')
        phasemotor = pvproperty(value =0.0, doc='')
        targettime = pvproperty(value =0.0, doc='')
        outputtime = pvproperty(value =0.0, doc='')
        cavfreq = pvproperty(value =0.0, doc='')
        rfpowerstd = pvproperty(value =0.0, doc='')
        diodepowerstd = pvproperty(value =0.0, doc='')
        fserror = pvproperty(value =0.0, doc='')
        sbandoffset = pvproperty(value =0.0, doc='')

    def atmsetup():
        """ Configure the following:
        - atm stage
        - atm intensity
        - atm amplitude
        - pix value
        """
        atmstagepos = pvproperty(value =0.0, doc='')
        ttamp = pvproperty(value =0.0, doc='')
        ipm = pvproperty(value =0.0, doc='')
        pix = pvproperty(value =0.0, doc='')

    def fiberovensetup():
        """ Configure the following:
        - one fiber oven temp input
        - one trigger delay output
        """
        fiberoven = pvproperty(value = 0.0, doc="fiber oven temp")
        fotrigdelay = pvproperty(value = 0.0, doc="trigger delay")

    def beamsetup():
        """ Configure the following:
        - one beam phase input
        - one beam longitudinal jitter input
        """
        beamtime = pvproperty(value = 0.0, doc="beamtime value")
        beamjitter = pvproperty(value = 0.0, doc="beam jitter")
    
    async def pcavupdate(self, instance):
        newvalue = instance[1].value + instance[0].gauss(0,self.beam_tjitter) + self.beam_drift*np.sin(2*np.pi*self.dfreq*self.tt.value)
        #print(newvalue)
        await instance[1].write(value=newvalue)

    async def pcavrealupdate(self,instance):
        await instance[1].write(value=self.srcdata[instance[0]][self.ii])

    async def phaseUpdate(self):
        # pdb.set_trace()
        await self.fehphase.write(value=(self.pcav1.value+self.pcav2.value)/2.0-self.fehps.value)
        await self.nehphase.write(value=(self.pcav3.value+self.pcav4.value)/2.0-self.nehps.value)

class ltmachine():
    """ Data model for laser timing and associated systems (largely to abstract ioc functionality per MVC, without the hassle of managing the pvs."""
    def __init__(self):
        self.pcav = pcavobj()
        self.atm = atmobj()
        self.laser = laserobj()

    async def updateState():
        """ Update the state of the lt model based on current values."""
        await pass

class timingObject():
    """  Base class for abstracted timing objects. """
    def __init__(self):
        self.pvs = {}

    async def updateTimingState():
        """ Update pvs. """
        for pv in self.pvs.values():
            await pv.get()



class laserobj(timingObject):
    """ Implementation of a basic laser. """
    def __init__(self):
        self.pvs.append({
            'laserphase' : pvproperty(value=0.0, doc=''),
            'refphase' : pvproperty(value=0.0, doc=''),
            'laserouttime' : pvproperty(value=0.0, doc=''),
            'timetool' : pvproperty(value=0.0, doc='')
            'outtrigger' : pvproperty(value=0.0, doc='')
        })
        self.baselasertime = 4000 # (ns)
        self.laserjitter = random.Random()
        self.jitterscale = 1.0e-6
        self.outputlasertime = self.baselasertime
        self.oscillatorfreq = 68.0e6 # (MHz; a typical Vitara oscillator)
        self.outtriggertime = 0.0

    def applyLaserJitter():
        """ Simple noise add. """
        self.outputlasertime = self.baselasertime + self.laserjitter.uniform([self.jitterscale]*2)

    async def updateTimingState():
        """ Laser specific update. """
        super().updateTimingState()
        self.baselasertime = self.


class laserLockerobj(timingObject):
    """ Implementation of a gen1 laser locker. """
    def __init__(self):
        self.pvs.append([
            laserphase=pvproperty(value=0.0, doc=''),
            refphase=pvproperty(value=0.0, doc=''),
            laserouttime=pvproperty(value=0.0, doc=''),
            timetool=pvproperty(value=0.0, doc='')
        ])

class atmobj(timingObject):
    """ Implementation of a time tool. """
    def __init__(self):
        self.pvs.append([
            atmstagepos = pvproperty(value =0.0, doc=''),
            ttamp = pvproperty(value =0.0, doc=''),
            ipm = pvproperty(value =0.0, doc=''),
            pix = pvproperty(value =0.0, doc='')
        ])

class pcavobj(timingObject):
    """ Implementation of a phase cavity object. """
    def __init__(self):
        self.pvs.append([
            pcav1 = pvproperty(value =0.0, doc='pcav1 pv'),
            pcav1gen = random.Random(),
            pcav2 = pvproperty(value =0.0, doc='pcav2 pv'),
            pcav2gen = random.Random()
        ])

if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix='ltioc:',
        desc=dedent(ltioc.__doc__)
    )
    ioc = ltioc(**ioc_options)
    run(ioc.pvdb, **run_options)
