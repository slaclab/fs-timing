# S0 Laser Timing - In-Brief
## [Commissioning Progressing - This documentation subject to change.]

Author: **J.May**
Date: 2022-04-04
Updated: __2022-09-20__

----

There are currently two primary panels accessible for accessing the rf locking and timing controls for the laser.

The user panel will load a panel that provides inputs in degrees to the laser timing control. This is designed to match what operations in ACR is familiar with on the NC systems. The configuration file for the laser provides the frequency used to convert. The controls on this panel talk to the phase offset controls in the Script I/O panel accessible in the expert controls.

![userpanel with tooltips](/documentation/rsc/S0_userpanel_tooltips.png)

The expert controls should be familiar to those used to LCLS-I. The panel presents the same information, and can be used in much the same way, though the route the data gets to the panel, from ATCA firmware registers and such, is different. 

[For extended documentation on this system [under development]](https://confluence.slac.stanford.edu/display/PCDS/Generation+1.5+Documentation)) and [Hardware](https://confluence.slac.stanford.edu/pages/viewpage.action?pageId=320476135)