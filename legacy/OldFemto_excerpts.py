# class PVS():   # creates pvs
#     """ This is the base class that organizes the PVs for operation of the code.
#     It has been propagated forward to use the external configuration object"""
#     def __init__(self, configfpath='femto_config.json'):
#         self.config = Config()
#         self.config.readConfig(configfpath)
#         self.config.expandPVs()
#         # self.version = 'Watchdog 141126a' # version string
#         self.version = self.config.version
#         self.name = self.config.name
#         print(self.name)
#         timeout = self.config.timeout

#        # set up all the matlab PVs
#         # for k, v in matlab_list.iteritems():  # loop over items
#         #     if not matlab_use[matlab_list[k][0]]: #not overriding on this one, keep older pv.
#         #         continue
#         #     pvname = matlab_pv_base[self.name]+str(matlab_list[k][0]+matlab_pv_offset[self.name]).zfill(matlab_pv_digits[self.name])
#         #     pv_description_field_name = pvname + '.DESC' # name of description field
#         #     pv = Pv(pv_description_field_name)
#         #     pv.connect(timeout)
#         #     pv.put(value= self.name+' '+v[1], timeout=1.0) # put in the description field
#         #     pv.disconnect() # done with this pv
#         #     pv_prec_name = pvname + '.PREC' # precision field
#         #     pv = Pv(pv_prec_name)
#         #     pv.connect(timeout)
#         #     pv.put(value = 4, timeout = 1.0) # set precision field
#         #     pv.disconnect() # done with precision field
#         #     self.pvlist[k]=Pv(pvname) # add pv  to list - this is where matlab woudl overwrite ioc pvs. 
#         self.OK = 1   
#         for k, v in iter(self.config.pvlist.items()):  # now loop over all pvs to initialize
#             try:
#                 v.connect(timeout) # connect to pv
#                 v.get(with_ctrlvars=True, timeout=1.0) # get data
#             except: # for now just fake it
#                 print('could not open '+v.__str__())
#                 print(k)
#                 self.OK = 0 # some error with setting up PVs, can't run, will exit  
#         self.error_pv = self.config.error_pv
#         self.error_pv.connect(timeout)
#         self.version_pv = self.config.version_pv
#         self.version_pv.connect(timeout)
#         self.version_pv.put(self.version, timeout = 10.0)
#         self.E = error_output(self.error_pv)
#         self.E.write_error('OK')
       
#     def get(self, name):
#         try:
#             self.pvlist[name].get(with_ctrlvars=True, timeout=10.0)
#             return self.pvlist[name].value                      
#         except:
#             print('PV READ ERROR')
#             print(name)
#             return 0
                         
#     def get_last(self, name): # gets last value read, no pv read / write
#         return self.pvlist[name].value                
                
#     def put(self, name, x):
#         try:
#             self.pvlist[name].put(x, timeout = 10.0) # long timeout           
#         except:
#             print('UNABLE TO WRITE PV')
#             print(name)
#             print(x)
                
#     def __del__ (self):
#         for v in self.pvlist.itervalues():
#             v.disconnect()  
#         self.error_pv.disconnect()    
#         print('closed all PV connections')

