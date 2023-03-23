""" The phasemotor class implements some middle layer logic for requesting phase shifts.

Justin May
"""

import time
import pdb

class PhaseMotor(object):
    """ Object to communicate with phase motors.
    
    The PhaseMotor class encapsulates the functionality of the phase control
    for a laser.
    """
    
    def __init__(self, P): 
        """ Initialize the object based on existing configuration.
        
        This uses a PV set passed to the class that has already been created.

        Arguments:
        P -- holds motor PVs (already open)
        """
        
        self.scale = .001 # motor is in ps, everthing else in ns
        self.P = P
        self.max_tries = 100
        self.loop_delay = 0.1
        self.tolerance = 2e-5  #was 5e-6
        self.position = self.P.get('phase_motor') * self.scale  # get the current position  WARNING logic race potential
        self.prev_pos = self.position
        self.wait_for_stop()  # wait until it stops moving

    def wait_for_stop(self):
        """ Hold execution until a move is not underway.
        
        The logical implication of this function is different depending on
        whether it is talking to a SIM or ATCA system, but the end result is
        largely the same, in part because the design of the MForce and SmarAct
        connections has been designed to look similar.
        
        """
        #print('wait for stop')
        # J.May (4/7/22): This isn't quite true, but we also don't get a phase readback, so I'm leaving this for now, even though one still needs a check against actual movement
        if self.P.config.is_atca: # ATCA shifts are instantaneous (~2 seconds maximum)
            #print('but i is atca')
            # DUh! THis is not a readback, this won't do a thing.
            while self.position != self.prev_pos:
                time.sleep(1.0) # fixed delay for ATCA time shifts
                self.prev_pos = self.position
                self.position = self.P.get('phase_motor') * self.scale
            time.sleep(0.2) # fixed delay for ATCA time shifts
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

    def move(self, pos):
        """ move motor to new position (no wait)."""

        #self.P.pvlist['phase_motor'].put(value=pos / self.scale, timeout = 10.0)  # allow long timeout for motor move
        # pdb.set_trace()
        self.P.put('phase_motor', pos/self.scale) # motor move if needed
        print("M: %f"%(pos/self.scale))
        self.position = pos  # requested position in ns
        self.wait_for_stop() # check
         
    def get_position(self):
        """ Return position for phase motor including wait_for_stop."""
        
        self.wait_for_stop() # wait until it stops moving
        self.position = self.scale * self.P.get('phase_motor')  # get position data
        return self.position     
