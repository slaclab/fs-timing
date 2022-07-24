from support.laserlockerversions.LaserLocker import LaserLocker
from ..TimeIntervalCounter import TimeIntervalCounter
from ..Trigger import Trigger
from ..PhaseMotor import PhaseMotor
from ..Sawtooth import Sawtooth
import numpy as np
from scipy import optimize
import scipy
import time
import math
import pdb
from collections import *

def err(inputs,x,times,trig):
    """ Error function for fitting."""
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
        self.laser_f = self.min_f * self.laser_n / 47.0 # laser frequency
        self.ppPeriod = 1/self.laser_f # pulse picker period
        self.locking_n = self.rmin * 8.0 # locking number ratio to 8.5MHz
        #self.locking_f = self.min_f * self.locking_n # 3.8GHz
        self.locking_f = self.laser_f
        self.trigger_n = self.rmin / 4.0  # trigger frequency ratio
        #self.trigger_f = self.min_f * self.trigger_n # 119Mhz trigger frequency
        self.trigger_f = 1.0
        self.calib_points = 200  # number of points to use in calibration cycle
        self.calib_range = 2400  # nanoseconds for calibration sweep, 1.4x PulsePicker period
        self.jump_tol = 0.150  # nanoseconds error to be considered a phase jump
        self.max_jump_error = 22.0 # nanoseconds too large to be a phase jump
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
        self.C = TimeIntervalCounter(self.P) # creates a time interval c
        self.phasescale = 1.0981 # here until IOC edited

    def locker_status(self):
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
        t = self.P.get('time') # FS_TGT_TIME
        if math.isnan(t):
            # A holdover from the matlab days, in for backwards compat.
            self.P.E.write_error({"value":'desired time is NaN',"lvl":2})
            return
        if t < self.min_time or t > self.max_time:
            self.P.E.write_error({"value":'need to move TIC trigger',"lvl":2})
            return
        t_high = self.P.get('time_hihi')
        t_low = self.P.get('time_lolo')
        # These typically won't be set with a new IOC, so it will keep moves
        # from occurring...
        # if t > t_high:
        #     t = t_high
        # if t < t_low:
        #     t = t_low
        T = Trigger(self.P) # set up trigger
        M = PhaseMotor(self.P)
        laser_t = t - self.d['delay']-self.d['offset']
        nlaser = np.floor(laser_t) # chop off the nanoseconds first
        # nlaser = np.floor(laser_t * self.laser_f)
        # pc = (t - ((self.d['offset'])+self.d['delay'])/1000.0)*self.phasescale # ..what's left can be done with the oscillator phase
        # pc = ((t -
        # self.d['offset'])*1000.0-(t-self.d['offset']))/1000.0*self.phasescale
        pc = self.wrapOscillator(t - self.d['offset']-self.d['delay'])/self.phasescale
        # temporary fix
        # pc = 0.8299*pc+106559.0
        # wrap the phase around to minimize movement from arbitrary phase shifter home
        #pdb.set_trace()
        # while pc > 1000.0/(2.0*self.laser_f) or pc < -1000.0/(2.0*self.laser_f):
        #     if pc >= 1000.0/(2.0*self.laser_f):
        #         pc = pc - 1000.0/self.laser_f
        #     if pc < -1000.0/(2.0*self.laser_f):
        #         pc = pc + 1000.0/self.laser_f
        # pc = t - (self.d['offset'] + nlaser / self.laser_f)
        # pc = np.mod(pc, 1/self.laser_f)
        # ntrig = round((t - self.d['delay'] - (1/self.trigger_f)) * self.trigger_f) # paren was after laser_f
        #ntrig = round((t - self.d['delay'] - (0.5/self.laser_f)) * self.trigger_f) # paren was after laser_f
        trig = nlaser / self.trigger_f
        #pdb.set_trace()
        if self.P.config.use_drift_correction:
            dc = self.P.get('drift_correction_signal')*1.0e-6 # TODO need to convert this to a configuration/control parameter
            do = self.P.get('drift_correction_offset') 
            dg = self.P.get('drift_correction_gain')
            ds = self.P.get('drift_correction_smoothing')
            self.drift_last = self.P.get('drift_correction_value')
            accum = self.P.get('drift_correction_accum')
            # modified to not use drift_correction_offset or drift_correction_multiplier:
            de  = (dc-do)  # (hopefully) fresh pix value from TT script
            if ( self.drift_initialized ):
                if ( dc != self.dc_last ):           
                    if ( accum == 1 ): # if drift correction accumulation is enabled
                        #TODO: Pull these limits from the associated matlab PV
                        self.drift_last = self.drift_last + (de- self.drift_last) / ds; # smoothing
                        self.drift_last = max(-.015, self.drift_last) # floor at 15ps
                        self.drift_last = min(.015, self.drift_last)#
                        self.P.put('drift_correction_value', self.drift_last)
                        self.dc_last = dc
            else:
                self.drift_last = de # initialize to most recent reading
                # TODO I needed to comment these to get the live code working,
                #but if the units are scaled correctly, shouldn't be a problem
                #self.drift_last = max(-.015, self.drift_last) # floor at 15ps
                #self.drift_last = min(.015, self.drift_last)#
                self.dc_last = dc
                self.drift_initialized = True # will average next time (ugly)    

            pc = pc - dg * self.drift_last; # fix phase control. 

        if self.P.config.use_secondary_calibration: # make small corrections based on another calibration
            sa = self.P.get('secondary_calibration_s')
            ca = self.P.get('secondary_calibration_c')
            pc = pc - sa * np.sin(pc * 3.808*2*np.pi) - ca * np.cos(pc * 3.808*2*np.pi) # fix phase

        if self.P.config.use_dither:
            dx = self.P.get('dither_level') 
            pc = pc + (np.random.random()-0.5)* dx / 1000 # uniformly distributed random. 

        if self.P.get('enable_trig'): # Full routine when trigger can move
            if T.get_ns()-2.0 != trig-2.0:   # need to move
                T.set_ns(trig-2.0) # sets the trigger
                self.P.E.write_error({'value':"proposed Trigger: %f"%(trig-2.0),"lvl":2})
                # print("proposed Trigger: %f"%(trig-2.0))

        pc_diff = M.get_position() - pc  # difference between current phase motor and desired time        
        if abs(pc_diff) > 1e-6:
            self.P.E.write_error({'value':"proposed phase: %f"%(pc),"lvl":2})
            print("proposed phase: %f"%(pc))
            M.move(pc) # moves the phase motor

    

    def calibrate(self,report=True):
        """ Sweep fine resolution laser phase to detect the edges of pulse
        picker periods. Some elements of this function are hold-overs from the
        first generation code to maintain some amount of consistency between
        them.
        """
        #pdb.set_trace()
        M = PhaseMotor(self.P)  # phase motor reference
        T = Trigger(self.P)  # trigger config reference
        ns = 10000 # number of different times to try for fit - INEFFICIENT - should do Newton's method but too lazy
        self.P.put('busy', 1) # set busy flag
        tctrl = np.linspace(0, self.calib_range, self.calib_points) # control values to use
        tout = np.array([]) # array to hold measured time data
        counter_good = np.array([]) # array to hold array of errors
        t_trig = T.get_ns() # trigger time in nanoseconds
        M.move(0)  # 1. move to zero to start 
        stability_wait = deque([],4)
        stability_wait.append(self.C.get_time())
        time.sleep(2.0)
        stable_pass = False
        while not stable_pass:
            t_check = self.C.get_time()
            stab_mean = np.average(stability_wait) # boxcar average by virtue of deque
            if (stab_mean -t_check)/stab_mean <= 0.05: # hand-wave value for now
                stable_pass = True
            stability_wait.append(t_check)
            time.sleep(2.0)
        M.wait_for_stop()
        # pdb.set_trace()
        self.d['delay'] = stab_mean
        self.P.put('delay', stab_mean)
        # # 2. Find the trigger edge
        # previous = self.C.get_time()
        # for t_step in np.arange(t_trig,t_trig+1012,1):
        #     T.set_ns(t_step)
        #     jump_check = self.C.get_time()
        #     if (jump_check - previous) < 1012.0:
        #         stability_wait.append(jump_check)
        #     else:
        #         t_edge = t_step # we jumped greater than 3 sigma, consider this the trigger edge
        #         T.set_ns(t_trig)
        #         break
        #     time.sleep(0.2)
        # 3. Sweep oscillator to find the pulse picker edges, starting from
        #    whatever 0 nominal phase is for the oscilator bucket we are in
        for x in tctrl:  #loop over input array 
            # print('calib start')
            print('Oscillator sweep')
            self.W.check() # check watchdog
            print('post watchdog')

            if self.W.error:
                return    
            if not self.P.get('calibrate'):
                return   # canceled calibration
            print('move motor')

            M.move(x)  # move motor
            print('wait for stop')

            M.wait_for_stop()
            print('sleep')

            time.sleep(2.2)
            t_tmp = 0 # to check if we ever get a good reading
            print('get read')
           # pdb.set_trace()
            for n in range (0, 25): # try to see if we can get a good reading
                 t_tmp = self.C.get_time()  # read time
                 if t_tmp != 0: # have a new reading
                     break # break out of loop
            tout = np.append(tout, t_tmp) # read timing and put in array
            print('end of loop')

            print(t_tmp)
            print(self.C.good)
            counter_good = np.append(counter_good, self.C.good) # will use to filter data
            if not self.C.good:
                print('bad counter data')

                self.P.E.write_error({"value":'timer error, bad data - continuing to calibrate',"lvl":2}) # just for testing
        # pdb.set_trace()
        M.move(tctrl[0])  # return to original position    
        #pdb.set_trace()
        index_range = np.floor(1050/(self.calib_range/self.calib_points))
        minv_index = np.argmin(tout[np.nonzero(counter_good)])
        maxv_index = np.argmax(tout[minv_index:minv_index+int(index_range)]*np.nonzero(counter_good[minv_index:minv_index+int(index_range)]))+minv_index
        minv = tout[minv_index]+ self.delay_offset
        maxv = tout[maxv_index]+ self.delay_offset
        input_phase_min = tctrl[minv_index]
        input_phase_max = tctrl[maxv_index]
        # calculate phase scaling
        self.phasescale = (maxv-minv)/(input_phase_max-input_phase_min)
        print("Calculated phase scaling: %f"%(self.phasescale))
        print('min v is: %f'%(minv))
        # print(minv)
        period = 1/self.laser_f # just defining things needed in sawtooth -  UGLY
        delay = minv - t_trig # more code cleanup neded in teh future.
        calerr = np.array([]) # will hold array of errors
        offset = np.linspace(0, period, ns)  # array of offsets to try
        for x in offset:  # here we blindly try different offsets to see what works
            S = Sawtooth(tctrl, t_trig, delay, x, period) # sawtooth sim
            calerr = np.append(calerr, sum(counter_good*S.r * (S.t - tout)**2))  # total error
        idx = np.argmin(calerr) # index of minimum of error
        print('offset, delay  trig_time')

        print(offset[idx])
        print(delay)
        print(t_trig)

        print("alt version")
        res = optimize.differential_evolution(err,bounds=((0,1015),(0,1015),(1000,1014)),args=(tctrl,tout,t_trig),mutation=1.2,tol=0.0001,atol=0.000000001)
        S = Sawtooth(tctrl, t_trig, delay, offset[idx], period) # Create Sawtooth based on the optimized values
        with open('calresults.md','w') as fp:
            fp.write("original cal\n")
            fp.write("delay: %f, offset: %f\n"%(delay,offset[idx]))
            fp.write("new cal\n")
            fp.write("t_trig: %f\ndelay: %f\noffset: %f\nperiod: %f\n---\nfun: %f\n"%(t_trig,res.x[0],res.x[1],res.x[2],res.fun))
        # np.savetxt("caldata.csv",np.stack((tctrl,tout),axis=-1),delimiter=',')
        self.P.put('calib_error', np.sqrt(calerr[idx]/ self.calib_points))
        # self.d['delay'] = delay
        self.d['offset'] = offset[idx]
        # self.P.put('delay', delay)
        self.P.put('offset', offset[idx])
        #print('PLOTTING CALIBRATION')

        #plot(tctrl, tout, 'bx', tctrl, S.r * S.t, 'r-') # plot to compare
        #plot(tctrl, tout, 'bx', tctrl, S.t, 'r-') # plot to compare
        #plot(tctrl, S.r *(tout - S.t), 'gx')
        #show()
        # pdb.set_trace()
        M.wait_for_stop() # wait for motor to stop moving before exit
        self.P.put('busy', 0)

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

    def fix_jump(self):  # tries to fix the jumps 
        if self.buckets == 0:  #no jump to begin with
            self.P.E.write_error({"value":'trying to fix non-existant jump',"lvl":"2"})
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
        laser_t = t - self.d['offset'] # - self.d['delay']
        T.set_ns(laser_t)
        self.P.E.write_error({"value":'Done Fixing Jump',"lvl":2})
        bc = self.P.get('bucket_counter') # previous number of jumps
        self.P.put('bucket_counter', bc + 1)  # write incremented number
        print('jump fix done')
        time.sleep(2)

    def wrapOscillator(self,intime):
        """ wrap oscillator phase around max pulse picker rate to keep it from
        moving very far distances. Protects against bad calculations and keeps
        the response faster without increasing locker slew rate."""
        outtime = intime
        while outtime < 0 or outtime >= self.ppPeriod:
            if outtime < 0:
                outtime +=  self.ppPeriod
            elif outtime >= self.ppPeriod:
                outtime -= self.ppPeriod
        return outtime