# class locker():  # sets up parameters of a particular locking system
#     def __init__(self, P, W):  # Uses PV list
#          self.P = P
#          self.W = W  # watchdog class
#          self.f0 = 0.476  # Reference frequency in GHz
#          self.rmin = 56.0 # Divide ratio to 8.5MHz - not really needed
#          self.min_f = self.f0 / self.rmin  # 8.5MHz
#          self.laser_n = self.rmin / 7 # laser frequency ratio from 8.5MHz
#          self.laser_f = self.min_f * self.laser_n # laser frequency
#          self.locking_n = self.rmin * 8.0 # locking number ratio to 8.5MHz
#          self.locking_f = self.min_f * self.locking_n # 3.8GHz
#          self.trigger_n = self.rmin / 4.0  # trigger frequency ratio
#          self.trigger_f = self.min_f * self.trigger_n # 119Mhz trigger frequency
#          self.calib_points = 50  # number of points to use in calibration cycle
#          self.calib_range = 30  # nanoseconds for calibration swe
#          self.jump_tol = 0.150  # nanoseconds error to be considered a phase jump
#          self.max_jump_error = .05 # nanoseconds too large to be a phase jump
#          self.max_frequency_error = 100.0
#          self.motor_tolerance = 1
#          self.min_time = -880000 # minimum time that can be set (ns) % was 100  %%%% tset
#          self.max_time = 20000.0 # maximum time that can be set (ns)
#          self.locker_file_name = 'locker_data_' + self.P.name + '.pkl'
#          self.timing_buffer = 0.0  # nanoseconds, how close to edge we can go in ns
#          self.d = dict()
#          self.d['delay'] =  self.P.get('delay')
#          self.d['offset'] = self.P.get('offset')
#          self.delay_offset = 0  # kludge to avoide running near sawtooth edge
#          self.drift_last= 0; # used for drift correction when activated
#          self.drift_initialized = False # will be true after first cycle
#          self.C = TimeIntervalCounter(self.P) # creates a time interval counter object
    
#     def locker_status(self): # check to see if locker / laser signals are OK, P is a PVS class      
#         self.laser_ok = 1 # list of various failure modes
#         self.rf_ok = 1
#         self.diode_ok = 1
#         self.frequency_ok =1
#         self.setpoint_ok = 1
#         self.lock_ok = 1
#         self.message = 'OK' # output error message, OK means no trouble found    
#         rfpwr = self.P.get('rf_pwr')  # check RF level
#         rfpwrhihi = self.P.get('rf_pwr_hihi')
#         rfpwrlolo = self.P.get('rf_pwr_lolo')
#         if (rfpwr > rfpwrhihi) | (rfpwr < rfpwrlolo):
#             self.message = 'RF power out of range'
#             self.laser_ok = 0
#             self.rf_ok = 0

#         dpwr = self.P.get('diode_pwr') # check diode level
#         dpwrhihi = self.P.get('diode_pwr_hihi')
#         dpwrlolo = self.P.get('diode_pwr_lolo')
#         if (dpwr > dpwrhihi) | (dpwr < dpwrlolo):
#             self.message = 'diode power out of range'
#             self.laser_ok = 0
#             self.rf_diode_ok = 0
        
#         if abs(self.P.get('freq_sp') - self.P.get('oscillator_f')) > self.max_frequency_error:  # oscillator set point wrong
#             self.laser_ok = 0
#             self.frequency_ok = 0
#             self.frequency_ok = 0
#             self.message = 'frequency set point out of range'
#         if not self.P.get('laser_locked'):
#             self.message = 'laser not indicating locked'
#             self.lock_ok = 0
#             self.laser_ok = 0

#     def calibrate(self):  # This is the big complicated calibration routine
#         M = PhaseMotor(self.P)  # creates a phase motor control object (PVs were initialized earlier)
#         T = Trigger(self.P)  # trigger class
#         ns = 10000 # number of different times to try for fit - INEFFICIENT - should do Newton's method but too lazy
#         self.P.put('busy', 1) # set busy flag
#         tctrl = linspace(0, self.calib_range, self.calib_points) # control values to use
#         tout = array([]) # array to hold measured time data
#         counter_good = array([]) # array to hold array of errors
#         t_trig = T.get_ns() # trigger time in nanoseconds
#         M.move(0)  # move to zero to start 
#         M.wait_for_stop()
#         for x in tctrl:  #loop over input array 
#             print('calib start')

#             self.W.check() # check watchdog
#             print('post watchdog')

#             if self.W.error:
#                 return    
#             if not self.P.get('calibrate'):
#                 return   # canceled calibration
#             print('move motor')

#             M.move(x)  # move motor
#             print('wait for stop')

#             M.wait_for_stop()
#             print('sleep')

#             time.sleep(2)  #Don't know why this is needed
#             t_tmp = 0 # to check if we ever get a good reading
#             print('get read')

#             for n in range (0, 25): # try to see if we can get a good reading
#                  t_tmp = self.C.get_time()  # read time
#                  if t_tmp != 0: # have a new reading
#                      break # break out of loop
#             tout = append(tout, t_tmp) # read timing and put in array
#             print('end of loop')

