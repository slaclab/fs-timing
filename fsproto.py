#fsproto.py
""" Service for driving local simulated fs system pvs for testing.

This utility provides a test bench via channel access for verifying the functionality of the fsManager and related systems.

External dependencies:
- caproto
- numpy

"""

from caproto.server import pvproperty, PVGroup, ioc_arg_parser, run
from matplotlib import *
from textwrap import dedent
import numpy as np
import random
import pdb

class fsioc(PVGroup):
    """
    IOC that provides simulated (and abstracted) fs timing interfaces for testing against the fsmanager.
    """
    beam_tjitter = 1.0e-12 # std of beam jitter (representative)
    beam_drift = 1.0e-13 # the slower beam drift (representative)
    prevValues = np.zeros(4) # array to hold previous values in case iterative processing is needed
    dfreq = 1.0/60.0 # frequency (ie. time-constant) for beam drift
    dt = 1.0

    tt = pvproperty(value=1.0)
    pcav1 = pvproperty(value =0.0, doc='pcav1 pv')
    pcav1gen = random.Random()
    pcav2 = pvproperty(value =0.0, doc='pcav2 pv')
    pcav2gen = random.Random()
    pcav3 = pvproperty(value =0.0, doc='pcav3 pv')
    pcav3gen = random.Random()
    pcav4 = pvproperty(value =0.0, doc='pcav4 pv')
    pcav4gen = random.Random()
    fehps = pvproperty(value =0.0, doc='feh phase shifter')
    nehps = pvproperty(value =0.0, doc='neh phase shifter')
    fehphase = pvproperty(value = 0.0, doc="feh phase") # additional PVs for calculated phase, if needed
    nehphase = pvproperty(value = 0.0, doc="neh phase") # ...
    watchdog = pvproperty(value = 1, doc="simulation watchdog")

    @tt.startup
    async def tt(self, instance, async_lib):
        await self.fehps.write(value=0.0)
        await self.nehps.write(value=0.0)
        await self.watchdog.write(value=self.watchdog.value+1)
        while True:
            tt = self.tt.value + self.dt
            await self.pcavupdate(instance=[self.pcav1gen,self.pcav1])
            await self.pcavupdate(instance=[self.pcav2gen,self.pcav2])
            await self.pcavupdate(instance=[self.pcav3gen,self.pcav3])
            await self.pcavupdate(instance=[self.pcav4gen,self.pcav4])
            await instance.write(value=tt)
            await self.phaseUpdate()
            await async_lib.library.sleep(self.dt)
    
    async def pcavupdate(self, instance):
        newvalue = instance[1].value + instance[0].gauss(0,self.beam_tjitter) + self.beam_drift*np.sin(2*np.pi*self.dfreq*self.tt.value)
        #print(newvalue)
        await instance[1].write(value=newvalue)

    async def phaseUpdate(self):
        # pdb.set_trace()
        await self.fehphase.write(value=(self.pcav1.value+self.pcav2.value)/2.0-self.fehps.value)
        await self.nehphase.write(value=(self.pcav3.value+self.pcav4.value)/2.0-self.nehps.value)

if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix='fsioc:',
        desc=dedent(fsioc.__doc__)
    )
    ioc = fsioc(**ioc_options)
    run(ioc.pvdb, **run_options)