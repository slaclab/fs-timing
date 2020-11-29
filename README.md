# fstiming
Repo for migrated fstiming code and resources.

This repo contains code and resources used by the various femtosecond timing systems. At initial commit, additional repositories around SLAC areas contain additional elements, or redudant copies of code properly found here. Eventually, these outlier code bases will by synchronized with the main operational branch here.

## Contents:
- femto.py - nominal baseline version of the laser locker hla
- femtoneh.py - pre-repo development branch for the newly commissioned NEH laser hall systems, and XPP
- fsManager.py - informally referred to as "The Glue Code"; coordinates the operation of the cable stabilizer and fiber oven with respect to the phase cavities
- pcav2ttdrift.py - stop gap code for wrapping a laser time feedback on the phase cavity measurements, in lieu of the reference system phase shifters
- time_tool.py - supplemental code for femto.py that processes the results of x-ray/optical cross-correlator measurements to provide fine scale (<100 fs) drift compensation
- watchdog.py - utility class used throughout the fstiming codebase for internal watchdog counting and code life-cycle management