#             print(t_tmp)
#             print(self.C.good)
#             counter_good = append(counter_good, self.C.good) # will use to filter data
#             if not self.C.good:
#                 print('bad counter data')

#                 self.P.E.write_error('timer error, bad data - continuing to calibrate' ) # just for testing
#         M.move(tctrl[0])  # return to original position    
#         minv = min(tout[nonzero(counter_good)])+ self.delay_offset

#         print('min v is')
        
#         print(minv)
#         period = 1/self.laser_f # just defining things needed in sawtooth -  UGLY
#         delay = minv - t_trig # more code cleanup neded in teh future.
#         err = array([]) # will hold array of errors
#         offset = linspace(0, period, ns)  # array of offsets to try
#         for x in offset:  # here we blindly try different offsets to see what works
#             S = sawtooth(tctrl, t_trig, delay, x, period) # sawtooth sim
#             err = append(err, sum(counter_good*S.r * (S.t - tout)**2))  # total error
#         idx = argmin(err) # index of minimum of error
#         print('offset, delay  trig_time')

#         print(offset[idx])
#         print(delay)
#         print(t_trig)
#         S = sawtooth(tctrl, t_trig, delay, offset[idx], period)
#         self.P.put('calib_error', sqrt(err[idx]/ self.calib_points))
#         self.d['delay'] = delay
#         self.d['offset'] = offset[idx]
#         self.P.put('delay', delay)
#         self.P.put('offset', offset[idx])
#         #print('PLOTTING CALIBRATION')

#         #plot(tctrl, tout, 'bx', tctrl, S.r * S.t, 'r-') # plot to compare
#         #plot(tctrl, tout, 'bx', tctrl, S.t, 'r-') # plot to compare
#         #plot(tctrl, S.r *(tout - S.t), 'gx')
#         #show()
#         M.wait_for_stop() # wait for motor to stop moving before exit
#         self.P.put('busy', 0)        
        
#     def second_calibrate(self):
#         print('starting second calibration - new test')

#         M = PhaseMotor(self.P)  # create phase motor object
#         ptime = 30 # seconds between cycles
#         tneg = 0.5 # nanoseconds range below current  -2 ok
#         tpos = -0.5 # nanoseconds range above current 12 ok
#         cycles = 30
#         t0 = M.get_position() # current motor position
#         tset = array([]) # holds target times
#         tread = array([]) # holds readback times
#         for n in range(0,cycles-1):  # loop
#             t = t0 + tneg + random.random()*(tpos - tneg) # random number in range
#             tset = append(tset, t)  # collect list of times
#             M.move(t) # move to new position
#             time.sleep(ptime)# long wait for now
#             tr = 1e9 * self.P.get('secondary_calibration')
#             tread = append(tread, tr)
#             print(n)
#             print(t)
#             print(tr)
#         M.move(t0) # put motor back    
#         print('done motor move')

        
        
        
#         sa = 0.01;
#         ca = 0.01;
#         param0 = sa,ca
#         tdiff = tread - tset - (mean(tread-tset))
#         print('start leastsq')

#         fout = leastsq(fitres, param0, args=(tset, tdiff))    
#         print('end leastsq, param =')

#         param = fout[0];
#         print(param)
#         sa,ca = param
#         ttest = array([])
#         for nx in range(0,200):
#             ttest = append(ttest, t0 + tneg + (nx/200.0)*(tpos-tneg))
#         #fitout = ffun(ttest, sa, ca)
#         self.P.put('secondary_calibration_s', sa)
#         self.P.put('secondary_calibration_c', ca)
#         #print('PLOTTING SECONDARY CALIBRATION')

#         #plot(tset, tdiff, 'bx', ttest, fitout, 'r-') # plot to compare
#         #show()
#         #print('Done plotting')

        
        
        
        
