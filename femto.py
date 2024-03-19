"""femto.py  program to control laser femtosecond timing

# major version rework through 2021-07-21 - JM 
# -- see version control history and Readme for major changes
# This library has been python3'd
"""

import time
import math
import sys
import random  # random number generator for secondary calibration
import pdb

# imports for memory leak investigation
import threading
from pathlib import Path
import datetime
import tracemalloc
tracemalloc.start()
tracerun = True

import numpy
from scipy.optimize import leastsq # for secondary calibration
# from pylab import *
# try:
#     from psp.Pv import Pv 
#     print('using psp.Pv')
# except ModuleNotFoundError:
try:
    from epics.pv import PV as Pv
    # print('using epics.pv')
except ModuleNotFoundError:
    print('no epics pv support located within environment')

from support import watchdog3 as watchdog
from support.femtoconfig import Config
# import support.tic.TimeIntervalCounter
# import support.tic.Keysight as TimeIntervalCounter
import support.PhaseMotor
from support.PVS import PVS
from support.ErrorOutput import error_output
from support.Degrees import degrees_s
from support.ErrorOutput import error_output
from support.laserlockerversions.Gen1LaserLocker import LaserLocker as Gen1LaserLocker
from support.laserlockerversions.Gen2LaserLocker import LaserLocker as Gen2LaserLocker
from support.Trigger import Trigger

def fitres(param, tin, tout):
    """ Compute error in calibration fit.

    Arguments: 
    tin -- is input time
    tout -- measured
    param -- parameters for fit
    """
    sa,ca = param  # sine and cosine amplitudes
    err= tout - ffun(tin, sa, ca)
    return err
        
def ffun( x, a, b):
    """ Support function for fitres.
    
    Arguments:
    x -- 
    a --
    b --
    """
    w0 = 2.600*2*numpy.pi
    out = a*numpy.sin(x * w0) + b * numpy.cos(x*w0)
    return out

def dump_tracemalloc():
    while tracerun:
        time.sleep(30.0)
        # tracemalloc.dump(Path("/home/fphysics/jemay/data/malloc/",f'dump_%s'%(datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S_%f"))))
        tracemalloc.take_snapshot().dump(str(Path(r"C:\Users\jemay\Documents\_Core\_Work_Local\_Data_Local\malloc_test",'dump_%s'%(datetime.datetime.now().strftime("%Y%m%d_%H_%M_%S_%f")))))

def femto(config_fpath='NULL'):
    """ Script-like main function for an instance of the laser locker HLA.
    
    The parent logical object for an instance of femto.py; initializes
    objects and manages the run loop. Intended to be launched from commandline via control system processes and manual control.
    
    Arguments:
    config_fpath -- path to a configuration file to load that describes the PV structure an installation
    """
    tracemallocthread = threading.Thread(None,target=dump_tracemalloc)
    tracemallocthread.start()
    config = Config()
    P = PVS(config_fpath,epicsdebug=False,localdebug=True)
    if P.OK == 0:
        return
    W = watchdog.watchdog(P.config.pvlist['watchdog'])
    if W.error:
        return
    if P.config.is_atca:
        L = Gen2LaserLocker(P.E,P,W)
    else:
        L = Gen1LaserLocker(P.E,P,W)
    if "find_beam_ctl" in P.config.config["add_config"]:
        beamFind_enabled = True
    else:
        beamFind_enabled = False
    L.locker_status()  # check locking sysetm / laser status
    P.E.write_error( {"value":L.message,"lvl":2})
    T = Trigger(P)
    T.get_ns()
    if "deg_conversion_freq" in P.config.config["add_config"]:
        D = degrees_s(P,P.config.config["add_config"]["deg_conversion_freq"]) # manages conversion of degrees to ns and back
    else:
        D = degrees_s(P,2.856)
    while W.error ==0:   # MAIN PROGRAM LOOP
        time.sleep(0.2)
        try:   # the never give up, never surrunder loop. 
            P.E.write_error({'value':'main loop start',"lvl":2})
            W.check()
            P.put('busy', 0)
            L.locker_status()  # check if the locking sysetm is OK
            if not L.laser_ok:  # if the laser isn't working, for now just do nothign, eventually suggest fixes
                P.E.write_error({'value':L.message,"lvl":2})
                P.put('ok', 0)
                P.E.write_error({'value':'laser not ok, looping',"lvl":2})
                time.sleep(0.5)  # to keep the loop from spinning too fast
                continue            #just try again if the laser isn't ready
            #if beamFind_enabled:
            # This functionality is currently disabled pending more testing for LCLS-II high rate operation
            #    L.findBeam()
            if P.get('calibrate'):
                P.E.write_error({'value':'calib requested',"lvl":2})
                P.put('ok', 0)
                P.put('busy', 1) # sysetm busy calibrating
                P.E.write_error({'value':'calibration requested - starting',"lvl":2})
                L.calibrate()
                P.put('calibrate', 0)
                P.E.write_error({'value':' calibration done',"lvl":2})
                continue
            if  P.config.use_secondary_calibration:  # run calibration against scope
                if P.get('secondary_calibration_enable'): # not requested  
                    P.put('ok', 0)
                    P.put('busy', 1) # sysetm busy calibrating
                    P.E.write_error({'value':'secondary calibration',"lvl":2})
                    L.second_calibrate()
                    P.put('secondary_calibration_enable', 0)
                    P.E.write_error({'value':' secondary calibration done',"lvl":2})
                    continue
                pass
            P.E.write_error({'value':'check for jumps',"lvl":2})
            L.check_jump()   # looks for phase jumps relative to phase control / trigger
            if P.get('fix_bucket') and L.buckets != 0 and P.get('enable'):
                P.E.write_error({'value':'fix buckets',"lvl":2})
                P.put('ok', 0)
                P.put('busy', 1)
                L.fix_jump()  # fixes bucket jumps - careful
            P.put('bucket_error',  L.buckets)
            P.put('unfixed_error', L.bucket_error)
            P.put('ok', 1)
            if P.get('enable'): # is enable time control active?
                P.E.write_error({'value':'time ctrl enabled, set time',"lvl":2})
                L.set_time() # set time read earlier    
            D.run()  # deals with degreees S band conversion    
        except:   # catch any otherwise uncaught error.
            P.E.write_error({'value':str(sys.exc_info()[0]),"lvl":2})
            P.E.write_error({'value':'UNKNOWN ERROR, trying again',"lvl":2})
            P = PVS(config_fpath,epicsdebug=False,localdebug=False)
            if P.OK == 0:
                return
            W = watchdog.watchdog(P.config.pvlist['watchdog'])
            if W.error:
                return
            if P.config.is_atca:
                L = Gen2LaserLocker(P.E,P,W)
            else:
                L = Gen1LaserLocker(P.E,P,W)
            L.locker_status()  # check locking sysetm / laser status
            P.E.write_error({'value':L.message,"lvl":2})
            T = Trigger(P)
            T.get_ns()
    P.E.write_error({'value':'done, exiting',"lvl":2})
    tracerun = False        


if __name__ == "__main__":
    """ Run femto.py via commandline.
    
    The HLA is designed to be launched via mechanisms deployed on the various
    control systems for issuing scripts (like the AD "watchers"). As such, the
    command line values are limited, and only limited error handling is provided
    here. While there are more robust commandline argument handlers, for
    backwards compatibility, this design is limited.

    Arguments: sys.argv[1] -- config file path relative to femto.py directory
    """
    if len(sys.argv) < 2:
        femto()  # null input will prompt
    else:
        femto(sys.argv[1]) # major change to provide config file as command line input
    

