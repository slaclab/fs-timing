#femto.py  program to control laser femtosecond timing

# major version rework through 2021-07-21 - JM 
# -- see version control history and Readme for major changes
# This library has been python3'd


import time
import math
import numpy
# from pylab import *
try:
    from psp.Pv import Pv 
    print('using psp.Pv')
except ModuleNotFoundError:
    try:
        from epics.pv import PV as Pv
        print('using epics.pv')
    except ModuleNotFoundError:
        print('no epics pv support located within environment')
import sys
import random  # random number generator for secondary calibration
from scipy.optimize import leastsq # for secondary calibration
from support import watchdog3 as watchdog
from support.femtoconfig import Config
import support.TimeIntervalCounter
import support.PhaseMotor
from support.PVS import PVS
from support.ErrorOutput import error_output
from support.Degrees import degrees_s
from support.ErrorOutput import error_output
from support.laserlockerversions.Gen1LaserLocker import locker as Gen1LaserLocker
from support.laserlockerversions.Gen2LaserLocker import LaserLocker as Gen2LaserLocker
from support.Trigger import Trigger

def fitres(param, tin, tout):  # tin isinput time, tout is measured, param is parameters    
    sa,ca = param  # sine and cosine amplitudes
    err= tout - ffun(tin, sa, ca)
    return err
        
def ffun( x, a, b):
    w0 = 3.808*2*pi
    out = a*sin(x * w0) + b * cos(x*w0)
    return out        


def femto(config_fpath='NULL'):
    """ The parent logical object for an instance of femto.py; initializes
    objects and manages the run loop."""
    config = Config()
    P = PVS(config_fpath)
    if P.OK == 0:
        return
    W = watchdog.watchdog(P.config.pvlist['watchdog'])
    if W.error:
        return
    if P.config.is_atca:
        L = Gen2LaserLocker(P,W)
    else:
        L = Gen1LaserLocker(P,W)
    # L = locker(P,W) #set up locking system parameters
    L.locker_status()  # check locking sysetm / laser status
    P.E.write_error( L.message)
    T = Trigger(P)
    T.get_ns()
#   C = time_interval_counter(P)  # time interval counter device
    D = degrees_s(P) # manages conversion of degrees to ns and back
#    C.get_time()
    while W.error ==0:   # MAIN PROGRAM LOOP
        time.sleep(0.1)
        try:   # the never give up, never surrunder loop. 
            print('main loop start')
            W.check()
            P.put('busy', 0)
            L.locker_status()  # check if the locking sysetm is OK
            if not L.laser_ok:  # if the laser isn't working, for now just do nothign, eventually suggest fixes
                P.E.write_error( L.message)
                P.put('ok', 0)
                print('laser not ok, looping')
                time.sleep(0.5)  # to keep the loop from spinning too fast
                continue            #just try again if the laser isn't ready  
            if P.get('calibrate'):
                print('calib requested')
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
            print('check for jumps')
            L.check_jump()   # looks for phase jumps relative to phase control / trigger
            if P.get('fix_bucket') and L.buckets != 0 and P.get('enable'):
                print('fix buckets')
                P.put('ok', 0)
                P.put('busy', 1)
                L.fix_jump()  # fixes bucket jumps - careful
            P.put('bucket_error',  L.buckets)
            P.put('unfixed_error', L.bucket_error)
            P.put('ok', 1)
            if P.get('enable'): # is enable time control active?
                print('time ctrl enabled, set time')
                L.set_time() # set time read earlier    
            D.run()  # deals with degreees S band conversion    
            #P.E.write_error('Laser OK')
        except:   # catch any otherwise uncaught error.
            print(sys.exc_info()[0]) # print error I hope)
            del P  #does this work?
            print('UNKNOWN ERROR, trying again')
   
            P = PVS(name)
            W = watchdog.watchdog(P.pvlist['watchdog'])
            L = locker(P, W) #set up locking system parameters
            L.locker_status()  # check locking sysetm / laser status
            P.E.write_error( L.message)
            T = Trigger(P)
            T.get_ns()
    P.E.write_error( 'done, exiting')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        femto()  # null input will prompt
    else:
        femto(sys.argv[1]) # major change to provide config file as command line input
    