#     def set_time(self): # sets laser to desired time in ns measured by time interval
#         t = self.P.get('time')
#         if math.isnan(t):
#             self.P.E.write_error('desired time is NaN')
#             return
#         if t < self.min_time or t > self.max_time:
#             self.P.E.write_error('need to move TIC trigger')
#             return
#         t_high = self.P.get('time_hihi')
#         t_low = self.P.get('time_lolo')
#         if t > t_high:
#             t = t_high
#         if t < t_low:
#             t = t_low
#         T = Trigger(self.P) # set up trigger
#         M = PhaseMotor(self.P)
#         laser_t = t - self.d['offset']  # Just copy workign matlab, don't think!
#         nlaser = floor(laser_t * self.laser_f)
#         pc = t - (self.d['offset'] + nlaser / self.laser_f)
#         pc = mod(pc, 1/self.laser_f)
#         ntrig = round((t - self.d['delay'] - (1/self.trigger_f)) * self.trigger_f) # paren was after laser_f
#         #ntrig = round((t - self.d['delay'] - (0.5/self.laser_f)) * self.trigger_f) # paren was after laser_f
#         trig = ntrig / self.trigger_f

#         if self.P.use_drift_correction:
#             dc = self.P.get('drift_correction_signal')*1.0e-6 # TODO need to convert this to a configuration/control parameter
#             do = self.P.get('drift_correction_offset') 
#             dg = self.P.get('drift_correction_gain')
#             ds = self.P.get('drift_correction_smoothing')
#             self.drift_last = self.P.get('drift_correction_value')
#             accum = self.P.get('drift_correction_accum')
#             # modified to not use drift_correction_offset or drift_correction_multiplier:
#             de  = (dc-do)  # (hopefully) fresh pix value from TT script
#             if ( self.drift_initialized ):
#                 if ( dc != self.dc_last ):           
#                     if ( accum == 1 ): # if drift correction accumulation is enabled
#                         #TODO: Pull these limits from the associated matlab PV
#                         self.drift_last = self.drift_last + (de- self.drift_last) / ds; # smoothing
#                         self.drift_last = max(-.015, self.drift_last) # floor at 15ps
#                         self.drift_last = min(.015, self.drift_last)#
#                         self.P.put('drift_correction_value', self.drift_last)
#                         self.dc_last = dc
#             else:
#                 self.drift_last = de # initialize to most recent reading
#                 # TODO I needed to comment these to get the live code working, but if the units are scaled correctly, shouldn't be a problem
#                 #self.drift_last = max(-.015, self.drift_last) # floor at 15ps
#                 #self.drift_last = min(.015, self.drift_last)#
#                 self.dc_last = dc
#                 self.drift_initialized = True # will average next time (ugly)    

#             pc = pc - dg * self.drift_last; # fix phase control. 

#         if self.P.use_secondary_calibration: # make small corrections based on another calibration
#             sa = self.P.get('secondary_calibration_s')
#             ca = self.P.get('secondary_calibration_c')
#             pc = pc - sa * sin(pc * 3.808*2*pi) - ca * cos(pc * 3.808*2*pi) # fix phase

#         if self.P.use_dither:
#             dx = self.P.get('dither_level') 
#             pc = pc + (random.random()-0.5)* dx / 1000 # uniformly distributed random. 

#         if self.P.get('enable_trig'): # Full routine when trigger can move
#             if T.get_ns() != trig:   # need to move
#                 T.set_ns(trig) # sets the trigger

#         pc_diff = M.get_position() - pc  # difference between current phase motor and desired time        
#         if abs(pc_diff) > 1e-6:
#             M.move(pc) # moves the phase motor
      
            
  
#     def check_jump(self):  # checks trigger and phase shift vs time interval counter for jump
#         print('jump detect') 
#         T = Trigger(self.P) # trigger class
#         print('setup phase motor')
#         M = PhaseMotor(self.P) # phase motor     
#         print('self.C.get_time')
#         t = self.C.get_time()
#         if t > -900000.0:      
#             self.P.put('error', t - self.P.get('time')) # timing error (reads counter)      
#         print('get trigger time')
#         t_trig = T.get_ns()
#         print('got trigger time')
#         print('get motor pos')
#         pc = M.get_position()
#         try:
#             print('get delay and offset pvs')
#             self.d['delay'] = self.P.get('delay')
#             self.d['offset'] = self.P.get('offset')
#         except:
#             print('problem reading delay and offset pvs')

