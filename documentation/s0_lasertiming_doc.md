# S0 Laser Timing - In-Brief
## [Commissioning Progressing - This documentation subject to change.]

Author: **J.May**
Date: __2022-04-04__

----

To load the simple user overview panel for now (until panels are fully commissioned):  
```
source $PACKAGE_TOP/anaconda/envs/python3.7env/bin/activate
pydm laserTimingOverview.py ../fs-timing/configs/s0_amp_uv_1.json &
```

This will load a panel that provides inputs in degrees to the laser timing control. This is designed to match what operations in ACR is familiar with on the NC systems. The configuration file loaded above provides the frequency used to convert, and should be set for gun, mdl, etc. as desired.

The main panel, re-wired from the old Vitara Details panel, has mostly the same functionality as that system, however, the timing controls are currently coded directly to the phase control of the oscillator, and not the target time (the result of the oscillator phase and the laser triggers).

[For extended documentation on this system [under development]](https://confluence.slac.stanford.edu/display/PCDS/Generation+1.5+Documentation))