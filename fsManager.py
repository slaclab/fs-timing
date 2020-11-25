#fs_Manager.py
""" Manager for to tie pcav measurements to cable stabilizer and fiber oven.  

This script, and class, implement a simplified version of the control process
that takes the pcav measurements, averages them, and sends drift corrections to
the cable stabilizer system. The fiber oven then corrects for the change in the
cable stabilizer phase.
"""

import time
from pylab import *
import watchdog
from psp.Pv import Pv
import sys
import random  # random number generator for secondary calibration

class fs_manager():
    """Manages pcav feedback to cable stabilizer, monitors fiber oven."""
    def __init__(self):
        pass

def run():
    pass

if __name__ == "__main__":
    run()