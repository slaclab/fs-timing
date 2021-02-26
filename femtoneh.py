
#femto.py  program to control laser femtosecond timing
#updated 9/27/13 14?30

# updated 10/01/13 - jemay : corrected capitalization error in error reporting try case;
# updated 10/01/13 - jemay : inverted phase sign for feedback to match what ops expects
# updated 10/03/13 - jemay : moved up-to-date code into place to fix stomped on version on production servers
# updated 10/15/13  frisch - add facet PVS  (reversion from earlier vesion)
# updated 10/17/13  frisch  - add loop delay to laser not-ok line to prevent loop spinning
# updated 10/28/13 frisch - added BCS tip logic (untested)
# updated 10/30/13 release version ,bcs reset doesn't work
# updated 11/1/13  test release
# updated 11/5/13   always use same algorithm for phase control
# updated 11/12/13 frisch - fix bcs lockup bug. release for LCLS
# updated 11/13/13b frisch - test version to allow conversion from matlab, write errors 
# updated 11/11/13 frisch
# updated 11/19/13 frisch
# updated 12/2/13 frisch
# updated 12/4/13 frisch, massive updates
# upadated 12/17/13 frisch to use XPP Pvs.
# updated 1/7/14 Now dev version with new time interval counter code
# updated 1/8/14 modes for XP
# updated 1/10/14 more dev
# updated 1/13/14  ready to move back to anaconda
# updated 1/14/14 use ns pvs for XPP
# updated 2/14/14  test with different offset in triger time - mystery
# 2/14/14 revert to previous
# 2/19;14 Update PVs for MEC
# 2/23/14 Update counter timeout for slow systems like MEC.
# 2/25/14 change offset for triggers to fix jump area
# 3/10/14 add secondary calibration routine - compare with scope / lbnl
# 3/13/14  changes for facet
# 3/14/14  Chagnes for mec
# 4/1/14 Disable plotting for seconddary calibartion
# 4/7/14 Put 201fs allowance on phase in the script. (avoid floating point roundoff).
#4/8/14 attempt to fix 56 bug
#4/14/14  allow negative times TEST
#4/17/14 increase allowed delay further.
#5/2/14 change to facet multiknob
#5/7/14 Add LBNL drift correction to XPP
#6/4/14 Added CXI
#6/17/14 add dither for  XPP
#7/9/14 Begin adding ASTA block
#7/28/14 add limits on time
#7/30/14 increase jump limit from .04 to .05 for mec
#9/12/14 fix bug for injector laseres
#10/1/14 Add CXI, AMO SXR, update watchdog in calibrate loop
#10/7/14 modify logic to show large time interval counter range.
#10/9/14 fix bad CXI PV
#10/13/14 Change CXI timign pv
#11/26/14 fix AMO trigger PV to strange convention.
#2015-10-29 AMO trigger PV changed again
#2015-12-08 Removed hard limits on TT drift addition

import time
import math
from pylab import *
import watchdog
from psp.Pv import Pv
import sys
import random  # random number generator for secondary calibration
from scipy.optimize import leastsq # for secondary calibration

