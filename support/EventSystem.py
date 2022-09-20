from epics.pv import PV as Pv

class EventSystem(object):
    """ The EventSystem class is a utility class that provides a series of
    functions to validate the configuration of the LCLS-II event system, for use
    prior to significant adjustments to the event system triggers controlling
    the injector lasers."""
    
    def __init__(self):
        pass

    def validateBeamMode(self):
        """ Check current Beam Mode."""
        checkPV = Pv("TPG:SYS0:1:MOD")
        if checkPV.value == 'SC11':
            return True
        else:
            return False

    def validateTriggerMode(self):
        """ Check current trigger mode."""
        checkPV = Pv("TPG:SYS0:1:PATTERN_TYPE")
        if checkPV.value == 'Continuous Mode':
            return True
        else:
            return False

    def validateMPSSumm(self):
        """ Check the summary MPS status. """
        checkPV = Pv("EVNT:MPSLNKSC:1:STATSUMY")
        if checkPV.value == 0:
            return True
        else:
            return False

    def validateReqRates(self):
        """ Check requested rates to destinations. """
        checkVal = True
        pvStrings = ["TPG:SYS0:1:DST00:REQRATE",
            "TPG:SYS0:1:DST01:REQRATE",
            "TPG:SYS0:1:DST02:REQRATE",
            "TPG:SYS0:1:DST03:REQRATE",
            "TPG:SYS0:1:DST04:REQRATE",
            "TPG:SYS0:1:DST05:REQRATE"]
        allowed = [1,10,100]
        notallowed = [0]
        checkVal = checkVal & (Pv(pvStrings[0]).value in allowed)
        checkVal = checkVal & (Pv(pvStrings[1]).value in allowed)
        checkVal = checkVal & (Pv(pvStrings[2]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[3]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[4]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[5]).value in notallowed)
        return checkVal

    def validateRates(self):
        """ Check rates to destinations. """
        checkVal = True
        pvStrings = ["TPG:SYS0:1:DST00:RATE",
            "TPG:SYS0:1:DST01:RATE",
            "TPG:SYS0:1:DST02:RATE",
            "TPG:SYS0:1:DST03:RATE",
            "TPG:SYS0:1:DST04:RATE",
            "TPG:SYS0:1:DST05:RATE"]
        allowed = [1,10,100]
        notallowed = [0]
        checkVal = checkVal & (Pv(pvStrings[0]).value in allowed)
        checkVal = checkVal & (Pv(pvStrings[1]).value in allowed)
        checkVal = checkVal & (Pv(pvStrings[2]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[3]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[4]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[5]).value in notallowed)
        return checkVal

    def validateMPSBCrb(self):
        """ Check the beam class readback value."""
        checkVal = True
        pvStrings = ["TPG:SYS0:1:DST00:MPS_BC_RBV",
            "TPG:SYS0:1:DST01:MPS_BC_RBV",
            "TPG:SYS0:1:DST02:MPS_BC_RBV",
            "TPG:SYS0:1:DST03:MPS_BC_RBV",
            "TPG:SYS0:1:DST04:MPS_BC_RBV",
            "TPG:SYS0:1:DST05:MPS_BC_RBV"]
        allowed = [1,10,100]
        notallowed = [0]
        checkVal = checkVal & (Pv(pvStrings[0]).value in allowed)
        checkVal = checkVal & (Pv(pvStrings[1]).value in allowed)
        checkVal = checkVal & (Pv(pvStrings[2]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[3]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[4]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[5]).value in notallowed)
        return checkVal

    def validateTPGBCrb(self):
        """ Check the beam class readback value."""
        checkVal = True
        pvStrings = ["TPG:SYS0:1:DST00:TPG_BC_RBV",
            "TPG:SYS0:1:DST01:TPG_BC_RBV",
            "TPG:SYS0:1:DST02:TPG_BC_RBV",
            "TPG:SYS0:1:DST03:TPG_BC_RBV",
            "TPG:SYS0:1:DST04:TPG_BC_RBV",
            "TPG:SYS0:1:DST05:TPG_BC_RBV"]
        allowed = [1,10,100]
        notallowed = [0]
        checkVal = checkVal & (Pv(pvStrings[0]).value in allowed)
        checkVal = checkVal & (Pv(pvStrings[1]).value in allowed)
        checkVal = checkVal & (Pv(pvStrings[2]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[3]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[4]).value in notallowed)
        checkVal = checkVal & (Pv(pvStrings[5]).value in notallowed)
        return checkVal
 
    def validate(self):
        """ Run all tests for event system configuration."""
        accStateValid = True
        # accStateValid = accStateValid & self.validateBeamMode()
        # accStateValid = accStateValid & self.validateTriggerMode()
        # accStateValid = accStateValid & self.validateMPSSumm()
        # accStateValid = accStateValid & self.validateReqRates()
        # accStateValid = accStateValid & self.validateRates()
        # accStateValid = accStateValid & self.validateMPSBCrb()
        # accStateValid = accStateValid & self.validateTPGBCrb()
        return accStateValid