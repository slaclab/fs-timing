from ..tic.TimeIntervalCounter import TimeIntervalCounter
from ..tic.Keysight import Keysight

class LaserLocker(object):
    """Generalized LaserLocker class. Hardware-specific implementations inherit
    the base LaserLocker class."""
    def __init__(self,errorLog,pvs,watchdog):
        """ Initialize LaserLocker object.
        
        Arguments:
            errorLog : error logging object (see ErrorOutput.py)
            pvs : PVS object (see PVS.py)
            watchdog : watchdog monitor (see watchdog3.py)
        """

        self.E = errorLog
        self.P = pvs
        self.W = watchdog
        pass
    
    def Calibrate(self,report=False):
        """Calibrate a laser locker to determine the relationship between the
        oscillator phase and the coarse event timing. If report is True,
        then output a record of the calibration. This function should be
        implemented at the child level, and should never fail whether
        report is true or false."""
        pass

    def locker_status(self):
        """Rolls up the status checks for a laser into a boolean response of
        whether the laser is in a "good" state or not."""
        self.E.write_error({'value':'LaserLocker super method: locker_status called','lvl':1})
        return True

    def isLaserTimeOk(self):
        """Check the time of the laser and the setpoint and return if the value
        is correct."""
        self.E.write_error({'value':'LaserLocker super method:isLaserTimeOk called','lvl':1})
        return False

    def isBucketJump(self):
        """Check whether the current time qualifies as a bucket jump."""
        pass

    def fixBucketJump(self):
        """Fix the time"""
        pass

    def setTime(self,tgt):
        """Issue the necessary time changes."""
        pass

    def setOscillatorPhase(self,tgt):
        """Set the necessary oscillator phase calculated."""
        pass

    def setTriggerTime(self,time):
        """Lower level function for setting a time value for the defined trigger."""
        pass