class PVS():   # creates pvs
    def __init__(self, nx='NULL'):
        self.version = 'Watchdog 141126a' # version string
        self.name = nx
        print self.name
        namelist = set()
        self.pvlist = dict()  # will hold pvs with names
        matlab_list = dict() # list of matlab style pvs, tuples of matlab number offset and pv description
        matlab_pv_base = dict() # header matlab pvs like SIOC:SYS0:ML00:OA....
        matlab_pv_offset = dict() # start number for pvs
        matlab_pv_digits = dict()  # number of digits for each pv
        matlab_use = dict() # set to true if this matlab pv shoudl be used even if a ioc pv exists defined below.
        for n in range(0,20):
            matlab_use[n] = True  # initize to always use matlab, override to use epics pvs.
        counter_base = dict()  # holds counter name
        freq_counter = dict() # frequencycounter name
        dev_base = dict() # used to generate other device names (mostl future)
        phase_motor = dict()
        laser_trigger = dict()
        trig_in_ticks = dict() # 1 if trigger units are ticks (1/119MHz), 0 if in nanoseconds( kludge for multi systems)
        reverse_counter = dict()  # 1 if the laser starts the counter, trigger stops.        
        error_pv_name = dict()    
        use_secondary_calibration = dict() # use a scope or other device
        for n in range(0,20):
            use_secondary_calibration[n] = False  # Turn off except where needed.
        secondary_calibration_enable = dict() # set to 1 to enable secondary calibration
        secondary_calibration = dict() # the pv to use for secondary calibration
        secondary_calibration_s = dict() # sine term for calibration
        secondary_calibration_c = dict() # cosine term for calibration
        use_drift_correction = dict() # used to set up the drifty correction based on LBNL
        drift_correction_signal = dict() # what PV to read
        drift_correction_multiplier = dict() # multiples the signal to get value
        drift_correction_value = dict() # PV the current reading in ns.
        drift_correction_offset = dict() # PV in final nanoseconds
        drift_correction_gain = dict()  # PV nanoseconds / pv value, 0 is disable
        drift_correction_smoothing = dict()  # number of pulse to exponential average
        drift_correction_accum = dict() # enables/disables drift correction accumulation (I term)
        for n in range(0,20):
            use_drift_correction[n] = False  # Turn off except where needed.
        use_dither = dict() # used to allow fast dither of timing (for special functions)
        dither_level = dict()  # amount of dither in picoseconds
        for n in range(0,20):
            use_dither[n] = False  # Turn off except where needed.
        version_pv_name = dict()
        matlab = dict()  # holds all matlab use pvs
        timeout = 1.0  # default timeout for connecting to pvs
        
        
        nm = 'ASTA'
        namelist.add(nm)
        base = 'OSC:AS01:1:'  # base name for this sysetm
        dev_base[nm] = base  # no separate device base for this one.
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base   # time interval counter - no added base to this one.
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'M1_MOTR_IQ' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'TRIG:AS01:RF01:SPARE5:TDES' # updated for ASTA
        trig_in_ticks[nm] = 0  # Now using new time invariant trjggers
        reverse_counter[nm] = 1  # start / stop reversed for this laser
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new Epics pvs for XPP.
        matlab[nm] = matlab_use    
        use_drift_correction[nm] = False  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)
        
        
        
        nm = 'FACET'
        namelist.add(nm)  # add to list of recognized systems
        dev_base[nm] = 'OSC:LA20:10:'  
        matlab_pv_base[nm] = 'SIOC:SYS1:ML00:AO'
        matlab_pv_offset[nm] = 451
        matlab_pv_digits[nm] = 3
        counter_base[nm] = 'UTIC:LA20:10:'
        freq_counter[nm] = dev_base[nm] +'FREQ_RBCK'
        phase_motor[nm] = dev_base[nm] + 'M1_MOTR_IQ'
        laser_trigger[nm] = 'MKB:SYS1:1:VAL'  # multiknob to run trigger
        error_pv_name[nm] = dev_base[nm]+ 'FS_STATUS'
        version_pv_name[nm] = dev_base[nm]  + 'FS_WATCHDOG.DESC'
        trig_in_ticks[nm] = 0
        reverse_counter[nm] = 1
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # initize to always use matlab, override to use epics pvs.
        matlab[nm] = matlab_use
        use_drift_correction[nm] = False  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)

        nm = 'AMO'
        namelist.add(nm)
        base = 'LAS:FS1:'  # base name for this sysetm
        dev_base[nm] = base+'VIT:'
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base+'CNT:TI:'   # time interval counter
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'MMS:PH' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'LAS:R51:EVR:33:TRIG0:TDES' # was 'LAS:R51:EVR:33:1:TRIG0:TDES' and before 'LAS:SR63:EVR:09:CTRL.DG0D'
        trig_in_ticks[nm] = 0  # eEdu Granados <edu.granados@gmail.com>xperiment side triggers operate in ticks units
        reverse_counter[nm] = 1
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new PVs
        matlab[nm] = matlab_use    
        use_drift_correction[nm] = False  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)

        nm = 'SXR'
        namelist.add(nm)
        base = 'LAS:FS2:'  # base name for this sysetm
        dev_base[nm] = base+'VIT:'
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base+'CNT:TI:'   # time interval counter
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'MMS:PH' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'LAS:R52:EVR:30:TRIG0:TDES' # was 'LAS:SR63:EVR:09:CTRL.DG0D'
        trig_in_ticks[nm] = 0  # eEdu Granados <edu.granados@gmail.com>xperiment side triggers operate in ticks units
        reverse_counter[nm] = 1
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new PVs
        matlab[nm] = matlab_use    
        use_drift_correction[nm] = False  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)

        nm = 'XPP'
        namelist.add(nm)
        base = 'LAS:FS3:'  # base name for this sysetm
        dev_base[nm] = base+'VIT:'
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base+'CNT:TI:'   # time interval counter
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'MMS:PH' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'LAS:R54:EVR:27:TRIG0:TDES' # was DG2D???  was -39983
        trig_in_ticks[nm] = 0  # Now using new time invariant trjggers
        reverse_counter[nm] = 1  # start / stop reversed for this laser
        use_secondary_calibration[nm] = 1
        secondary_calibration_enable[nm] = 'LAS:FS3:VIT:matlab:01'  #enables secondary calibration.
        secondary_calibration[nm] = 'XPP:USER:LAS:T0_MONITOR'
        secondary_calibration_s[nm] = 'LAS:FS3:VIT:matlab:02'
        secondary_calibration_c[nm] = 'LAS:FS3:VIT:matlab:03'
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new Epics pvs for XPP.
        # modified for timetool drift draft
        drift_correction_signal[nm] = 'LAS:FS3:VIT:matlab:29' # what PV to read
        drift_correction_multiplier[nm] = -1/(2.856 * 360); 
        drift_correction_value[nm]= 'LAS:FS3:VIT:matlab:04'# PV the current reading in ns.
        drift_correction_offset[nm]= 'LAS:FS3:VIT:matlab:05' # PV in final nanoseconds
        drift_correction_gain[nm]= 'LAS:FS3:VIT:matlab:06'  # PV nanoseconds / pv value, 0 is disable
        drift_correction_smoothing[nm]='LAS:FS3:VIT:matlab:07'
        drift_correction_accum[nm]='LAS:FS3:VIT:matlab:09'
        use_drift_correction[nm] = True  
        use_dither[nm] = True # used to allow fast dither of timing (for special functions)
        dither_level[nm] = 'LAS:FS3:VIT:matlab:08'    
        matlab[nm] = matlab_use


        nm = 'XCS'
        namelist.add(nm)
        base = 'LAS:FS4:'  # base name for this sysetm
        dev_base[nm] = base+'VIT:'
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base+'CNT:TI:'   # time interval counter
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'MMS:PH' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'XCS:LAS:EVR:01:TRIG0:TDES' # was 'LAS:SR63:EVR:09:CTRL.DG0D'
        trig_in_ticks[nm] = 0  # eEdu Granados <edu.granados@gmail.com>xperiment side triggers operate in ticks units
        reverse_counter[nm] = 1
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new PVs
        # modified for timetool drift draft
        drift_correction_signal[nm] = 'LAS:FS4:VIT:matlab:29' # what PV to read
        drift_correction_multiplier[nm] = -1/(2.856 * 360); 
        drift_correction_value[nm]= 'LAS:FS4:VIT:matlab:04'# PV the current reading in ns.
        drift_correction_offset[nm]= 'LAS:FS4:VIT:matlab:05' # PV in final nanoseconds
        drift_correction_gain[nm]= 'LAS:FS4:VIT:matlab:06'  # PV nanoseconds / pv value, 0 is disable
        drift_correction_smoothing[nm]='LAS:FS4:VIT:matlab:07'
        drift_correction_accum[nm]='LAS:FS4:VIT:matlab:09'
        use_drift_correction[nm] = True  
        use_dither[nm] = True # used to allow fast dither of timing (for special functions)
        dither_level[nm] = 'LAS:FS4:VIT:matlab:08'    
        matlab[nm] = matlab_use


        nm = 'CXI'
        namelist.add(nm)
        base = 'LAS:FS5:'  # base name for this sysetm
        dev_base[nm] = base+'VIT:'
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base+'CNT:TI:'   # time interval counter
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'MMS:PH' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'LAS:R52B:EVR:31:TRIG0:TDES' # was 'LAS:SR63:EVR:09:CTRL.DG0D'
        trig_in_ticks[nm] = 0  # eEdu Granados <edu.granados@gmail.com>xperiment side triggers operate in ticks units
        reverse_counter[nm] = 1
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new PVs
        matlab[nm] = matlab_use    
        # modified for timetool drift draft
        drift_correction_signal[nm] = 'LAS:FS5:VIT:matlab:29' # what PV to read
        drift_correction_multiplier[nm] = -1/(2.856 * 360); 
        drift_correction_value[nm]= 'LAS:FS5:VIT:matlab:04'# PV the current reading in ns.
        drift_correction_offset[nm]= 'LAS:FS5:VIT:matlab:05' # PV in final nanoseconds
        drift_correction_gain[nm]= 'LAS:FS5:VIT:matlab:06'  # PV nanoseconds / pv value, 0 is disable
        drift_correction_smoothing[nm]='LAS:FS5:VIT:matlab:07'
        drift_correction_accum[nm]='LAS:FS5:VIT:matlab:09'
        use_drift_correction[nm] = True  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)


        nm = 'MEC'
        namelist.add(nm)
        base = 'LAS:FS6:'  # base name for this sysetm
        dev_base[nm] = base+'VIT:'
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base+'CNT:TI:'   # time interval counter
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'MMS:PH' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'LAS:MEC:EVR:03:TRIG0:TDES' # was 'LAS:SR63:EVR:09:CTRL.DG0D'
        trig_in_ticks[nm] = 0  # eEdu Granados <edu.granados@gmail.com>xperiment side triggers operate in ticks units
        reverse_counter[nm] = 1
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new PVs  
        matlab[nm] = matlab_use 
        use_drift_correction[nm] = False  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)          

        
       

        nm = 'VITARA1'
        namelist.add(nm)
        dev_base[nm] = 'OSC:LR20:20:'
        version_pv_name[nm] =  dev_base[nm] +'FS_WATCHDOG.DESC'  # holds version string
        matlab_pv_base[nm] = 'SIOC:SYS0:ML01:AO'
        matlab_pv_offset[nm] = 480
        matlab_pv_digits[nm] = 3
        counter_base[nm] = dev_base[nm]
        freq_counter[nm] = dev_base[nm] + 'FREQ_CUR'
        phase_motor[nm] = dev_base[nm] + 'M1_MOTR_IQ'
        laser_trigger[nm] = 'TRIG:LR20:LS02:TDES'
        error_pv_name[nm] = dev_base[nm] + 'FS_STATUS'
        version_pv_name[nm] = dev_base[nm] + 'FS_WATCHDOG.DESC'
        trig_in_ticks[nm] = 0
        reverse_counter[nm] = 1
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # epicspvs .
        matlab[nm] = matlab_use
        use_drift_correction[nm] = False  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)
        
        
        nm = 'VITARA2'
        namelist.add(nm)
        dev_base[nm] = 'OSC:LR20:10:'
        version_pv_name[nm] = dev_base[nm] + 'FS_WATCHDOG.DESC'  # holds version string
        matlab_pv_base[nm] = 'SIOC:SYS0:ML01:AO'
        matlab_pv_offset[nm] = 480
        matlab_pv_digits[nm] = 3
        counter_base[nm] = dev_base[nm]
        freq_counter[nm] = dev_base[nm] + 'FREQ_CUR'
        phase_motor[nm] = dev_base[nm] + 'M1_MOTR_IQ'
        laser_trigger[nm] = 'TRIG:LR20:LS03:TDES'
        error_pv_name[nm] = dev_base[nm] + 'FS_STATUS'
        version_pv_name[nm] = dev_base[nm] + 'FS_WATCHDOG.DESC'
        trig_in_ticks[nm] = 0
        reverse_counter[nm] = 1
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # epicspvs .
        matlab[nm] = matlab_use
        use_drift_correction[nm] = False  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)

        nm = 'FS11'
        namelist.add(nm)
        base = 'LAS:FS11:'  # base name for this sysetm
        dev_base[nm] = base+'VIT:'
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base+'CNT:TI:'   # time interval counter
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'MMS:PH' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'EVR:LAS:LHN:01:TRIG1:TDES' # was DG2D???  was -39983
        trig_in_ticks[nm] = 0  # Now using new time invariant trjggers
        reverse_counter[nm] = 1  # start / stop reversed for this laser
        use_secondary_calibration[nm] = 0
        secondary_calibration_enable[nm] = 'LAS:FS11:VIT:matlab:01'  #enables secondary calibration.
        secondary_calibration[nm] = 'XPP:USER:LAS:T0_MONITOR'
        secondary_calibration_s[nm] = 'LAS:FS11:VIT:matlab:02'
        secondary_calibration_c[nm] = 'LAS:FS11:VIT:matlab:03'
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new Epics pvs for XPP.
        # modified for timetool drift draft
        drift_correction_signal[nm] = 'LAS:FS11:VIT:matlab:29' # what PV to read
        drift_correction_multiplier[nm] = -1/(2.856 * 360); 
        drift_correction_value[nm]= 'LAS:FS11:VIT:matlab:04'# PV the current reading in ns.
        drift_correction_offset[nm]= 'LAS:FS11:VIT:matlab:05' # PV in final nanoseconds
        drift_correction_gain[nm]= 'LAS:FS11:VIT:matlab:06'  # PV nanoseconds / pv value, 0 is disable
        drift_correction_smoothing[nm]='LAS:FS11:VIT:matlab:07'
        drift_correction_accum[nm]='LAS:FS11:VIT:matlab:09'
        use_drift_correction[nm] = True  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)
        dither_level[nm] = 'LAS:FS11:VIT:matlab:08'    
        matlab[nm] = matlab_use

        nm = 'FS14'
        namelist.add(nm)
        base = 'LAS:FS14:'  # base name for this sysetm
        dev_base[nm] = base+'VIT:'
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base+'CNT:TI:'   # time interval counter
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'MMS:PH' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'EVR:LAS:LHN:04:TRIG1:TDES' # was DG2D???  was -39983
        trig_in_ticks[nm] = 0  # Now using new time invariant trjggers
        reverse_counter[nm] = 1  # start / stop reversed for this laser
        use_secondary_calibration[nm] = 0
        secondary_calibration_enable[nm] = 'LAS:FS14:VIT:matlab:01'  #enables secondary calibration.
        secondary_calibration[nm] = 'XPP:USER:LAS:T0_MONITOR'
        secondary_calibration_s[nm] = 'LAS:FS14:VIT:matlab:02'
        secondary_calibration_c[nm] = 'LAS:FS14:VIT:matlab:03'
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new Epics pvs for XPP.
        # modified for timetool drift draft
        drift_correction_signal[nm] = 'LAS:FS14:VIT:matlab:29' # what PV to read
        drift_correction_multiplier[nm] = -1/(2.856 * 360); 
        drift_correction_value[nm]= 'LAS:FS14:VIT:matlab:04'# PV the current reading in ns.
        drift_correction_offset[nm]= 'LAS:FS14:VIT:matlab:05' # PV in final nanoseconds
        drift_correction_gain[nm]= 'LAS:FS14:VIT:matlab:06'  # PV nanoseconds / pv value, 0 is disable
        drift_correction_smoothing[nm]='LAS:FS14:VIT:matlab:07'
        drift_correction_accum[nm]='LAS:FS14:VIT:matlab:09'
        use_drift_correction[nm] = True  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)
        dither_level[nm] = 'LAS:FS14:VIT:matlab:08'    
        matlab[nm] = matlab_use
       

        while not (self.name in namelist):
            print self.name + '  not found, please enter one of the following '
            for x in namelist:
                print x
            self.name = raw_input('enter system name:')                           

        matlab_use = matlab[self.name]
        self.use_secondary_calibration = use_secondary_calibration[self.name]
        self.use_drift_correction = use_drift_correction[self.name]
        if self.use_drift_correction:
            self.drift_correction_multiplier = drift_correction_multiplier[self.name]
        self.use_dither = use_dither[self.name] # used to allow fast dither of timing (for special functions)
        if self.use_dither:
            self.dither_level = dither_level[self.name]      
        self.trig_in_ticks = trig_in_ticks[self.name]
        self.reverse_counter = reverse_counter[self.name]                     
        #matlab list holds tuples of the matlab variable index offset and description field                       
        matlab_list['watchdog'] = 0,'femto watchdog' + self.version # matlab variable and text string
        matlab_list['oscillator_f'] = 1,'femto oscillator target F' # frequency to enter in oscillator field
        matlab_list['time'] = 2,'femto target time ns' # when control is enabled, laser will move to this time on counter
        matlab_list['calibrate'] = 3,'femto enter 1 to calibrate' # used to run calibration routine
        matlab_list['enable'] = 4,'femto enable time control' # automated time control
        matlab_list['busy'] = 5,'femto control busy'
        matlab_list['error'] = 6,'timing error vs freq counter'
        matlab_list['ok'] = 7,'femto Laser OK'
        matlab_list['fix_bucket'] = 8, 'fix bucket jump' # used to fix a bucket error
        matlab_list['delay'] = 9, 'trigger delay - do not change'
        matlab_list['offset'] = 10, 'timing  offset do not change'
        matlab_list['enable_trig'] = 11, 'enable trigger control'
        matlab_list['bucket_error'] = 12, ' buckets of 3808MHz error'        
        matlab_list['unfixed_error'] = 13, 'error from integer buckets ns'
        matlab_list['bucket_counter'] = 14, 'bucket corrects since reset'
        matlab_list['deg_Sband'] = 15, 'Degrees S band control'
        matlab_list['deg_offset'] = 16, 'Degrees offset'
        matlab_list['ns_offset'] =  17, 'ns, offset degS control'       
        matlab_list['calib_error'] = 19, 'last calibration error ns'
        
        # List of other PVs used.
        self.pvlist['watchdog'] =  Pv(dev_base[self.name]+'FS_WATCHDOG')
        self.pvlist['oscillator_f'] =  Pv(dev_base[self.name]+'FS_OSC_TGT_FREQ')
        self.pvlist['time'] =  Pv(dev_base[self.name]+'FS_TGT_TIME')
        self.pvlist['time_hihi'] =  Pv(dev_base[self.name]+'FS_TGT_TIME.HIHI')
        self.pvlist['time_lolo'] =  Pv(dev_base[self.name]+'FS_TGT_TIME.LOLO')
        self.pvlist['calibrate'] =  Pv(dev_base[self.name]+'FS_START_CALIB')
        self.pvlist['enable'] =  Pv(dev_base[self.name]+'FS_ENABLE_TIME_CTRL')
        self.pvlist['busy'] =  Pv(dev_base[self.name]+'FS_CTRL_BUSY')
        self.pvlist['error'] =  Pv(dev_base[self.name]+'FS_TIMING_ERROR')
        self.pvlist['ok'] =  Pv(dev_base[self.name]+'FS_LASER_OK')
        self.pvlist['fix_bucket'] =  Pv(dev_base[self.name]+'FS_ENABLE_BUCKET_FIX')   
        self.pvlist['delay'] =  Pv(dev_base[self.name]+'FS_TRIGGER_DELAY')
        self.pvlist['offset'] =  Pv(dev_base[self.name]+'FS_TIMING_OFFSET')
        self.pvlist['enable_trig'] =  Pv(dev_base[self.name]+'FS_ENABLE_TRIGGER')
        self.pvlist['bucket_error'] =  Pv(dev_base[self.name]+'FS_BUCKET_ERROR')
        self.pvlist['bucket_counter'] =  Pv(dev_base[self.name]+'FS_CORRECTION_CNT')
        self.pvlist['deg_Sband'] =  Pv(dev_base[self.name]+'PDES')
        self.pvlist['deg_offset'] =  Pv(dev_base[self.name]+'POC')
        self.pvlist['ns_offset'] =  Pv(dev_base[self.name]+'FS_NS_OFFSET')
        self.pvlist['calib_error'] =  Pv(dev_base[self.name]+'FS_CALIB_ERROR')
        
        if self.reverse_counter:
            self.pvlist['counter'] = Pv(counter_base[self.name]+'GetOffsetInvMeasMean')  #time interval counter result, create Pv
            self.pvlist['counter_low'] = Pv(counter_base[self.name]+'GetOffsetInvMeasMean.LOW')        
            self.pvlist['counter_high'] = Pv(counter_base[self.name]+'GetOffsetInvMeasMean.HIGH') 
        
        else:
            self.pvlist['counter'] = Pv(counter_base[self.name]+'GetMeasMean')  #time interval counter result, create Pv
            self.pvlist['counter_low'] = Pv(counter_base[self.name]+'GetMeasMean.LOW')        
            self.pvlist['counter_high'] = Pv(counter_base[self.name]+'GetMeasMean.HIGH') 
        
        self.pvlist['counter_jitter'] = Pv(counter_base[self.name]+'GetMeasJitter')
        self.pvlist['counter_jitter_high'] = Pv(counter_base[self.name]+'GetMeasJitter.HIGH')        
        self.pvlist['freq_counter'] = Pv(freq_counter[self.name])  # frequency counter readback        
        self.pvlist['phase_motor'] = Pv(phase_motor[self.name])  # phase control smart motor
        self.pvlist['phase_motor_dmov'] = Pv(phase_motor[self.name]+'.DMOV')  # motor motion status
        self.pvlist['phase_motor_rb'] = Pv(phase_motor[self.name]+'.RBV')  # motor readback
        self.pvlist['freq_sp'] =  Pv(dev_base[self.name]+'FREQ_SP')  # frequency counter setpoing
        self.pvlist['freq_err'] = Pv(dev_base[self.name]+'FREQ_ERR') # frequency counter error
        self.pvlist['rf_pwr']= Pv(dev_base[self.name]+'CH1_RF_PWR') # RF power readback
        self.pvlist['rf_pwr_lolo']= Pv(dev_base[self.name]+'CH1_RF_PWR'+'.LOLO') # RF power readback
        self.pvlist['rf_pwr_hihi']= Pv(dev_base[self.name]+'CH1_RF_PWR'+'.HIHI') # RF power readback 
        self.pvlist['diode_pwr'] = Pv(dev_base[self.name]+'CH1_DIODE_PWR')
        self.pvlist['diode_pwr_lolo'] = Pv(dev_base[self.name]+'CH1_DIODE_PWR'+'.LOLO')
        self.pvlist['diode_pwr_hihi'] = Pv(dev_base[self.name]+'CH1_DIODE_PWR'+'.HIHI')
        self.pvlist['laser_trigger'] = Pv(laser_trigger[self.name])
        self.pvlist['laser_locked'] = Pv(dev_base[self.name]+'PHASE_LOCKED')
        self.pvlist['lock_enable'] = Pv(dev_base[self.name]+'RF_LOCK_ENABLE')
        self.pvlist['unfixed_error'] =  Pv(dev_base[self.name]+'FS_UNFIXED_ERROR')
  
        if self.use_secondary_calibration:
            self.pvlist['secondary_calibration'] = Pv(secondary_calibration[self.name])
            self.pvlist['secondary_calibration_enable'] = Pv(secondary_calibration_enable[self.name])
            self.pvlist['secondary_calibration_s'] = Pv(secondary_calibration_s[self.name])
            self.pvlist['secondary_calibration_c'] = Pv(secondary_calibration_c[self.name])
        if self.use_drift_correction:
            self.pvlist['drift_correction_signal'] = Pv(drift_correction_signal[self.name])
            self.pvlist['drift_correction_value'] = Pv(drift_correction_value[self.name])
            self.pvlist['drift_correction_offset'] = Pv(drift_correction_offset[self.name])
            self.pvlist['drift_correction_gain'] =  Pv(drift_correction_gain[self.name])
            self.pvlist['drift_correction_smoothing'] =  Pv(drift_correction_smoothing[self.name])
            self.pvlist['drift_correction_accum'] = Pv(drift_correction_accum[self.name])
        if self.use_dither:
            self.pvlist['dither_level'] = Pv(dither_level[self.name])
       # set up all the matlab PVs
        for k, v in matlab_list.iteritems():  # loop over items
            if not matlab_use[matlab_list[k][0]]: #not overriding on this one, keep older pv.
                continue
            pvname = matlab_pv_base[self.name]+str(matlab_list[k][0]+matlab_pv_offset[self.name]).zfill(matlab_pv_digits[self.name])
            pv_description_field_name = pvname + '.DESC' # name of description field
            pv = Pv(pv_description_field_name)
            pv.connect(timeout)
            pv.put(value= self.name+' '+v[1], timeout=1.0) # put in the description field
            pv.disconnect() # done with this pv
            pv_prec_name = pvname + '.PREC' # precision field
            pv = Pv(pv_prec_name)
            pv.connect(timeout)
            pv.put(value = 4, timeout = 1.0) # set precision field
            pv.disconnect() # done with precision field
            self.pvlist[k]=Pv(pvname) # add pv  to list - this is where matlab woudl overwrite ioc pvs. 
        self.OK = 1   
        for k, v in self.pvlist.iteritems():  # now loop over all pvs to initialize
            try:
                v.connect(timeout) # connect to pv
                v.get(ctrl=True, timeout=1.0) # get data
            except: # for now just fake it
                print('could not open '+v.name)
                print k
                self.OK = 0 # some error with setting up PVs, can't run, will exit  
        self.error_pv = Pv(error_pv_name[self.name]) # open pv
        self.error_pv.connect(timeout)
        self.version_pv = Pv(version_pv_name[self.name])
        self.version_pv.connect(timeout)
        self.version_pv.put(self.version, timeout = 10.0)
        self.E = error_output(self.error_pv)
        self.E.write_error('OK')
       
        
        
        
    def get(self, name):
        try:
            self.pvlist[name].get(ctrl=True, timeout=10.0)
            return self.pvlist[name].value                      
        except:
            print 'PV READ ERROR'
            print name
            return 0
                
                
    def get_last(self, name): # gets last value read, no pv read / write
        return self.pvlist[name].value                
                
    def put(self, name, x):
        try:
            self.pvlist[name].put(x, timeout = 10.0) # long timeout           
        except:
            print 'UNABLE TO WRITE PV'
            print name
            print x
                
    def __del__ (self):
        for v in self.pvlist.itervalues():
            v.disconnect()  
        self.error_pv.disconnect()    
        print 'closed all PV connections'

