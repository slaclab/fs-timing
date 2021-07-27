import time
import math
#from pylab import *
import plotly
import numpy
# import watchdog
#from psp.Pv import Pv
from epics import PV as Pv # switching in this lib, doesn't necessarily match online version
import sys
import random  # random number generator for secondary calibration
from scipy.optimize import leastsq # for secondary calibration
from femtoconfig import Config

class PVS():   # creates pvs
    def __init__(self, nx='NULL'):
        #self.config = Config()
        #self.config.readConfig("configs/astagen1.json")
        self.version = 'Watchdog 141126a' # version string
        #self.version = self.config["version"]
        
        
        self.name = nx
        print(self.name)
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
        atca_base = dict() # used for ATCA PV names
        phase_motor = dict()
        laser_trigger = dict()
        trig_in_ticks = dict() # 1 if trigger units are ticks (1/119MHz), 0 if in nanoseconds( kludge for multi systems)
        reverse_counter = dict()  # 1 if the laser starts the counter, trigger stops.        
        error_pv_name = dict()    
        use_secondary_calibration = dict() # use a scope or other device
        is_atca = dict() # holds whether the system is an ATCA system
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
        trig_in_ticks[nm] = 0  # Now using new time invariant triggers
        reverse_counter[nm] = 1  # start / stop reversed for this laser
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new Epics pvs for XPP.
        matlab[nm] = matlab_use    
        use_drift_correction[nm] = False  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)
        

        # ASTA, ATCA Hybrid Edition
        nm = 'ASTA_ATCA'
        namelist.add(nm)
        base = 'OSC:AS01:1:'  # base name for this sysetm
        dev_base[nm] = base  # no separate device base for this one.
        atca_base[nm] = 'OSC:AS01:3:' # ATCA laser locker has this base PV
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base   # time interval counter - no added base to this one.
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = atca_base[nm]+'PHASE_SWEEP' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'TRIG:AS01:RF01:SPARE5:TDES' # this stays the same for ATCA Hybrid Edition
        trig_in_ticks[nm] = 0  # Now using new time invariant triggers
        reverse_counter[nm] = 1  # start / stop reversed for this laser
        use_secondary_calibration[nm] = 0
        is_atca[nm] = 1
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
        is_atca[nm] = 0
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
        
       
        
        while not (self.name in namelist):
            print(self.name + ' not found, please enter one of the following ')
            for x in namelist:
                print(x)
            # self.name = raw_input('enter system name:')                           

        matlab_use = matlab[self.name]
        self.use_secondary_calibration = use_secondary_calibration[self.name]
        try:
            self.is_atca = is_atca[self.name]
        except KeyError: 
            pass
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
        # ASTA ATCA system replaces certain PVs
        try:
            if self.is_atca:
                self.pvlist['lock_enable'] = Pv(atca_base[self.name]+'RF_LOCK_ENABLE')
                self.pvlist['laser_locked'] = Pv(atca_base[self.name]+'PHASE_LOCKED')
                self.pvlist['rf_pwr']= Pv(atca_base[self.name]+'RF_PWR') # RF power readback
                self.pvlist['rf_pwr_lolo']= Pv(atca_base[self.name]+'RF_PWR'+'.LOLO') # RF power readback
                self.pvlist['rf_pwr_hihi']= Pv(atca_base[self.name]+'RF_PWR'+'.HIHI') # RF power readback 
                self.pvlist['diode_pwr'] = Pv(atca_base[self.name]+'DIODE_PWR')
                self.pvlist['diode_pwr_lolo'] = Pv(atca_base[self.name]+'DIODE_PWR'+'.LOLO')
                self.pvlist['diode_pwr_hihi'] = Pv(atca_base[self.name]+'DIODE_PWR'+'.HIHI')
            else:
                self.pvlist['phase_motor_dmov'] = Pv(phase_motor[self.name]+'.DMOV')  # motor motion status
        except AttributeError: 
            self.pvlist['phase_motor_dmov'] = Pv(phase_motor[self.name]+'.DMOV')  # motor motion status
            
       # set up all the matlab PVs
        # for k, v in matlab_list.iteritems():  # loop over items
        #     if not matlab_use[matlab_list[k][0]]: #not overriding on this one, keep older pv.
        #         continue
        #     pvname = matlab_pv_base[self.name]+str(matlab_list[k][0]+matlab_pv_offset[self.name]).zfill(matlab_pv_digits[self.name])
        #     pv_description_field_name = pvname + '.DESC' # name of description field
        #     pv = Pv(pv_description_field_name)
        #     pv.connect(timeout)
        #     pv.put(value= self.name+' '+v[1], timeout=1.0) # put in the description field
        #     pv.disconnect() # done with this pv
        #     pv_prec_name = pvname + '.PREC' # precision field
        #     pv = Pv(pv_prec_name)
        #     pv.connect(timeout)
        #     pv.put(value = 4, timeout = 1.0) # set precision field
        #     pv.disconnect() # done with precision field
        #     self.pvlist[k]=Pv(pvname) # add pv  to list - this is where matlab woudl overwrite ioc pvs. 
        # self.OK = 1   
        # for k, v in self.pvlist.iteritems():  # now loop over all pvs to initialize
        #     try:
        #         v.connect(timeout) # connect to pv
        #         v.get(ctrl=True, timeout=1.0) # get data
        #     except: # for now just fake it
        #         print('could not open '+v.name)
        #         print(k)
        #         self.OK = 0 # some error with setting up PVs, can't run, will exit  
        # self.error_pv = Pv(error_pv_name[self.name]) # open pv
        # self.error_pv.connect(timeout)
        # self.version_pv = Pv(version_pv_name[self.name])
        # self.version_pv.connect(timeout)
        # self.version_pv.put(self.version, timeout = 10.0)
        # self.E = error_output(self.error_pv)
        # self.E.write_error('OK')
       
    def get(self, name):
        try:
            self.pvlist[name].get(ctrl=True, timeout=10.0)
            return self.pvlist[name].value                      
        except:
            print('PV READ ERROR')
            print(name)
            return 0
                         
    def get_last(self, name): # gets last value read, no pv read / write
        return self.pvlist[name].value                
                
    def put(self, name, x):
        try:
            self.pvlist[name].put(x, timeout = 10.0) # long timeout           
        except:
            print('UNABLE TO WRITE PV')
            print(name)
            print(x)
                
    def __del__ (self):
        for v in self.pvlist.itervalues():
            v.disconnect()  
        self.error_pv.disconnect()    
        print('closed all PV connections')
