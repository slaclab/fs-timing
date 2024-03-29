""" Watchdog.py modified for python 3 compatibility.

This is a convenience function implementing a watchdog timer with indirect loop
control via inspection of provided PVs. This is used throughout the fstiming
codebase. This tool is not currently asynchronous.

Dependencies:
- pyepics

Justin May
"""

import time  #includes sleep command to wait for other users

import epics

class watchdog():
    """ Watchdog object to monitor code execution."""
    def __init__(self, pv):
        """ Set up watchdog object with already configured pvs.
        
        This object checks for various error states/control states upon init
        that imply certain control system states.
        
        Arguments:
            pv : a direct link to a watchdog PV
        """

        self.pv = pv
        self.counter = 0;
        try:
            self.pv.get( timeout=1.0)
            self.value = self.pv.value
            if self.value < 0:#command to exit programs
                self.error = 1 #exit program
                print('watchdog pv negative - exiting')
                return
            print('initializing watchdog')
            time.sleep(1) # wait 1 second1 for an update
            self.pv.get(timeout=1.0)
        except:
            print('cant write watchdog pv, exiting')
            self.error = 1
            return
        if self.pv.value < 0:#command to exit programs
            self.error = 1 #exit program
            print('watchdog pv negative - exiting')
            return
        if self.pv.value != self.value:
            self.error = 1
            print('another program is incrementing the watchdog')
            return
        self.error = 0  # OK to continue

    def check(self):  # check watchdog timer
        """ Check status of watchdog and act on special states.
        
        This function will check for various conditions, in particular whether
        the watchdog is jumping values or whether the value of the PV has
        externally been set to an error state. Note, a PV value of 0, the
        control state for requesting a graceful termination of the process, is
        handled externally in femto.py.
        """
        
        try:
            self.pv.get(timeout=1.0)
        except:
            print('not able to read watchdog PV, continuing to try')
            self.error = 0  # not an error (at least for now)
            return
        if self.pv.value < 0:
            self.error = 1 #exit program
            print('watchdog pv negative - exiting')
            return
        if self.pv.value != self.value:  # value changed
            self.error = 1
            print('another program is incrementing the watchdog')
            return
        self.error = 0
        self.value = self.pv.value+1
        self.pv.put(value = self.value, timeout=1.0) # write new number to increment