class locker():  # sets up parameters of a particular locking system
    def __init__(self, P, W):  # Uses PV list
         self.P = P
         self.W = W  # watchdog class
         self.f0 = 0.476  # Reference frequency in GHz
         self.rmin = 56.0 # Divide ratio to 8.5MHz - not really needed
         self.min_f = self.f0 / self.rmin  # 8.5MHz
         self.laser_n = self.rmin / 7 # laser frequency ratio from 8.5MHz
         self.laser_f = self.min_f * self.laser_n # laser frequency
         self.locking_n = self.rmin * 8.0 # locking number ratio to 8.5MHz
         self.locking_f = self.min_f * self.locking_n # 3.8GHz
         self.trigger_n = self.rmin / 4.0  # trigger frequency ratio
         self.trigger_f = self.min_f * self.trigger_n # 119Mhz trigger frequency
         self.calib_points = 50  # number of points to use in calibration cycle
         self.calib_range = 30  # nanoseconds for calibration swe
         self.jump_tol = 0.150  # nanoseconds error to be considered a phase jump
         self.max_jump_error = .05 # nanoseconds too large to be a phase jump
         self.max_frequency_error = 100.0
         self.motor_tolerance = 1
         self.min_time = -880000 # minimum time that can be set (ns) % was 100  %%%% tset
         self.max_time = 20000.0 # maximum time that can be set (ns)
         self.locker_file_name = 'locker_data_' + self.P.name + '.pkl'
         self.timing_buffer = 0.0  # nanoseconds, how close to edge we can go in ns
         self.d = dict()
         self.d['delay'] =  self.P.get('delay')
         self.d['offset'] = self.P.get('offset')
         self.delay_offset = 0  # kludge to avoide running near sawtooth edge
         self.drift_last= 0; # used for drift correction when activated
         self.drift_initialized = False # will be true after first cycle
         self.C = time_interval_counter(self.P) # creates a time interval counter object
    def locker_status(self): # check to see if locker / laser signals are OK, P is a PVS class      
        self.laser_ok = 1 # list of various failure modes
        self.rf_ok = 1
        self.diode_ok = 1
        self.frequency_ok =1
        self.setpoint_ok = 1
        self.lock_ok = 1
        self.message = 'OK' # output error message, OK means no trouble found    
        rfpwr = self.P.get('rf_pwr')  # check RF level
        rfpwrhihi = self.P.get('rf_pwr_hihi')
        rfpwrlolo = self.P.get('rf_pwr_lolo')
        if (rfpwr > rfpwrhihi) | (rfpwr < rfpwrlolo):
            self.message = 'RF power out of range'
            self.laser_ok = 0
            self.rf_ok = 0

        dpwr = self.P.get('diode_pwr') # check diode level
        dpwrhihi = self.P.get('diode_pwr_hihi')
        dpwrlolo = self.P.get('diode_pwr_lolo')
        if (dpwr > dpwrhihi) | (dpwr < dpwrlolo):
            self.message = 'diode power out of range'
            self.laser_ok = 0
            self.rf_diode_ok = 0
        
        if abs(self.P.get('freq_sp') - self.P.get('oscillator_f')) > self.max_frequency_error:  # oscillator set point wrong
            self.laser_ok = 0
            self.frequency_ok = 0
            self.frequency_ok = 0
            self.message = 'frequency set point out of range'
        if not self.P.get('laser_locked'):
            self.message = 'laser not indicating locked'
            self.lock_ok = 0
            self.laser_ok = 0

    def calibrate(self):  # This is the big complicated calibration routine
        M = phase_motor(self.P)  # creates a phase motor control object (PVs were initialized earlier)
        T = trigger(self.P)  # trigger class
        ns = 10000 # number of different times to try for fit - INEFFICIENT - should do Newton's method but too lazy
        self.P.put('busy', 1) # set busy flag
        tctrl = linspace(0, self.calib_range, self.calib_points) # control values to use
        tout = array([]) # array to hold measured time data
        counter_good = array([]) # array to hold array of errors
        t_trig = T.get_ns() # trigger time in nanoseconds
        M.move(0)  # move to zero to start 
        M.wait_for_stop()
        for x in tctrl:  #loop over input array 
            print 'calib start'
            self.W.check() # check watchdog
            print 'post watchdog'
            if self.W.error:
                return    
            if not self.P.get('calibrate'):
                return   # canceled calibration
            print 'move motor'
            M.move(x)  # move motor
            print 'wait for stop'
            M.wait_for_stop()
            print 'sleep'
            time.sleep(2)  #Don't know why this is needed
            t_tmp = 0 # to check if we ever get a good reading
            print 'get read'
            for n in range (0, 25): # try to see if we can get a good reading
                 t_tmp = self.C.get_time()  # read time
                 if t_tmp != 0: # have a new reading
                     break # break out of loop
            tout = append(tout, t_tmp) # read timing and put in array
            print 'end of loop'
            print t_tmp
            print self.C.good
            counter_good = append(counter_good, self.C.good) # will use to filter data
            if not self.C.good:
                print 'bad counter data'
                self.P.E.write_error('timer error, bad data - continuing to calibrate' ) # just for testing
        M.move(tctrl[0])  # return to original position    
        minv = min(tout[nonzero(counter_good)])+ self.delay_offset

        print 'min v is'        
        print minv
        period = 1/self.laser_f # just defining things needed in sawtooth -  UGLY
        delay = minv - t_trig # more code cleanup neded in teh future.
        err = array([]) # will hold array of errors
        offset = linspace(0, period, ns)  # array of offsets to try
        for x in offset:  # here we blindly try different offsets to see what works
            S = sawtooth(tctrl, t_trig, delay, x, period) # sawtooth sim
            err = append(err, sum(counter_good*S.r * (S.t - tout)**2))  # total error
        idx = argmin(err) # index of minimum of error
        print 'offset, delay  trig_time'
        print offset[idx]
        print delay
        print t_trig
        S = sawtooth(tctrl, t_trig, delay, offset[idx], period)
        self.P.put('calib_error', sqrt(err[idx]/ self.calib_points))
        self.d['delay'] = delay
        self.d['offset'] = offset[idx]
        self.P.put('delay', delay)
        self.P.put('offset', offset[idx])
        #print 'PLOTTING CALIBRATION'
        #plot(tctrl, tout, 'bx', tctrl, S.r * S.t, 'r-') # plot to compare
        #plot(tctrl, tout, 'bx', tctrl, S.t, 'r-') # plot to compare
        #plot(tctrl, S.r *(tout - S.t), 'gx')
        #show()
        M.wait_for_stop() # wait for motor to stop moving before exit
        self.P.put('busy', 0)        
        
    def second_calibrate(self):
        print 'starting second calibration - new test'
        M = phase_motor(self.P)  # create phase motor object
        ptime = 30 # seconds between cycles
        tneg = 0.5 # nanoseconds range below current  -2 ok
        tpos = -0.5 # nanoseconds range above current 12 ok
        cycles = 30
        t0 = M.get_position() # current motor position
        tset = array([]) # holds target times
        tread = array([]) # holds readback times
        for n in range(0,cycles-1):  # loop
            t = t0 + tneg + random.random()*(tpos - tneg) # random number in range
            tset = append(tset, t)  # collect list of times
            M.move(t) # move to new position
            time.sleep(ptime)# long wait for now
            tr = 1e9 * self.P.get('secondary_calibration')
            tread = append(tread, tr)
            print n
            print t
            print tr
        M.move(t0) # put motor back    
        print 'done motor move'
        
        
        
        sa = 0.01;
        ca = 0.01;
        param0 = sa,ca
        tdiff = tread - tset - (mean(tread-tset))
        print 'start leastsq'
        fout = leastsq(fitres, param0, args=(tset, tdiff))    
        print 'end leastsq, param ='
        param = fout[0];
        print param
        sa,ca = param
        ttest = array([])
        for nx in range(0,200):
            ttest = append(ttest, t0 + tneg + (nx/200.0)*(tpos-tneg))
        #fitout = ffun(ttest, sa, ca)
        self.P.put('secondary_calibration_s', sa)
        self.P.put('secondary_calibration_c', ca)
        #print 'PLOTTING SECONDARY CALIBRATION'
        #plot(tset, tdiff, 'bx', ttest, fitout, 'r-') # plot to compare
        #show()
        #print 'Done plotting'
        
        
        
        
    def set_time(self): # sets laser to desired time in ns measured by time interval
        t = self.P.get('time')
        if math.isnan(t):
            self.P.E.write_error('desired time is NaN')
            return
        if t < self.min_time or t > self.max_time:
            self.P.E.write_error('need to move TIC trigger')
            return
        t_high = self.P.get('time_hihi')
        t_low = self.P.get('time_lolo')
        if t > t_high:
            t = t_high
        if t < t_low:
            t = t_low
        T = trigger(self.P) # set up trigger
        M = phase_motor(self.P)
        laser_t = t - self.d['offset']  # Just copy workign matlab, don't think!
        nlaser = floor(laser_t * self.laser_f)
        pc = t - (self.d['offset'] + nlaser / self.laser_f)
        pc = mod(pc, 1/self.laser_f)
        ntrig = round((t - self.d['delay'] - (1/self.trigger_f)) * self.trigger_f) # paren was after laser_f
        #ntrig = round((t - self.d['delay'] - (0.5/self.laser_f)) * self.trigger_f) # paren was after laser_f
        trig = ntrig / self.trigger_f

        if self.P.use_drift_correction:
            dc = self.P.get('drift_correction_signal')
            do = self.P.get('drift_correction_offset') 
            dg = self.P.get('drift_correction_gain')
            ds = self.P.get('drift_correction_smoothing')
            self.drift_last = self.P.get('drift_correction_value')
            accum = self.P.get('drift_correction_accum')
            # modified to not use drift_correction_offset or drift_correction_multiplier:
            de  = (dc-do)  # (hopefully) fresh pix value from TT script
            if ( self.drift_initialized ):
                if ( dc <> self.dc_last ):           
                    if ( accum == 1 ): # if drift correction accumulation is enabled
                        #TODO: Pull these limits from the associated matlab PV
                        self.drift_last = self.drift_last + (de- self.drift_last) / ds; # smoothing
                        self.drift_last = max(-.015, self.drift_last) # floor at 15ps
                        self.drift_last = min(.015, self.drift_last)#
                        self.P.put('drift_correction_value', self.drift_last)
                        self.dc_last = dc
            else:
                self.drift_last = de # initialize to most recent reading
                self.drift_last = max(-.015, self.drift_last) # floor at 15ps
                self.drift_last = min(.015, self.drift_last)#
                self.dc_last = dc
                self.drift_initialized = True # will average next time (ugly)    

            pc = pc - dg * self.drift_last; # fix phase control. 

        if self.P.use_secondary_calibration: # make small corrections based on another calibration
            sa = self.P.get('secondary_calibration_s')
            ca = self.P.get('secondary_calibration_c')
            pc = pc - sa * sin(pc * 3.808*2*pi) - ca * cos(pc * 3.808*2*pi) # fix phase

        if self.P.use_dither:
            dx = self.P.get('dither_level') 
            pc = pc + (random.random()-0.5)* dx / 1000 # uniformly distributed random. 

        if self.P.get('enable_trig'): # Full routine when trigger can move
            if T.get_ns() != trig:   # need to move
                T.set_ns(trig) # sets the trigger

        pc_diff = M.get_position() - pc  # difference between current phase motor and desired time        
        if abs(pc_diff) > 1e-6:
            M.move(pc) # moves the phase motor
      
            
  
    def check_jump(self):  # checks trigger and phase shift vs time interval counter for jump
        
        T = trigger(self.P) # trigger class
        M = phase_motor(self.P) # phase motor     
        t = self.C.get_time()
        if t > -900000.0:      
            self.P.put('error', t - self.P.get('time')) # timing error (reads counter)      
        t_trig = T.get_ns()
        pc = M.get_position()
        try:
            self.d['delay'] = self.P.get('delay')
            self.d['offset'] = self.P.get('offset')
        except:
            print 'problem reading delay and offset pvs'
        S = sawtooth(pc, t_trig, self.d['delay'], self.d['offset'], 1/self.laser_f) # calculate time        
        self.terror = t - S.t # error in ns
        self.buckets = round(self.terror * self.locking_f)
        self.bucket_error = self.terror - self.buckets / self.locking_f
        self.exact_error = self.buckets / self.locking_f  # number of ns to move (exactly)
        if (self.C.range > (2 * self.max_jump_error)) or (self.C.range == 0):  # too wide a range of measurements
            self.buckets = 0  # do not count a bucket error if readings are not consistant
            self.P.E.write_error( 'counter not stable')
            return
        if abs(self.bucket_error) > self.max_jump_error:
            self.buckets = 0
            self.P.E.write_error( 'not an integer number of buckets')
        if self.buckets != 0:
            print 'bucket jump - buckets, error'
            print 'buckets'
            print self.buckets
            print self.bucket_error
        self.P.E.write_error( 'Laser OK')      # laser is OK
            
    def fix_jump(self):  # tries to fix the jumps 
        if self.buckets == 0:  #no jump to begin with
            self.P.E.write_error( 'trying to fix non-existant jump')
            return
        if abs(self.bucket_error) > self.max_jump_error:
            self.P.E.write_error( 'non-integer bucket error, cant fix')
            return
        self.P.E.write_error( 'Fixing Jump')
        print'fixing jump'
        M = phase_motor(self.P) #phase control motor
        M.wait_for_stop()  # just ot be sure
        old_pc = M.get_position()
        new_pc = old_pc  - self.exact_error # new time for phase control
        new_pc_fix = mod(new_pc, 1/self.laser_f)  # equal within one cycle. 
        M.move(new_pc_fix) # moves phase motor to new position
        #self.P.put('fix_bucket', 0)  # turn off bucket fix TESTING
        M.wait_for_stop()
        time.sleep(2)  # 
        new_offset = self.d['offset'] - (new_pc_fix - old_pc)
        self.d['offset'] = new_offset
        self.P.put('offset', new_offset)
        self.P.E.write_error( 'Done Fixing Jump')
        bc = self.P.get('bucket_counter') # previous number of jumps
        self.P.put('bucket_counter', bc + 1)  # write incremented number
        print 'jump fix done'
       
            
