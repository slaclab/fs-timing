""" Concrete subclass of the LaserLocker object designed for operation with
primarily Amplitude Tangerine lasers running ATCA hardware.
"""

import time
import math
import pdb
from collections import *

import numpy as np
from scipy import optimize
import scipy

from support.laserlockerversions.LaserLocker import LaserLocker
from ..tic.TimeIntervalCounter import TimeIntervalCounter
from ..Trigger import Trigger
from ..PhaseMotor import PhaseMotor
from ..Sawtooth import Sawtooth
from support.EventSystem import EventSystem

def err(inputs,x,times,trig):
    """ Error function for fitting.
    
    Arguments:
        inputs : effectively a lambda function argument
        x : array index data
        times : 
        trig :
    """

    S = Sawtooth(x,trig,inputs[0],inputs[1],inputs[2])
    res = sum((S.t - times)**2.0)
    return res

class LaserLocker(LaserLocker):
    """Gen 2 Laser locker object, inheriting from generalized LaserLocker object."""
    def __init__(self,errorLog,pvs,watchdog):
        super().__init__(errorLog,pvs,watchdog)
        self.f0 = 1.3  # Reference frequency in GHz
        self.rmin = 196.0 # Divide ratio to 46.429 MHz - not really needed
        self.min_f = self.f0 / self.rmin  # 46.429 MHz
        self.laser_n = 7 
        self.laser_f = self.min_f * self.laser_n / 50.0 # laser frequency
        self.ppPeriod = 1/self.laser_f # pulse picker period
        self.locking_n = self.rmin * 8.0 # locking number ratio to 8.5MHz
        self.locking_f = self.laser_f
        self.trigger_n = self.rmin / 4.0  # trigger frequency rati
        self.trigger_f = 1.0
        self.calib_points = 120  # number of points to use in calibration cycle
        self.calib_range = 1200  # nanoseconds for calibration sweep, 1.4x PulsePicker period
        self.jump_tol = 0.150  # nanoseconds error to be considered a phase jump
        self.max_jump_error = 22.0 # nanoseconds too large to be a phase jump
        self.max_frequency_error = 100.0
        self.motor_tolerance = 1
        self.min_time = -880000 # minimum time that can be set (ns) % was 100  %%%% tset
        self.max_time = 20000.0 # maximum time that can be set (ns)
        self.locker_file_name = 'locker_data_' + self.P.name + '.pkl'
        self.timing_buffer = 0.0  # nanoseconds, how close to edge we can go in ns
        T = Trigger(self.P)
        self.initTPR = T.get_ns()
        self.d = dict()
        self.d['delay'] =  self.P.get('delay')
        self.d['offset'] = self.P.get('offset')
        self.delay_offset = 0  # kludge to avoide running near sawtooth edge
        self.drift_last= 0; # used for drift correction when activated
        self.drift_initialized = False # will be true after first cycle
        self.C = TimeIntervalCounter(self.P) # creates a time interval c
        self.phasescale = 2856.0/2600.0 # here until IOC edited

    def locker_status(self):
        """ Check state of locker."""
        status = super().locker_status()
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
            self.message = 'RF power out of range\n'
            self.laser_ok = 0
            self.rf_ok = 0

        dpwr = self.P.get('diode_pwr') # check diode level
        dpwrhihi = self.P.get('diode_pwr_hihi')
        dpwrlolo = self.P.get('diode_pwr_lolo')
        if (dpwr > dpwrhihi) | (dpwr < dpwrlolo):
            self.message = 'diode power out of range\n'
            self.laser_ok = 0
            self.rf_diode_ok = 0
        
        if abs(self.P.get('freq_sp') - self.P.get('oscillator_f')) > self.max_frequency_error:  # oscillator set point wrong
            self.laser_ok = 0
            self.frequency_ok = 0
            self.frequency_ok = 0
            self.message = 'frequency set point out of range\n'
        if not self.P.get('laser_locked'):
            self.message = 'laser not indicating locked\n'
            self.lock_ok = 0
            self.laser_ok = 0
        if not self.laser_ok:
            self.E.write_error({'value':self.message,'lvl':1})
        status = status & self.laser_ok
        self.P.put('ok',status)
        return status

    def set_time(self):
        """ Basic move function. 
        
        This function is the core move command for the laser locker, used by higher level functions.
        """
        #pdb.set_trace()
        targetTime = self.P.get('time') # FS_TGT_TIME
        if math.isnan(targetTime):
            # A holdover from the matlab days, in for backwards compat.
            self.P.E.write_error({"value":'desired time is NaN',"lvl":2})
            return
        if targetTime < self.min_time or targetTime > self.max_time:
            self.P.E.write_error({"value":'need to move TIC trigger',"lvl":2})
            return
        t_high = self.P.get('time_hihi')
        t_low = self.P.get('time_lolo')
        T = Trigger(self.P) # set up trigger
        M = PhaseMotor(self.P)
        laser_tdes = targetTime - self.d['delay']-100.0 # might need to be + delay
        nlaser = np.floor(targetTime/self.ppPeriod) # chop off the nanoseconds first
        pc = self.wrapOscillator(targetTime - self.d['offset'])
        pc = pc/self.phasescale
        # trig = self.initTPR + 1012.0* nlaser / self.trigger_f
        #pdb.set_trace()
      
        if self.P.get('enable_trig'): # Full routine when trigger can move
            T.set_ns(laser_tdes)
            self.P.E.write_error({'value':"moving Trigger: %f"%(laser_tdes),"lvl":2})

        pc_diff = M.get_position() - pc  # difference between current phase motor and desired time        
        if abs(pc_diff) > 1e-9:
            self.P.E.write_error({'value':"proposed phase: %f"%(pc),"lvl":2})
            print("proposed phase: %f"%(pc))
            M.move(pc) # moves the phase motor

    def calibrate(self,report=True):
        """ Sweep fine resolution laser phase to detect the edges of pulse
        picker periods. Some elements of this function are hold-overs from the
        first generation code to maintain some amount of consistency between
        them.

        Arguments:
            report : boolean to control whether output from calibration is presented
        """

        #pdb.set_trace()
        eventSystem = EventSystem()
        accStatusCheck = eventSystem.validate()
        if not accStatusCheck:
            self.P.E.write_error({"value":'Calibration: Machine Invalid',"lvl":2})
            self.P.put('find_beam_ctl',-1)
            return
        self.P.E.write_error({"value":'Calibration: Machine config valid; increasing TWID',"lvl":2})
        M = PhaseMotor(self.P)  # phase motor reference
        T = Trigger(self.P)  # trigger config reference
        T.set_width(1200)
        ns = 10000 # number of different times to try for fit - INEFFICIENT - should do Newton's method but too lazy
        self.P.put('busy', 1) # set busy flag
        tctrl = np.linspace(0, self.calib_range, self.calib_points) # control values to use
        tout = np.array([]) # array to hold measured time data
        counter_good = np.array([]) # array to hold array of errors
        t_trig = T.get_ns() # trigger time in nanoseconds
        M.move(0)  # 1. move to zero to start 
        stability_wait = deque([],4)
        print(self.C.get_time())
        stability_wait.append(self.C.get_time())
        time.sleep(2.0)
        stable_pass = False
        while not stable_pass:
            t_check = self.C.get_time()
            stab_mean = np.average(stability_wait) # boxcar average by virtue of deque
            print("%f,%f"%(stab_mean,stability_wait[0]))
            if (stab_mean -t_check)/stab_mean <= 0.1: # hand-wave value for now
                stable_pass = True
            stability_wait.append(t_check)
            time.sleep(2.0)
        M.wait_for_stop()
        time_ZeroPhi_afterTrig = self.C.get_time()
        delay_val = time_ZeroPhi_afterTrig - T.get_ns()
        # pdb.set_trace()
        self.d['delay'] = delay_val
        self.P.put('delay', delay_val)
        self.d['offset'] = time_ZeroPhi_afterTrig
        self.P.put('offset', time_ZeroPhi_afterTrig)
        T.set_width(400)

    def check_jump(self):
        """ Gen 2 implementation of bucket jump detection."""
        self.P.E.write_error({'value':'jump detect',"lvl":2})
        T = Trigger(self.P) # trigger class
        self.P.E.write_error({'value':'setup phase motor',"lvl":2})
        M = PhaseMotor(self.P) # phase motor
        self.P.E.write_error({'value':'counter time',"lvl":2})  
        t = self.C.get_time()
        if t > -900000.0:      
            self.P.put('error', t - self.P.get('time')) # timing error (reads counter)      
        self.P.E.write_error({'value':'get trigger time',"lvl":2})
        self.terror = t-self.P.get('time') # error between target time and readback time
        try:
            self.P.E.write_error({'value':'get delay and offset PVs',"lvl":2})
            self.d['delay'] = self.P.get('delay')
            self.d['offset'] = self.P.get('offset')
        except:
            self.P.E.write_error({'value':'jump detect: problem reading delay and offset PVs',"lvl":1})
        if np.abs(self.terror) < 21.0:
            self.buckets = 0
            self.bucket_error = 0
            return
        t_trig = T.get_ns()
        self.P.E.write_error({'value':'get motor pos',"lvl":2})
        pc = M.get_position()
        #pdb.set_trace()
        

        S = Sawtooth(pc, t_trig, self.d['delay'], self.d['offset'], 1/self.laser_f) # calculate time        
        
        # self.terror = t - S.t # error in ns
        # self.terror = t-self.d['offset']
        # self.terror = t-self.P.get('time')
        # self.buckets = round(self.terror * self.locking_f)
        self.buckets = np.mod(round(self.terror*self.laser_f*47),47)
        # self.bucket_error = self.terror - self.buckets / self.locking_f
        self.bucket_error = self.terror - self.buckets / (self.laser_f*47)
        # self.exact_error = self.buckets / self.locking_f  # number of ns to move (exactly)
        self.exact_error = self.buckets / (self.laser_f*47)
        if (self.C.range > (2 * self.max_jump_error)) or (self.C.range == 0):  # too wide a range of measurements
            self.buckets = 0  # do not count a bucket error if readings are not consistant
            self.E.write_error({'value':u"counter not stable",'lvl':2})
            return
        # if abs(self.bucket_error) > self.max_jump_error:
        #     self.buckets = 0
        #     self.E.write_error({'value':u"not an integer number of buckets",'lvl':2})
        if self.buckets != 0:
            print('bucket jump - buckets, error')

           # pdb.set_trace()
            print('buckets')

            print(self.buckets)
            print(self.bucket_error)
        self.E.write_error({'value':u"Laser OK",'lvl':2})

    def fix_jump(self):
        """ Gen 2 bucket correction."""
        if self.buckets == 0:  #no jump to begin with
            self.P.E.write_error({"value":'trying to fix non-existant jump',"lvl":2})
            return
        # if abs(self.bucket_error) > self.max_jump_error:
        #     self.P.E.write_error( 'non-integer bucket error, cant fix')
        #     return
        self.P.E.write_error({'value':"Fixing Jump...","lvl":2})
        # print('fixing jump')
        M = PhaseMotor(self.P) #phase control motor
        M.wait_for_stop()  # just ot be sure
        old_pc = M.get_position()
        new_pc = old_pc - self.exact_error # new time for phase control
        wrapped_pc = self.wrapOscillator(new_pc)
        new_pc_fix = np.mod(new_pc, 1/(self.laser_f*47.0))  # equal within one cycle. 
        # M.move(new_pc_fix) # moves phase motor to new position
        M.move(wrapped_pc) # moves phase motor to new position
        #self.P.put('fix_bucket', 0)  # turn off bucket fix TESTING
        M.wait_for_stop()
        time.sleep(2)  # 
        # new_offset = self.d['offset'] - (new_pc_fix - old_pc)
        new_offset = self.d['offset'] - (wrapped_pc - old_pc)
        self.d['offset'] = new_offset
        self.P.put('offset', new_offset)
        T = Trigger(self.P) # set up trigger
        t = T.get_ns()
        laser_t = t - self.d['offset'] - self.d['delay'] - 64.0
        T.set_ns(laser_t)
        self.P.E.write_error({"value":'Done Fixing Jump',"lvl":2})
        bc = self.P.get('bucket_counter') # previous number of jumps
        self.P.put('bucket_counter', bc + 1)  # write incremented number
        print('jump fix done')
        time.sleep(2)

    def wrapOscillator(self,intime):
        """ Correct oscillator phase to avoid excessive moves.
        
        wrap oscillator phase around max pulse picker rate to keep it from
        moving very far distances. Protects against bad calculations and keeps
        the response faster without increasing locker slew rate.
        
        Arguments:
            intime : input time to mod
        """

        outtime = intime
        while outtime < 0 or outtime >= self.ppPeriod:
            if outtime < 0:
                outtime +=  self.ppPeriod
            elif outtime >= self.ppPeriod:
                outtime -= self.ppPeriod
        return outtime

    def wrapOscillatorAndTrig(self,intime,intrig):
        """ Wrap oscillator and trigger times around pulse picker rate
        
        wrap oscillator phase and trigger time around max pulse picker rate to keep it from
        moving very far distances. Protects against bad calculations and keeps
        the response faster without increasing locker slew rate.
        
        Arguments:
            intime : input time for oscillator
            intrig : TPR TDES for AOM
        """

        outtime = intime
        outtrig = intrig
        while outtime < 0 or outtime >= self.ppPeriod:
            if outtime < 0:
                outtime +=  self.ppPeriod
                outtrig -= self.ppPeriod
            elif outtime >= self.ppPeriod:
                outtime -= self.ppPeriod
                outtrig =+ self.ppPeriod
        return outtime,outtrig

    def findBeam(self):
        """ Adjust trigger parameters to insure a pulse will be emitted.
        
        Sweeps trigger parameters to locate a laser pulse in the event that the
        oscillator phase has put the beam outside of the trigger width that is
        other wise needed for operation. Much of the logic for determining
        whether this function can proceed is duplicated in the calibration
        routines, for reference. This applies, so far, only to Amplitude
        Tangerines.
        
        Caution should be exercised when using this function, as it is possible
        to end up with an undefined (at best) trigger state if the allowed power
        class is highter than what is expected.
        """

        beamFindState = self.P.get("find_beam_ctl")
        T = Trigger(self.P)
        if beamFindState == 1:
            self.P.E.write_error({"value":'Beam Find Requested...',"lvl":2})
            self.P.put("find_beam_ctl",1)
            #Check logic conditions for whether proceeding is okay
            eventSystem = EventSystem()
            accStatusCheck = eventSystem.validate()
            if not accStatusCheck:
                self.P.E.write_error({"value":'Beam Find: Machine Invalid',"lvl":2})
                self.P.put('find_beam_ctl',-1)
                return
            self.P.E.write_error({"value":'Beam Find: Machine config valid; increasing TWID',"lvl":2})
            T.set_width(1200)
        elif beamFindState == 2:
            self.P.E.write_error({"value":'Restoring TWID...',"lvl":2})
            self.P.put("find_beam_ctl",0)
            T.set_width(400)
        elif beamFindState == -1:
            self.P.E.write_error({"value":'Clearing Beam Find error',"lvl":2})
            self.P.put("find_beam_ctl",0)