#         S = sawtooth(pc, t_trig, self.d['delay'], self.d['offset'], 1/self.laser_f) # calculate time        
#         self.terror = t - S.t # error in ns
#         self.buckets = round(self.terror * self.locking_f)
#         self.bucket_error = self.terror - self.buckets / self.locking_f
#         self.exact_error = self.buckets / self.locking_f  # number of ns to move (exactly)
#         if (self.C.range > (2 * self.max_jump_error)) or (self.C.range == 0):  # too wide a range of measurements
#             self.buckets = 0  # do not count a bucket error if readings are not consistant
#             self.P.E.write_error( 'counter not stable')
#             return
#         if abs(self.bucket_error) > self.max_jump_error:
#             self.buckets = 0
#             self.P.E.write_error( 'not an integer number of buckets')
#         if self.buckets != 0:
#             print('bucket jump - buckets, error')

#             print('buckets')

#             print(self.buckets)
#             print(self.bucket_error)
#         self.P.E.write_error( 'Laser OK')      # laser is OK
            
#     def fix_jump(self):  # tries to fix the jumps 
#         if self.buckets == 0:  #no jump to begin with
#             self.P.E.write_error( 'trying to fix non-existant jump')
#             return
#         if abs(self.bucket_error) > self.max_jump_error:
#             self.P.E.write_error( 'non-integer bucket error, cant fix')
#             return
#         self.P.E.write_error( 'Fixing Jump')
#         print('fixing jump')
#         M = PhaseMotor(self.P) #phase control motor
#         M.wait_for_stop()  # just ot be sure
#         old_pc = M.get_position()
#         new_pc = old_pc  - self.exact_error # new time for phase control
#         new_pc_fix = mod(new_pc, 1/self.laser_f)  # equal within one cycle. 
#         M.move(new_pc_fix) # moves phase motor to new position
#         #self.P.put('fix_bucket', 0)  # turn off bucket fix TESTING
#         M.wait_for_stop()
#         time.sleep(2)  # 
#         new_offset = self.d['offset'] - (new_pc_fix - old_pc)
#         self.d['offset'] = new_offset
#         self.P.put('offset', new_offset)
#         self.P.E.write_error( 'Done Fixing Jump')
#         bc = self.P.get('bucket_counter') # previous number of jumps
#         self.P.put('bucket_counter', bc + 1)  # write incremented number
#         print('jump fix done')

      
# class time_interval_counter():  # reads interval counter data, gets raw or average as needed
#     def __init__(self, P):
#         self.scale = 1e9 # scale relative to nanoseconds
#         self.P = P
#         self.good = 1 
#         self.rt = ring() # create a ring buffer to hold data
#         self.rt.add_element(self.P.get('counter')) # read first counter value to initialize array
#         self.rj = ring() # ring to hold jitter data
#         self.rj.add_element(self.P.get('counter_jitter'))
#         self.range = 0 # range of data
#     def get_time(self):
#         self.good = 0  # assume bad unless we fall through all the traps
#         self.range = 0; # until we overwrite
#         tol = self.P.get('counter_jitter_high')
#         tmin = self.P.get('counter_low')
#         tmax = self.P.get('counter_high')
#         time = self.P.get('counter')  # read counter time
#         if time == self.rt.get_last_element: # no new data
#             return 0 # no new data
#         if (time > tmax) or (time < tmin):
#             return 0 # data out of range
#         jit = self.P.get('counter_jitter')
#         if jit > tol:
#             return 0  # jitter too high
#         # if we got here, we have a good reading
#         self.rt.add_element(time) # add time to ring
#         self.rj.add_element(jit)  # add jitter to ring
#         self.good = 1
#         if self.rt.full:
#             self.range = self.scale * (max(self.rt.get_array()) - min(self.rt.get_array()))  # range of measurements
#         else:
#             self.range = 0  # don't have a full buffer yet
#         return time * self.scale

   

# class phase_motor():
#     def __init__(self, P): # P holds motor PVs (already open)
#         self.scale = .001 # motor is in ps, everthing else in ns
#         self.P = P
#         self.max_tries = 100
#         self.loop_delay = 0.1
#         self.tolerance = 2e-5  #was 5e-6
#         self.position = self.P.get('phase_motor') * self.scale  # get the current position  WARNING logic race potential
#         self.wait_for_stop()  # wait until it stops moving