# t0 is an array of inputs that represent the phase shift time
# t_trig is the EVR trigger time
# delay is the cable length after the trigger
# offset is the dealay from the photodiode to the time interval counter
class sawtooth():  # generates a sawtooth waveform and a vector of OK / notok points for where the fit should be good
        def __init__(self, t0, t_trig, delay, offset, period):  #t0 is a numpy array of input times
            trig_out = t_trig + delay
            laser_t0 = t0 + offset
            tx = trig_out - laser_t0
            nlaser = ceil(tx / period)
            self.t = t0 + offset + nlaser * period
            tr = self.t - trig_out
            self.r = (0.5 + copysign(.5, tr - 0.2 * period)) * (0.5 + copysign(.5, .8 * period - tr)) # no sign function



class ring():  # very simple ring buffer 
    def __init__(self, sz=12):  # sz is size of ring
        self.sz = sz  # hold size of ring
        self.a = array(range(sz))
        self.a = self.a * 0.0  # create an array of zeros
        self.ptr = -1 # points to last data, start negative
        self.full = False # set to true when the ring is full
        
    def add_element(self, x):  # adds element to ring
        self.ptr = mod(self.ptr+1,self.sz)        
        self.a[self.ptr] = x # set this element
        if self.ptr == 7:
            self.full = True

    def get_last_element(self):
        return self.a[self.ptr]       
        
    def get_array(self):
        return self.a
        
 
