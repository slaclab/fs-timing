# fstiming
Repo for migrated fstiming code and resources.

This repo contains code and resources used in the various laser timing control systems. At initial commit, additional repositories around SLAC areas contain additional elements, or redudant copies of code properly found here, and additional components for systems like beam phase cavities, cable stabilizers, etc. Eventually, these outlier code bases will by synchronized with the main operational branch here or moved to separate repositories to establish a separation of function.

## Contents:
- femto.py : nominal baseline version of the laser locker hla
- configs : by default, an empty directory where a user's config files is intended to be placed; everything but the readme in this directory will be ignored by git
- documentation : this directory contains default documentation for laser lockers, a fallback in lieu of site-specific documentation configured per installation. Moreover, this documentation is intended for the limited case of loading via control system panels, and is otherwise superceded by the more robust documentation provided in eg. ptsd-docs, Confluence and Sharepoint
- - documentation/rsc : material referenced in ..
- legacy : material referenced in development and/or included as an absolute fallback in the event everyone simply replaces v1 installations everywhere at once
- support : contains the majority of the related code used in the operation of femto.py and or unit-testing
- - support/tic : various implementations of time interval counter support
- - laserlockerversions : the generation specific versions of laser locker code that is called by femto.py
- templates : instructions and template for configuring an installation
