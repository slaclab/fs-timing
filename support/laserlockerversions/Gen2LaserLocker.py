from support.laserlockerversions.LaserLocker import LaserLocker

class LaserLocker(LaserLocker):
    """Gen 2 Laser locker object, inheriting from generalized LaserLocker object."""
    def __init__(self,errorLog,pvs,watchdog):
        super().__init__(errorLog,pvs,watchdog)
        self.f0 = 1.3  # Reference frequency in GHz
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
        self.C = TimeIntervalCounter(self.P) # creates a time interval c

    def isLaserOk(self):
        status = super().isLaserOk()
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