class time_interval_counter():  # reads interval counter data, gets raw or average as needed
    def __init__(self, P):
        self.scale = 1e9 # scale relative to nanoseconds
        self.P = P
        self.good = 1 
        self.rt = ring() # create a ring buffer to hold data
        self.rt.add_element(self.P.get('counter')) # read first counter value to initialize array
        self.rj = ring() # ring to hold jitter data
        self.rj.add_element(self.P.get('counter_jitter'))
        self.range = 0 # range of data
    def get_time(self):
        self.good = 0  # assume bad unless we fall through all the traps
        self.range = 0; # until we overwrite
        tol = self.P.get('counter_jitter_high')
        tmin = self.P.get('counter_low')
        tmax = self.P.get('counter_high')
        time = self.P.get('counter')  # read counter time
        if time == self.rt.get_last_element: # no new data
            return 0 # no new data
        if (time > tmax) or (time < tmin):
            return 0 # data out of range
        jit = self.P.get('counter_jitter')
        if jit > tol:
            return 0  # jitter too high
        # if we got here, we have a good reading
        self.rt.add_element(time) # add time to ring
        self.rj.add_element(jit)  # add jitter to ring
        self.good = 1
        if self.rt.full:
            self.range = self.scale * (max(self.rt.get_array()) - min(self.rt.get_array()))  # range of measurements
        else:
            self.range = 0  # don't have a full buffer yet
        return time * self.scale

   

