class PhaseMotor(object):
    """The PhaseMotor class encapsulates the functionality of the phase control
    for a laser."""
    
    def __init__(self, P): # P holds motor PVs (already open)
        self.scale = .001 # motor is in ps, everthing else in ns
        self.P = P
        self.max_tries = 100
        self.loop_delay = 0.1
        self.tolerance = 2e-5  #was 5e-6
        self.position = self.P.get('phase_motor') * self.scale  # get the current position  WARNING logic race potential
        self.wait_for_stop()  # wait until it stops moving

    def wait_for_stop(self):
        #print('wait for stop')
        if self.P.is_atca: # ATCA shifts are instantaneous (~2 seconds maximum)
            #print('but i is atca')
            pause(0.1) # fixed delay for ATCA time shifts
            return
        for n in range (0, self.max_tries):
            try:
                stopped = self.P.get('phase_motor_dmov') # 1 if stopped, if throws error, is still moving
            except:
                print('could not get dmov')

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