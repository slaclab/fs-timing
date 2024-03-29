""" Extracted version of original watchdog function. This was updated to be
Python3 compatible in the module watchdog3.py. Provided for historical
reference.

Justin May
"""

import time  #includes sleep command to wait for other users
class watchdog():
    def __init__(self, pv):  # pv is an already connected pv
        self.pv = pv
        self.counter = 0;
        try:
            self.pv.get(ctrl=True, timeout=1.0)
            self.value = self.pv.value
            if self.value < 0:#command to exit programs
                self.error = 1 #exit program
                print 'watchdog pv negative - exiting'
                return
            print 'initializing watchdog'
            time.sleep(1) # wait 1 second1 for an update
            self.pv.get(ctrl=True, timeout=1.0)
        except:
            print 'cant write watchdog pv, exiting'
            self.error = 1
            return
        if self.pv.value < 0:#command to exit programs
            self.error = 1 #exit program
            print 'watchdog pv negative - exiting'
            return
        if self.pv.value != self.value:
            self.error = 1
            print 'another program is incrementing the watchdog'
            return
        self.error = 0  # OK to continue

    def check(self):  # check watchdog timer
        try:
            self.pv.get(ctrl=True, timeout=1.0)
        except:
            print 'not able to read watchdog PV, continuing to try'
            self.error = 0  # not an error (at least for now)
            return
        if self.pv.value < 0:
            self.error = 1 #exit program
            print 'watchdog pv negative - exiting'
            return
        if self.pv.value != self.value:  # value changed
            self.error = 1
            print 'another program is incrementing the watchdog'
            return
        self.error = 0
        self.value = self.pv.value+1
        self.pv.put(value = self.value, timeout=1.0) # write new number to increment