class phase_motor():
    def __init__(self, P): # P holds motor PVs (already open)
        self.scale = .001 # motor is in ps, everthing else in ns
        self.P = P
        self.max_tries = 100
        self.loop_delay = 0.1
        self.tolerance = 2e-5  #was 5e-6
        self.position = self.P.get('phase_motor') * self.scale  # get the current position  WARNING logic race potential
        self.wait_for_stop()  # wait until it stops moving

    def wait_for_stop(self):
        for n in range (0, self.max_tries):
            try:
                stopped = self.P.get('phase_motor_dmov') # 1 if stopped, if throws error, is still moving
            except:
                print 'could not get dmov'
                stopped = 0  # threw error, assume not stopped (should clean up to look for epics error)
            if stopped:
                posrb = self.P.get('phase_motor_rb') * self.scale  # position in nanoseconds
                if abs(posrb - self.position) < self.tolerance:  # are we within range
                   break
            time.sleep(self.loop_delay)        

    def move(self, pos): # move motor to new position (no wait).
        #self.P.pvlist['phase_motor'].put(value=pos / self.scale, timeout = 10.0)  # allow long timeout for motor move
        self.P.put('phase_motor', pos/self.scale) # motor move if needed   
        self.position = pos  # requested position in ns
        self.wait_for_stop() # check
         

    def get_position(self):
        self.wait_for_stop() # wait until it stops moving
        self.position = self.scale * self.P.get('phase_motor')  # get position data
        return self.position           
   