#     def wait_for_stop(self):
#         #print('wait for stop')
#         if self.P.is_atca: # ATCA shifts are instantaneous (~2 seconds maximum)
#             #print('but i is atca')
#             pause(0.1) # fixed delay for ATCA time shifts
#             return
#         for n in range (0, self.max_tries):
#             try:
#                 stopped = self.P.get('phase_motor_dmov') # 1 if stopped, if throws error, is still moving
#             except:
#                 print('could not get dmov')

#                 stopped = 0  # threw error, assume not stopped (should clean up to look for epics error)
#             if stopped:
#                 posrb = self.P.get('phase_motor_rb') * self.scale  # position in nanoseconds
#                 if abs(posrb - self.position) < self.tolerance:  # are we within range
#                    break
#             time.sleep(self.loop_delay)        

#     def move(self, pos): # move motor to new position (no wait).
#         #self.P.pvlist['phase_motor'].put(value=pos / self.scale, timeout = 10.0)  # allow long timeout for motor move
#         self.P.put('phase_motor', pos/self.scale) # motor move if needed   
#         self.position = pos  # requested position in ns
#         self.wait_for_stop() # check
         

#     def get_position(self):
#         self.wait_for_stop() # wait until it stops moving
#         self.position = self.scale * self.P.get('phase_motor')  # get position data
#         return self.position           
   
# class trigger():  # deals with annoying problmes of triggers in ns or ticks
#     def __init__ (self, P):  # P is a pv list that includes trigger scaling information
#         self.P = P
#         if self.P.trig_in_ticks:
#             self.scale =1000.0/119.0  # 119MHz, 8 ns ticks 
#         else:
#             self.scale = 1 # trigger is in ns units
#         self.time = self.scale * self.P.get('laser_trigger')    
   
#     def get_ns(self):
#         tmp = self.P.get('laser_trigger')
#         self.time = self.scale * tmp
#         return self.time
        
#     def set_ns(self,t):
#         self.time = t/self.scale
#         #self.P.pvlist['laser_trigger'].put(self.time)
#         self.P.put('laser_trigger', self.time)
   
  
# class error_output():
#     def __init__(self, pv): # writes to this string pv (already connected)
#         self.pv = pv  # just to keep it here
#         self.pv.put(value= 'OK', timeout=1.0)
#         self.maxlen = 25 # maxumum error string length
  
#     def write_error(self, txt):
#         n = len(txt)
#         if n > self.maxlen:
#             txt = txt[0:self.maxlen]
#         self.pv.put(value = txt, timeout = 1.0)

# class degrees_s(): # manages time control in degrees S-band
#     def __init__(self, P):  #P has the list of PVs
#         self.P = P
#         self.freq = 2.856  # in GHz
#         self.last_time = self.P.get('time') # last time entered in contol
#         self.last_deg = self.P.get('deg_Sband') # last degrees sband
#         self.last_ns_offset = self.P.get('ns_offset')
#         self.last_deg_offset = self.P.get('deg_offset')
        
#     def run(self): # checks which changed last. NS given priority
#         ns = self.P.get('time')
#         deg = self.P.get('deg_Sband')
#         ns_offset = self.P.get('ns_offset')
#         deg_offset = self.P.get('deg_offset')
#         if ns != self.last_time or ns_offset != self.last_ns_offset: # nanoseconds have changed
#             deg_new = -1.0*(ns - ns_offset) * self.freq * 360 - deg_offset
#             self.last_time = ns
#             self.last_ns_offset = ns_offset
#             self.last_deg = deg_new
#             self.P.put('deg_Sband', deg_new) #write the degrees back
           
#         elif deg != self.last_deg or deg_offset != self.last_deg_offset:  #changed degrees
#             ns_new = -1.0*(deg + deg_offset)/(self.freq * 360) + ns_offset
#             self.last_time = ns_new
#             self.last_deg = deg
#             self.last_deg_offset = deg_offset
#             self.P.put('time', ns_new) 

#         else:
#             pass