class trigger():  # deals with annoying problmes of triggers in ns or ticks
    def __init__ (self, P):  # P is a pv list that includes trigger scaling information
        self.P = P
        if self.P.trig_in_ticks:
            self.scale =1000.0/119.0  # 119MHz, 8 ns ticks 
        else:
            self.scale = 1 # trigger is in ns units
        self.time = self.scale * self.P.get('laser_trigger')    
   
    def get_ns(self):
        tmp = self.P.get('laser_trigger')
        self.time = self.scale * tmp
        return self.time
        
    def set_ns(self,t):
        self.time = t/self.scale
        #self.P.pvlist['laser_trigger'].put(self.time)
        self.P.put('laser_trigger', self.time)
   
  
class error_output():
    def __init__(self, pv): # writes to this string pv (already connected)
        self.pv = pv  # just to keep it here
        self.pv.put(value= 'OK', timeout=1.0)
        self.maxlen = 25 # maxumum error string length
  
    def write_error(self, txt):
        n = len(txt)
        if n > self.maxlen:
            txt = txt[0:self.maxlen]
        self.pv.put(value = txt, timeout = 1.0)

class degrees_s(): # manages time control in degrees S-band
    def __init__(self, P):  #P has the list of PVs
        self.P = P
        self.freq = 2.856  # in GHz
        self.last_time = self.P.get('time') # last time entered in contol
        self.last_deg = self.P.get('deg_Sband') # last degrees sband
        self.last_ns_offset = self.P.get('ns_offset')
        self.last_deg_offset = self.P.get('deg_offset')
        
    def run(self): # checks which changed last. NS given priority
        ns = self.P.get('time')
        deg = self.P.get('deg_Sband')
        ns_offset = self.P.get('ns_offset')
        deg_offset = self.P.get('deg_offset')
        if ns != self.last_time or ns_offset != self.last_ns_offset: # nanoseconds have changed
           deg_new = -1.0*(ns - ns_offset) * self.freq * 360 - deg_offset
           self.last_time = ns
           self.last_ns_offset = ns_offset
           self.last_deg = deg_new
           self.P.put('deg_Sband', deg_new) #write the degrees back
           
        elif deg != self.last_deg or deg_offset != self.last_deg_offset:  #changed degrees
           ns_new = -1.0*(deg + deg_offset)/(self.freq * 360) + ns_offset
           self.last_time = ns_new
           self.last_deg = deg
           self.last_deg_offset = deg_offset
           self.P.put('time', ns_new) 

        else:
            pass




def fitres(param, tin, tout):  # tin isinput time, tout is measured, param is parameters    
    sa,ca = param  # sine and cosine amplitudes
    err= tout - ffun(tin, sa, ca)
    return err
        
def ffun( x, a, b):
    w0 = 3.808*2*pi
    out = a*sin(x * w0) + b * cos(x*w0)
    return out        






def femto(name='NULL'):
    P = PVS(name)
    if P.OK == 0:
        return
    W = watchdog.watchdog(P.pvlist['watchdog'])
    if W.error:
        return
    L = locker(P,W) #set up locking system parameters
    L.locker_status()  # check locking sysetm / laser status
    P.E.write_error( L.message)
    T = trigger(P)
    T.get_ns()
#   C = time_interval_counter(P)  # time interval counter device
    D = degrees_s(P) # manages conversion of degrees to ns and back
#    C.get_time()
    while W.error ==0:   # MAIN PROGRAM LOOP
        pause(0.1)
        try:   # the never give up, never surrunder loop. 
            W.check()
            P.put('busy', 0)
            L.locker_status()  # check if the locking sysetm is OK
            if not L.laser_ok:  # if the laser isn't working, for now just do nothign, eventually suggest fixes
                P.E.write_error( L.message)
                P.put('ok', 0)
                time.sleep(0.5)  # to keep the loop from spinning too fast
                continue            #just try again if the laser isn't ready  
            if P.get('calibrate'):
                P.put('ok', 0)
                P.put('busy', 1) # sysetm busy calibrating
                P.E.write_error( 'calibration requested - starting')
                L.calibrate()
                P.put('calibrate', 0)
                P.E.write_error( ' calibration done')
                continue
            if  P.use_secondary_calibration:  # run calibration against scope
                if P.get('secondary_calibration_enable'): # not requested  
                    P.put('ok', 0)
                    P.put('busy', 1) # sysetm busy calibrating
                    P.E.write_error( 'secondary calibration')
                    L.second_calibrate()
                    P.put('secondary_calibration_enable', 0)
                    P.E.write_error( ' secondary calibration done')
                    continue
                pass
            L.check_jump()   # looks for phase jumps relative to phase control / trigger
            if P.get('fix_bucket') and L.buckets != 0 and P.get('enable'):
                P.put('ok', 0)
                P.put('busy', 1)
                L.fix_jump()  # fixes bucket jumps - careful
            P.put('bucket_error',  L.buckets)
            P.put('unfixed_error', L.bucket_error)
            P.put('ok', 1)
            if P.get('enable'): # is enable time control active?
                L.set_time() # set time read earlier    
            D.run()  # deals with degreees S band conversion    
            #P.E.write_error('Laser OK')
        except:   # catch any otehrwise uncaught error.
            print sys.exc_info()[0] # print error I hope
            del P  #does this work?
            print 'UNKNOWN ERROR, trying again'   
            P = PVS(name)
            W = watchdog.watchdog(P.pvlist['watchdog'])
            L = locker(P, W) #set up locking system parameters
            L.locker_status()  # check locking sysetm / laser status
            P.E.write_error( L.message)
            T = trigger(P)
            T.get_ns()
    P.E.write_error( 'done, exiting')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        femto()  # null input will prompt
    else:
        femto(sys.argv[1])
    

